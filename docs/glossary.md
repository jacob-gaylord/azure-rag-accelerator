# Glossary

This glossary defines key terms and concepts used in the Azure RAG Accelerator and Retrieval-Augmented Generation systems.

## A

**Azure AI Search** (formerly Azure Cognitive Search)
: A cloud search service that provides secure information retrieval over private content in traditional and generative AI search applications. Used for indexing and searching documents in the RAG accelerator.

**Azure Developer CLI (azd)**
: A command-line tool that accelerates the time it takes to get applications running in Azure. Used for deploying and managing the RAG accelerator infrastructure.

**Azure OpenAI Service**
: Microsoft's managed service providing access to OpenAI's powerful language models, including GPT-4 and GPT-3.5-turbo, through REST APIs with enterprise-grade security and compliance.

**Application Insights**
: Azure's application performance management service that provides monitoring, alerting, and diagnostics for web applications, including the RAG accelerator.

## B

**Bicep**
: A domain-specific language (DSL) for deploying Azure resources. The RAG accelerator uses Bicep templates for infrastructure as code deployment.

**Blob Storage**
: Azure's object storage service for storing massive amounts of unstructured data. Used by the RAG accelerator to store uploaded documents and processed content.

**BM25**
: A ranking function used in traditional text search to estimate the relevance of documents to a given search query. Part of the hybrid search approach in Azure AI Search.

## C

**Chunking**
: The process of breaking down large documents into smaller, manageable pieces (chunks) that can be efficiently processed and indexed for search and retrieval.

**Citation**
: A reference to the original source document from which information was retrieved to answer a user's question. The RAG accelerator provides configurable citation strategies.

**Container Apps**
: Azure's fully managed serverless container platform for running microservices and containerized applications. The RAG accelerator runs on Container Apps for scalability and cost optimization.

**Cosmos DB**
: Azure's globally distributed, multi-model database service. Used by the RAG accelerator to store user feedback, chat history, and session data.

**Content Filtering**
: Azure OpenAI's built-in safety system that screens prompts and responses for potentially harmful content including hate speech, sexual content, violence, and self-harm.

## D

**Document Intelligence**
: Azure's AI service for extracting text, tables, structure, and other data from documents. Used in the RAG accelerator for processing uploaded files.

**Dense Retrieval**
: A search method that uses vector embeddings to find semantically similar content, even when exact keywords don't match. Also known as vector search or semantic search.

## E

**Embedding**
: A numerical representation (vector) of text that captures semantic meaning. Used in the RAG accelerator for vector search capabilities.

**Embedding Model**
: An AI model that converts text into vector embeddings. The RAG accelerator uses Azure OpenAI's text-embedding-ada-002 model by default.

## F

**Feedback System**
: A mechanism for collecting user ratings and comments on AI-generated responses, helping improve the system over time. Built into the RAG accelerator's admin dashboard.

**Fine-tuning**
: The process of training a pre-trained model on specific data to improve performance for particular tasks. Not directly used in the RAG accelerator but can be applied to embedding models.

## G

**GPT (Generative Pre-trained Transformer)**
: A family of language models developed by OpenAI. The RAG accelerator uses GPT-3.5-turbo and GPT-4 models for generating responses.

**Grounding**
: The process of anchoring AI model responses to specific, retrieved documents to ensure accuracy and provide verifiable sources.

## H

**Hybrid Search**
: A search approach that combines traditional keyword-based search (BM25) with vector/semantic search for improved relevance and coverage.

**Hallucination**
: When an AI model generates information that appears plausible but is actually false or not supported by the provided context. RAG systems help reduce hallucinations by grounding responses in retrieved documents.

## I

**Index**
: A structured data store in Azure AI Search that contains searchable documents and their metadata. The RAG accelerator creates and maintains search indexes for efficient document retrieval.

**Ingestion**
: The process of collecting, processing, and indexing documents from various sources into the search system. The RAG accelerator supports multiple ingestion methods.

## K

**Knowledge Base**
: A collection of documents, data, and information that serves as the foundation for the RAG system's responses. In the RAG accelerator, this includes all indexed documents.

## L

**LLM (Large Language Model)**
: AI models with billions of parameters trained on vast amounts of text data. The RAG accelerator uses Azure OpenAI's LLMs for generating responses.

**Langchain**
: A framework for developing applications with language models. Used in the RAG accelerator for orchestrating retrieval and generation workflows.

## M

**Managed Identity**
: Azure's service for providing applications with an automatically managed identity in Azure AD for authentication to Azure services without storing credentials.

**Microsoft Graph**
: A unified API endpoint for accessing Microsoft 365 services, including SharePoint. Used by the RAG accelerator for SharePoint integration.

**Multi-modal**
: Refers to AI systems that can process and understand multiple types of data (text, images, audio). The RAG accelerator primarily focuses on text but can extract text from various document formats.

## N

**NDJSON (Newline Delimited JSON)**
: A data format where each line is a valid JSON object. Used by the RAG accelerator for exporting data and streaming responses.

## O

**Orchestration**
: The coordination and management of multiple AI services and processes to complete complex tasks. The RAG accelerator orchestrates retrieval and generation steps.

**Overrides**
: Configuration parameters that can be passed to customize the behavior of search and AI model operations in the RAG accelerator.

## P

**Prompt Engineering**
: The practice of designing and optimizing text prompts to get better results from language models. Built into the RAG accelerator's approach templates.

