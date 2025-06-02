# Changelog

All notable changes to the Azure RAG Accelerator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation suite including API reference, deployment guides, and troubleshooting
- Real-world scenario-based deployment guides
- Admin dashboard for analytics and feedback management
- Enhanced feedback system with rating capabilities
- Observability improvements with Application Insights integration
- Performance monitoring and health check endpoints

### Changed
- Improved search relevance with hybrid retrieval modes
- Enhanced citation system with configurable strategies
- Optimized document processing pipeline
- Better error handling and user feedback

### Fixed
- SharePoint connector authentication issues
- Memory optimization for large document processing
- Citation URL generation for various document sources

### Security
- Enhanced authentication and authorization controls
- Improved data privacy and compliance features

## [1.2.0] - 2024-01-10

### Added
- SharePoint Online integration support
- Multi-source data ingestion capabilities
- Enhanced admin dashboard with export functionality
- Real-time feedback collection and analysis
- Performance optimization tools
- Comprehensive API documentation

### Changed
- Improved container app deployment architecture
- Enhanced search index configuration
- Better error handling for AI service failures
- Optimized memory usage for document processing

### Fixed
- Authentication redirect issues in certain environments
- Large file upload handling
- Search result ranking improvements
- Citation link generation bugs

## [1.1.0] - 2023-12-15

### Added
- Azure Container Apps deployment support
- Enhanced observability with Application Insights
- Feedback system for user interactions
- Admin dashboard for monitoring and analytics
- Support for multiple document formats
- Configurable AI model selection

### Changed
- Migrated from App Service to Container Apps
- Improved deployment automation with Azure Developer CLI
- Enhanced security with managed identity integration
- Better scalability with auto-scaling configuration

### Fixed
- Memory leaks in document processing
- Authentication token refresh issues
- Search service connection reliability
- Error handling for malformed documents

### Security
- Implemented Azure Active Directory integration
- Added role-based access control
- Enhanced data encryption at rest and in transit

## [1.0.0] - 2023-11-01

### Added
- Initial release of Azure RAG Accelerator
- Basic chat interface with Azure OpenAI integration
- Document upload and processing capabilities
- Azure Cognitive Search integration
- Vector and hybrid search support
- Basic citation system
- Azure deployment automation

### Features
- **Chat Interface**: Interactive web-based chat for document Q&A
- **Document Processing**: Support for PDF, Word, and text documents
- **Azure Integration**: Seamless integration with Azure AI services
- **Search Capabilities**: Vector, text, and hybrid search modes
- **Deployment Automation**: One-command deployment with Azure Developer CLI

### Technical Details
- Python-based backend with Quart framework
- React-based frontend with TypeScript
- Azure OpenAI for language model capabilities
- Azure Cognitive Search for document indexing
- Azure Blob Storage for document storage
- Azure App Service for hosting

## [0.9.0] - 2023-10-15 (Beta)

### Added
- Beta release for testing and feedback
- Core RAG functionality implementation
- Basic Azure service integration
- Initial deployment scripts

### Changed
- Performance optimizations based on alpha testing
- Improved error handling and logging
- Enhanced user interface design

### Fixed
- Document chunking algorithm improvements
- Search relevance scoring adjustments
- Memory usage optimizations

## [0.8.0] - 2023-09-30 (Alpha)

### Added
- Alpha release for early adopters
- Basic chat functionality
- Document upload and indexing
- Simple search implementation

### Known Issues
- Limited error handling
- Basic user interface
- No authentication system
- Limited document format support

---

## Version History Summary

| Version | Release Date | Key Features |
|---------|-------------|--------------|
| 1.2.0 | 2024-01-10 | SharePoint integration, Enhanced admin dashboard |
| 1.1.0 | 2023-12-15 | Container Apps, Observability, Feedback system |
| 1.0.0 | 2023-11-01 | Initial GA release with core RAG functionality |
| 0.9.0 | 2023-10-15 | Beta release with performance improvements |
| 0.8.0 | 2023-09-30 | Alpha release for early testing |

## Upgrade Instructions

### From 1.1.x to 1.2.0
1. Update environment variables for SharePoint integration
2. Run `azd up` to deploy new container configuration
3. Update admin dashboard permissions if needed
4. Test SharePoint connector functionality

