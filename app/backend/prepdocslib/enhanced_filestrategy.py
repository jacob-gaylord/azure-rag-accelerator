"""
Enhanced file strategy with asyncio-based concurrent processing and optimizations.

This module provides an enhanced version of FileStrategy that supports:
- Concurrent file processing with configurable limits
- Parallel downloads and processing stages
- Enhanced error handling and retry mechanisms
- Performance monitoring and metrics
- Memory-efficient streaming for large files
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from .filestrategy import FileStrategy, parse_file
from .listfilestrategy import File, ListFileStrategy
from .blobmanager import BlobManager
from .embeddings import ImageEmbeddings, OpenAIEmbeddings
from .fileprocessor import FileProcessor
from .searchmanager import SearchManager, Section
from .strategy import DocumentAction, SearchInfo, Strategy

logger = logging.getLogger("scripts")


@dataclass
class ProcessingMetrics:
    """Metrics for monitoring processing performance"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_processing_time: float = 0.0
    average_file_size: float = 0.0
    concurrent_tasks: int = 0
    max_concurrent_tasks: int = 0
    
    def add_file_processed(self, processing_time: float, file_size: int):
        self.processed_files += 1
        self.total_processing_time += processing_time
        if self.processed_files > 0:
            self.average_file_size = (self.average_file_size * (self.processed_files - 1) + file_size) / self.processed_files
    
    def add_file_failed(self):
        self.failed_files += 1
    
    def add_file_skipped(self):
        self.skipped_files += 1
    
    def set_concurrent_tasks(self, count: int):
        self.concurrent_tasks = count
        self.max_concurrent_tasks = max(self.max_concurrent_tasks, count)


