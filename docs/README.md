# RAGTrace Documentation

Welcome to the RAGTrace documentation! This folder contains comprehensive guides for installation, development, troubleshooting, and usage.

## 📚 Core Documentation

### 🚀 Getting Started
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Complete installation guide for all platforms and environments
  - Docker deployment (recommended)
  - Local development setup
  - Windows enterprise installation
  - Offline/air-gapped deployment
  - Environment configuration
  - Verification steps

- **[Windows_Offline_Installation_Guide.md](Windows_Offline_Installation_Guide.md)** - Comprehensive guide for Windows air-gapped environments
  - Step-by-step offline package generation
  - Detailed installation procedures
  - BGE-M3 model setup for offline use
  - Common issues and solutions
  - Complete process from preparation to execution

### 🏗️ Development
- **[ARCHITECTURE_AND_DEVELOPMENT.md](ARCHITECTURE_AND_DEVELOPMENT.md)** - Architecture overview and development guide
  - Clean Architecture implementation
  - Development environment setup
  - Feature extension guide
  - Adding new LLM providers
  - Testing and quality assurance
  - Best practices

### 🆘 Support
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Comprehensive troubleshooting guide
  - Common installation issues
  - Platform-specific problems
  - Performance optimization
  - Debug techniques
  - Emergency recovery

## 📖 User Guides

### 📊 Core Features
- **[RAGTRACE_METRICS.md](RAGTRACE_METRICS.md)** - Complete guide to RAGAS evaluation metrics
  - All 5 core metrics: Faithfulness, Answer Relevancy, Context Recall, Context Precision, Answer Correctness
  - Interpretation guidelines with practical examples
  - Korean technical documentation
  - Advanced analytics and statistical analysis

- **[Data_Import_Guide.md](Data_Import_Guide.md)** - Excel/CSV data import and conversion
  - Supported formats
  - Column requirements
  - Validation procedures
  - Batch processing

### 🐳 Deployment
- **[Docker_Deployment_Guide.md](Docker_Deployment_Guide.md)** - Docker containerization guide
  - Production deployment
  - Configuration management
  - Scaling strategies
  - Monitoring setup

## 📂 Archive

The `archive/` directory contains historical documentation and files that have been consolidated:

- Architecture analysis reports
- Legacy development guides
- Platform-specific guides (now consolidated)
- Project planning documents
- Completed enhancement plans

## 🎯 Quick Navigation

### New Users
1. Start with [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
2. Review [RAGTRACE_METRICS.md](RAGTRACE_METRICS.md) to understand evaluation
3. Import your data using [Data_Import_Guide.md](Data_Import_Guide.md)

### Developers
1. Read [ARCHITECTURE_AND_DEVELOPMENT.md](ARCHITECTURE_AND_DEVELOPMENT.md)
2. Setup development environment
3. Understand Clean Architecture principles
4. Follow extension guidelines for new features

### System Administrators
1. Use [Docker_Deployment_Guide.md](Docker_Deployment_Guide.md) for production
2. Review [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for enterprise deployment
3. Keep [TROUBLESHOOTING.md](TROUBLESHOOTING.md) handy for issues

### Issues and Support
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
2. Search [GitHub Issues](https://github.com/ntts9990/RAGTrace/issues)
3. Create new issue with diagnostic information

## 📝 Documentation Standards

All documentation follows these principles:

- **User-Centric**: Written from the user's perspective
- **Actionable**: Clear steps with expected outcomes
- **Comprehensive**: Covers common scenarios and edge cases
- **Maintained**: Regularly updated with latest features
- **Cross-Referenced**: Links to related documentation

## 🔄 Updates

Documentation is updated with each release. Check the git history for recent changes:

```bash
git log --oneline docs/
```

For the most current information, always refer to the main branch documentation.

---

**Need help?** Check our [troubleshooting guide](TROUBLESHOOTING.md) or [create an issue](https://github.com/ntts9990/RAGTrace/issues) on GitHub.