### From 1.0.x to 1.1.0
1. Backup existing data and configuration
2. Update Azure Developer CLI to latest version
3. Run `azd up` to migrate to Container Apps
4. Reconfigure Application Insights if needed
5. Test authentication and authorization

### From 0.9.x to 1.0.0
1. Review breaking changes in API endpoints
2. Update client applications to use new authentication
3. Migrate data from beta storage format
4. Update deployment scripts to use production configuration

## Breaking Changes

### Version 1.2.0
- SharePoint configuration requires new environment variables
- Admin API endpoints changed authentication requirements
- Some feedback data structure changes

### Version 1.1.0
- Migration from App Service to Container Apps
- New authentication flow with Azure AD
- API endpoint structure changes
- Environment variable naming updates

### Version 1.0.0
- API endpoints restructured for production use
- Authentication system completely rewritten
- Document storage format changes
- Configuration file format updates

## Deprecation Notices

### Deprecated in 1.2.0
- Legacy citation format (will be removed in 2.0.0)
- Old admin API endpoints (use new `/admin/v2/` endpoints)

### Deprecated in 1.1.0
- App Service deployment method (use Container Apps)
- Basic authentication (use Azure AD)

### Removed in 1.0.0
- Beta API endpoints
- Development-only authentication
- Legacy document storage format

## Migration Guides

### Migrating to Latest Version

1. **Backup Current Deployment**:
   ```bash
   # Export current configuration
   azd env get-values > backup-config.env
   
   # Backup search index
   az search index export --name your-index --service-name your-search --output-file index-backup.json
   ```

2. **Update Azure Developer CLI**:
   ```bash
   # Update azd to latest version
   curl -fsSL https://aka.ms/install-azd.sh | bash -s -- --version latest
   ```

3. **Deploy Latest Version**:
   ```bash
   # Pull latest code
   git pull origin main
   
   # Deploy with existing environment
   azd up
   ```

4. **Verify Migration**:
   ```bash
   # Test health endpoints
   curl https://your-app.azurecontainerapps.io/health
   
   # Test authentication
   curl https://your-app.azurecontainerapps.io/auth_setup
   ```

### Data Migration Scripts

For major version upgrades, migration scripts are available in the `/scripts/migration/` directory:

- `migrate-1.1-to-1.2.py`: SharePoint configuration migration
- `migrate-1.0-to-1.1.py`: Container Apps migration
- `migrate-0.9-to-1.0.py`: Production configuration migration

## Support and Compatibility

### Azure Service Compatibility

| Azure Service | Minimum Version | Recommended Version |
|---------------|----------------|-------------------|
| Azure OpenAI | 2023-03-15-preview | 2023-12-01-preview |
| Cognitive Search | 2023-07-01-preview | 2023-11-01 |
| Container Apps | 2023-05-01 | 2023-11-02-preview |
| Application Insights | v2.1 | v2.1 |

### Python Dependencies

Major dependency versions by release:

| Package | v1.2.0 | v1.1.0 | v1.0.0 |
|---------|--------|--------|--------|
| Quart | 0.19.4 | 0.19.0 | 0.18.0 |
| Azure SDK | 1.15.0 | 1.14.0 | 1.13.0 |
| OpenAI | 1.6.1 | 1.3.0 | 0.28.0 |
| LangChain | 0.1.0 | 0.0.350 | 0.0.325 |

## Known Issues

### Current Known Issues (v1.2.0)
- SharePoint large file sync may timeout on slow connections
- Admin dashboard export functionality has memory limits for large datasets
- Citation generation occasionally fails for password-protected documents

### Resolved Issues
- ✅ Authentication loops in certain browser configurations (fixed in 1.2.0)
- ✅ Memory leaks during large document processing (fixed in 1.1.0)
- ✅ Search index corruption with special characters (fixed in 1.0.1)

## Contributing

### Changelog Guidelines

When contributing to this project:

1. **Add entries to [Unreleased]** section
2. **Use conventional commit format**:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `refactor:` for code refactoring
   - `perf:` for performance improvements

3. **Include breaking changes** in the appropriate section
4. **Reference GitHub issues** where applicable

### Release Process

1. Update version numbers in relevant files
2. Move [Unreleased] changes to new version section
3. Update compatibility tables and migration guides
4. Create GitHub release with changelog notes
5. Update documentation and deployment templates

---

*For technical support and questions about specific versions, please refer to the [troubleshooting guide](troubleshooting.md) or create an issue on GitHub.* 