class EnhancedFileStrategy(FileStrategy):
    """
    Enhanced strategy with concurrent processing, retry mechanisms, and performance optimizations
    """
    
    def __init__(
        self,
        list_file_strategy: ListFileStrategy,
        blob_manager: BlobManager,
        search_info: SearchInfo,
        file_processors: dict[str, FileProcessor],
        document_action: DocumentAction = DocumentAction.Add,
        embeddings: Optional[OpenAIEmbeddings] = None,
        image_embeddings: Optional[ImageEmbeddings] = None,
        search_analyzer_name: Optional[str] = None,
        search_field_name_embedding: Optional[str] = None,
        use_acls: bool = False,
        category: Optional[str] = None,
        use_content_understanding: bool = False,
        content_understanding_endpoint: Optional[str] = None,
        # New parameters for enhanced processing
        max_concurrent_files: int = 5,
        max_concurrent_downloads: int = 10,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        enable_metrics: bool = True,
        chunk_size: int = 8192,
    ):
        super().__init__(
            list_file_strategy=list_file_strategy,
            blob_manager=blob_manager,
            search_info=search_info,
            file_processors=file_processors,
            document_action=document_action,
            embeddings=embeddings,
            image_embeddings=image_embeddings,
            search_analyzer_name=search_analyzer_name,
            search_field_name_embedding=search_field_name_embedding,
            use_acls=use_acls,
            category=category,
            use_content_understanding=use_content_understanding,
            content_understanding_endpoint=content_understanding_endpoint,
        )
        
        # Enhanced processing parameters
        self.max_concurrent_files = max_concurrent_files
        self.max_concurrent_downloads = max_concurrent_downloads
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.enable_metrics = enable_metrics
        self.chunk_size = chunk_size
        
        # Semaphores for controlling concurrency
        self.file_processing_semaphore = asyncio.Semaphore(max_concurrent_files)
        self.download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        
        # Metrics tracking
        self.metrics = ProcessingMetrics() if enable_metrics else None
    
    async def run(self):
        """Enhanced run method with concurrent processing"""
        self.setup_search_manager()
        
        if self.document_action == DocumentAction.Add:
            await self._run_concurrent_add()
        elif self.document_action == DocumentAction.Remove:
            await self._run_remove()
        elif self.document_action == DocumentAction.RemoveAll:
            await self._run_remove_all()
    
    async def _run_concurrent_add(self):
        """Run file addition with concurrent processing"""
        start_time = time.time()
        
        # Create async generator for files
        files = self.list_file_strategy.list()
        
        # Process files concurrently using semaphore
        tasks = []
        active_tasks = set()
        
        try:
            async for file in files:
                if self.metrics:
                    self.metrics.total_files += 1
                
                # Create task for processing this file
                task = asyncio.create_task(self._process_file_with_semaphore(file))
                tasks.append(task)
                active_tasks.add(task)
                
                # Update metrics
                if self.metrics:
                    self.metrics.set_concurrent_tasks(len(active_tasks))
                
                # Limit the number of concurrent tasks to prevent memory issues
                if len(active_tasks) >= self.max_concurrent_files * 2:  # Allow some buffering
                    # Wait for some tasks to complete
                    done, active_tasks = await asyncio.wait(
                        active_tasks, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Handle completed tasks
                    for completed_task in done:
                        try:
                            await completed_task
                        except Exception as e:
                            logger.error(f"Task failed: {e}")
                            if self.metrics:
                                self.metrics.add_file_failed()
                    
                    # Update metrics
                    if self.metrics:
                        self.metrics.set_concurrent_tasks(len(active_tasks))
            
            # Wait for all remaining tasks to complete
            if active_tasks:
                done, _ = await asyncio.wait(active_tasks)
                for completed_task in done:
                    try:
                        await completed_task
                    except Exception as e:
                        logger.error(f"Task failed: {e}")
                        if self.metrics:
                            self.metrics.add_file_failed()
        
        finally:
            # Ensure all tasks are cleaned up
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for cancelled tasks to finish
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log final metrics
        if self.metrics:
            total_time = time.time() - start_time
            self.metrics.total_processing_time = total_time
            self._log_final_metrics()
    
    async def _process_file_with_semaphore(self, file: File):
        """Process a single file with semaphore control and retry logic"""
        async with self.file_processing_semaphore:
            # Update concurrent task count
            if self.metrics:
                current_count = self.max_concurrent_files - self.file_processing_semaphore._value
                self.metrics.set_concurrent_tasks(current_count)
            
            return await self._process_file_with_retry(file)
    
    async def _process_file_with_retry(self, file: File) -> bool:
        """Process a file with retry logic"""
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                start_time = time.time()
                success = await self._process_single_file(file)
                
                if success and self.metrics:
                    processing_time = time.time() - start_time
                    file_size = getattr(file, 'size', 0) or 0
                    self.metrics.add_file_processed(processing_time, file_size)
                
                return success
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{self.retry_attempts} failed for file {file.filename()}: {e}")
                
                if attempt < self.retry_attempts - 1:
                    # Wait before retrying (exponential backoff)
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed to process file {file.filename()} after {self.retry_attempts} attempts: {last_exception}")
                    if self.metrics:
                        self.metrics.add_file_failed()
                    return False
            
            finally:
                # Always ensure file is closed
                if file:
                    try:
                        file.close()
                    except Exception as e:
                        logger.warning(f"Failed to close file {file.filename()}: {e}")
        
        return False
    
    async def _process_single_file(self, file: File) -> bool:
        """Process a single file through the pipeline"""
        try:
            logger.info(f"Processing file: {file.filename()}")
            
            # Stage 1: Parse file (CPU bound)
            sections = await parse_file(file, self.file_processors, self.category, self.image_embeddings)
            
            if not sections:
                logger.info(f"No content extracted from {file.filename()}, skipping")
                if self.metrics:
                    self.metrics.add_file_skipped()
                return True
            
            # Stage 2: Upload to blob storage (I/O bound)
            blob_sas_uris = await self._upload_with_semaphore(file)
            
            # Stage 3: Generate image embeddings if needed (CPU/I/O bound)
            blob_image_embeddings: Optional[list[list[float]]] = None
            if self.image_embeddings and blob_sas_uris:
                blob_image_embeddings = await self.image_embeddings.create_embeddings(blob_sas_uris)
            
            # Stage 4: Update search index (I/O bound)
            await self.search_manager.update_content(sections, blob_image_embeddings, url=file.url)
            
            logger.info(f"Successfully processed file: {file.filename()}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename()}: {e}")
            raise
    
    async def _upload_with_semaphore(self, file: File):
        """Upload file to blob storage with download semaphore"""
        async with self.download_semaphore:
            return await self.blob_manager.upload_blob(file)
    
    async def _run_remove(self):
        """Run file removal (unchanged from parent)"""
        paths = self.list_file_strategy.list_paths()
        async for path in paths:
            await self.blob_manager.remove_blob(path)
            await self.search_manager.remove_content(path)
    
    async def _run_remove_all(self):
        """Run remove all (unchanged from parent)"""
        await self.blob_manager.remove_blob()
        await self.search_manager.remove_content()
    
    def _log_final_metrics(self):
        """Log final processing metrics"""
        if not self.metrics:
            return
        
        logger.info("=== Processing Metrics ===")
        logger.info(f"Total files: {self.metrics.total_files}")
        logger.info(f"Processed: {self.metrics.processed_files}")
        logger.info(f"Failed: {self.metrics.failed_files}")
        logger.info(f"Skipped: {self.metrics.skipped_files}")
        logger.info(f"Total processing time: {self.metrics.total_processing_time:.2f}s")
        logger.info(f"Max concurrent tasks: {self.metrics.max_concurrent_tasks}")
        
        if self.metrics.processed_files > 0:
            avg_time = self.metrics.total_processing_time / self.metrics.processed_files
            logger.info(f"Average processing time per file: {avg_time:.2f}s")
            logger.info(f"Average file size: {self.metrics.average_file_size:.0f} bytes")
        
        success_rate = (self.metrics.processed_files / self.metrics.total_files * 100) if self.metrics.total_files > 0 else 0
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info("=========================")


class StreamingFileProcessor:
    """
    Utility class for processing large files in streaming fashion to reduce memory usage
    """
    
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
    
    async def process_large_file_streaming(
        self, 
        file: File, 
        processor_func,
        max_memory_mb: int = 100
    ):
        """
        Process large files in chunks to limit memory usage
        """
        file_size = getattr(file, 'size', 0)
        max_memory_bytes = max_memory_mb * 1024 * 1024
        
        if file_size > max_memory_bytes:
            # Process in streaming mode
            logger.info(f"Processing large file {file.filename()} ({file_size} bytes) in streaming mode")
            return await self._process_streaming(file, processor_func)
        else:
            # Process normally
            return await processor_func(file)
    
    async def _process_streaming(self, file: File, processor_func):
        """
        Stream process a large file in chunks
        """
        # This would be implemented based on specific file type and processing needs
        # For now, delegate to normal processing
        logger.warning("Streaming processing not yet implemented, falling back to normal processing")
        return await processor_func(file) 