**Preprocessing**
: The steps taken to clean, format, and prepare documents before indexing, including text extraction, chunking, and metadata generation.

## Q

**Quart**
: An async Python web framework used as the backend framework for the RAG accelerator's API server.

**Query Expansion**
: A technique to improve search results by expanding or modifying the original query, often using synonyms or related terms.

## R

**RAG (Retrieval-Augmented Generation)**
: An AI architecture that enhances language model responses by first retrieving relevant information from a knowledge base, then using that information to generate informed answers.

**Retrieval**
: The process of finding and extracting relevant documents or passages from a knowledge base in response to a user query.

**Role Assignment**
: Azure's method for granting permissions to users, groups, or services to access specific Azure resources. Critical for the RAG accelerator's security model.

## S

**Semantic Search**
: A search method that understands the meaning and context of queries rather than just matching keywords. Implemented using vector embeddings in the RAG accelerator.

**SharePoint Online**
: Microsoft's cloud-based collaboration platform. The RAG accelerator can integrate with SharePoint as a document source.

**Sparse Retrieval**
: Traditional keyword-based search methods like BM25 that rely on exact term matches and frequency statistics.

**System Prompt**
: Instructions given to a language model that define its role, behavior, and response format. The RAG accelerator uses carefully crafted system prompts for different conversation approaches.

## T

**Token**
: The basic unit of text that language models process. Can be words, parts of words, or punctuation. Important for managing costs and context length limits.

**Top-K**
: A parameter that specifies how many of the best search results to retrieve before passing to the language model for response generation.

**TPM (Tokens Per Minute)**
: A rate limit metric for Azure OpenAI services that determines how many tokens can be processed per minute.

## U

**User Principal Name (UPN)**
: A unique identifier for users in Azure Active Directory, typically in email format. Used for authentication and authorization in the RAG accelerator.

## V

**Vector Database**
: A specialized database optimized for storing and searching high-dimensional vectors (embeddings). Azure AI Search serves this role in the RAG accelerator.

**Vector Search**
: A search method that uses mathematical similarity between vector embeddings to find semantically related content.

**Vectorization**
: The process of converting text into numerical vector representations (embeddings) that capture semantic meaning.

## W

**Web App**
: A cloud-based application accessible through web browsers. The RAG accelerator provides a web interface for users to interact with the system.

**Workload Identity**
: Azure's recommended authentication method for applications running in Kubernetes environments, providing secure access to Azure resources.

---

## Acronyms and Abbreviations

| Acronym | Full Form | Description |
|---------|-----------|-------------|
| AAD | Azure Active Directory | Microsoft's identity and access management service |
| ACA | Azure Container Apps | Serverless container platform |
| ACL | Access Control List | Security mechanism for controlling resource access |
| AI | Artificial Intelligence | Computer systems that can perform tasks typically requiring human intelligence |
| API | Application Programming Interface | Set of protocols for building software applications |
| ARM | Azure Resource Manager | Azure's deployment and management service |
| AZD | Azure Developer CLI | Command-line tool for Azure development |
| CORS | Cross-Origin Resource Sharing | Security feature for web applications |
| CPU | Central Processing Unit | Computer's main processor |
| CSV | Comma-Separated Values | File format for tabular data |
| DNS | Domain Name System | System for translating domain names to IP addresses |
| GPU | Graphics Processing Unit | Specialized processor for parallel computing |
| HTTP | Hypertext Transfer Protocol | Protocol for web communication |
| HTTPS | HTTP Secure | Encrypted version of HTTP |
| JSON | JavaScript Object Notation | Lightweight data-interchange format |
| JWT | JSON Web Token | Standard for secure token-based authentication |
| ML | Machine Learning | Subset of AI focused on learning from data |
| NLP | Natural Language Processing | AI field focused on human language understanding |
| OCR | Optical Character Recognition | Technology for extracting text from images |
| PDF | Portable Document Format | File format for documents |
| RAM | Random Access Memory | Computer's working memory |
| REST | Representational State Transfer | Architectural style for web services |
| SDK | Software Development Kit | Tools for developing applications |
| SLA | Service Level Agreement | Contract defining service performance standards |
| SQL | Structured Query Language | Language for managing databases |
| SSL | Secure Sockets Layer | Security protocol for encrypted communication |
| TLS | Transport Layer Security | Cryptographic protocol for secure communication |
| UI | User Interface | Visual elements users interact with |
| UX | User Experience | Overall experience of using a product |
| VM | Virtual Machine | Software emulation of a physical computer |

## Related Technologies

**Azure Services Used:**
- Azure OpenAI Service
- Azure AI Search (Cognitive Search)
- Azure Container Apps
- Azure Blob Storage
- Azure Cosmos DB
- Azure Application Insights
- Azure Key Vault
- Azure Active Directory
- Microsoft Graph API

**Development Technologies:**
- Python (Backend)
- TypeScript/React (Frontend)
- Quart (Web Framework)
- Docker (Containerization)
- Bicep (Infrastructure as Code)

**AI/ML Concepts:**
- Large Language Models (LLMs)
- Natural Language Processing (NLP)
- Vector Embeddings
- Semantic Search
- Transformer Architecture
- Attention Mechanisms

---

*This glossary is regularly updated as new features and technologies are added to the Azure RAG Accelerator. For the most current information, refer to the official Azure documentation and OpenAI documentation.* 