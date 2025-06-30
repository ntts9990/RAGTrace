# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAGTrace is a comprehensive RAG (Retrieval-Augmented Generation) evaluation framework that provides quantitative assessment and analysis of RAG system performance. Built on the [RAGAS](https://github.com/explodinggradients/ragas) framework by ExplodingGradients, it implements Clean Architecture principles with full dependency injection.

**Key Features:**
- **Multi-LLM Support**: Google Gemini 2.5 Flash and Naver HCX-005
- **Multi-Embedding Support**: Google Gemini, Naver HCX, and BGE-M3 Local Embedding
- **Excel/CSV Data Import**: Native support for Excel (.xlsx, .xls) and CSV files with automatic format detection
- **BGE-M3 GPU Auto-Detection**: Automatic CUDA/MPS/CPU detection with optimization
- **Local Model Support**: Fully offline embedding processing with BGE-M3
- **Interactive Web Dashboard**: Real-time evaluation with Streamlit
- **Complete Dependency Injection**: Using dependency-injector framework
- **Clean Architecture**: Domain, Application, Infrastructure, Presentation layers
- **Flexible Data Handling**: Supports multiple datasets with automatic detection and batch processing
- **Comprehensive Metrics**: All 5 RAGAS metrics including Answer Correctness
- **Advanced Analytics**: EDA, time series analysis, anomaly detection, statistical analysis
- **Historical Tracking**: SQLite-based evaluation history with visualization
- **Production Ready**: Error handling, timeout management, and user-friendly interfaces
- **Centralized Configuration**: All default values managed in single config file

## Architecture

The project follows Clean Architecture with complete dependency injection:

### Core Layers
- `src/domain/` - Core domain models, entities, and value objects
- `src/application/` - Business logic, use cases, and port interfaces  
- `src/infrastructure/` - External adapters (LLM, storage, RAGAS framework)
- `src/presentation/` - Entry points (CLI, web dashboard)

### Dependency Injection
- `src/container.py` - Centralized DI container using dependency-injector
- All services and adapters are managed through the container
- Support for runtime LLM selection and configuration

## Running the Application

### Web Dashboard (Recommended)
```bash
# Start the interactive web dashboard (UV recommended)
uv run streamlit run src/presentation/web/main.py

# Or using Just
just dashboard

# Legacy method
python run_dashboard.py
```
Access at: http://localhost:8501

**Dashboard Features:**
- **LLM Selection**: Choose between Gemini and HCX models with real-time validation
- **Embedding Model Choice**: Independent LLM and embedding model selection
- **Prompt Type Selection**: Default, Korean tech, or multilingual prompts
- **Dataset Management**: Automatic detection and validation of evaluation datasets
- **Real-time Evaluation**: Live progress tracking with spinner and status updates
- **Interactive Visualization**: Radar charts, bar charts, and trend analysis
- **Historical Tracking**: SQLite-based evaluation history with comparison tools
- **Detailed Analysis**: Individual QA pair examination and metric explanations

### CLI Evaluation (Advanced)
```bash
# Excel/CSV data import and conversion
uv run python cli.py import-data your_data.xlsx --validate --output converted_data.json
uv run python cli.py import-data your_data.csv --validate --batch-size 100

# Basic evaluation with UV (recommended)
uv run python cli.py evaluate evaluation_data
uv run python cli.py evaluate evaluation_data.json

# LLM selection
uv run python cli.py evaluate evaluation_data.json --llm gemini
uv run python cli.py evaluate evaluation_data.json --llm hcx

# Independent LLM and embedding model selection
uv run python cli.py evaluate evaluation_data.json --llm gemini --embedding hcx
uv run python cli.py evaluate evaluation_data.json --llm hcx --embedding gemini

# Custom prompt types
uv run python cli.py evaluate evaluation_data.json --prompt-type nuclear_hydro_tech
uv run python cli.py evaluate evaluation_data.json --prompt-type korean_formal

# Save results to file
uv run python cli.py evaluate evaluation_data.json --output results.json

# Verbose output with detailed logs
uv run python cli.py evaluate evaluation_data.json --verbose

# Information commands
uv run python cli.py list-datasets
uv run python cli.py list-prompts
uv run python cli.py --help

# Using Just for convenience
just eval evaluation_data
just eval-llm evaluation_data gemini
```

#### Excel/CSV Data Import
The system supports importing evaluation data from Excel (.xlsx, .xls) and CSV files with automatic format detection and validation.

**Required Columns:**
- `question`: The question to be evaluated
- `contexts`: Reference contexts (supports multiple formats)
- `answer`: System-generated answer
- `ground_truth`: Expected correct answer

**Contexts Format Options:**
1. **JSON Array** (recommended): `["context 1", "context 2", "context 3"]`
2. **Semicolon separated**: `context 1;context 2;context 3`
3. **Pipe separated**: `context 1|context 2|context 3`
4. **Single context**: `single long context content`

**Import Features:**
- Automatic encoding detection (UTF-8, CP949, EUC-KR)
- Data validation with detailed error reporting
- Batch processing for large datasets
- Support for various context formats

### Simple Evaluation (Basic)
```bash
# Quick evaluation with default settings (UV recommended)
uv run python src/presentation/main.py

# With parameters
uv run python src/presentation/main.py evaluation_data_variant1 --llm gemini --embedding gemini --prompt-type default

# Using Just
just quick-test
```

## Environment Setup

### UV Package Manager

**IMPORTANT: This project uses UV for dependency management. UV is REQUIRED.**

#### Install UV
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Homebrew (macOS)
brew install uv

# pip
pip install uv
```

#### Quick Setup
```bash
# Automated setup (recommended)
chmod +x uv-setup.sh
./uv-setup.sh

# Or manual setup
uv sync --all-extras
```

### Required API Keys

Create a `.env` file with your API credentials:

```bash
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Naver Cloud CLOVA Studio API Key (for HCX-005)
CLOVA_STUDIO_API_KEY=your_clova_studio_api_key_here

# Optional: Override default models
DEFAULT_LLM=hcx  # or "gemini"
DEFAULT_EMBEDDING=bge_m3  # or "gemini", "hcx"

# Optional: BGE-M3 Local Embedding Configuration
BGE_M3_MODEL_PATH="./models/bge-m3"  # Local model path
# BGE_M3_DEVICE="auto"  # auto, cpu, cuda, mps (auto-detection if commented)
```

### Dependencies Installation

```bash
# Install all dependencies with UV
uv sync --all-extras

# Install specific extras
uv sync --extra dev        # Development tools
uv sync --extra performance # Performance monitoring
uv sync --extra analysis   # Data analysis tools

# Production install (no dev dependencies)
uv sync --no-dev
```

### Full Requirements
```txt
# Core evaluation
dependency-injector>=4.48.1
ragas>=0.1.0
google-generativeai>=0.3.0
python-dotenv>=1.0.0

# Local embeddings
sentence-transformers>=2.2.2
torch>=2.0.0

# Web dashboard
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0
numpy>=1.24.0

# Additional utilities
requests>=2.31.0
datasets>=2.14.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

## Key Implementation Details

### LLM Integration
- **Multi-LLM Support**: Google Gemini 2.5 Flash and Naver HCX-005
- **Multi-Embedding Support**: Google Gemini, Naver HCX, and BGE-M3 Local Embedding
- **BGE-M3 Auto-Detection**: Automatic GPU/CPU detection (CUDA, MPS, CPU) with performance optimization
- **Local Model Support**: Fully offline embedding processing with BGE-M3 sentence-transformers
- **HTTP Direct Call Architecture**: Custom HTTP wrappers to bypass LangChain timeout issues
- **Stability Improvements**: HttpGeminiWrapper and GeminiHttpEmbeddingAdapter for reliable API calls
- **Error Handling**: Comprehensive timeout and retry mechanisms with network stability
- **Runtime Selection**: Dynamic LLM and embedding model switching via CLI and web UI
- **Independent Selection**: LLM and embedding models can be chosen independently
- **Centralized Configuration**: All model types and settings managed in single config file

### Data Management
- **Evaluation Data**: JSON format in `data/` directory
- **Results Storage**: SQLite database with full metadata
- **Supported Formats**: Hugging Face Dataset compatible

### Architecture Patterns
- **Clean Architecture**: Complete separation of concerns
- **Dependency Injection**: Full DI with dependency-injector library
- **Port-Adapter Pattern**: All external dependencies abstracted
- **Factory Pattern**: Dynamic object creation and configuration

### Evaluation Metrics
- **Faithfulness**: Answer grounding in provided context
- **Answer Relevancy**: Question-answer alignment
- **Context Recall**: Information retrieval completeness  
- **Context Precision**: Retrieved context accuracy
- **Answer Correctness**: Ground truth alignment and factual accuracy
- **RAGAS Score**: Combined metric average

## Important Files

### Entry Points
- `cli.py` - Advanced CLI with LLM selection
- `src/presentation/main.py` - Simple CLI entry point
- `run_dashboard.py` - Web dashboard launcher (legacy)
- `hello.py` - Environment and connectivity test script

### UV Configuration Files
- `pyproject.toml` - Project metadata, dependencies, and tool configurations
- `uv.toml` - UV-specific settings (cache, resolution strategy)
- `uv.lock` - Locked dependency versions (generated automatically)
- `.python-version` - Python version specification for UV
- `uv-setup.sh` - Automated UV environment setup script
- `justfile` - Task runner with UV-based commands
- `UV_SETUP.md` - Detailed UV setup and usage guide

### Core Architecture  
- `src/container.py` - Dependency injection container
- `src/config.py` - Configuration management
- `src/domain/` - Domain models and entities
- `src/application/` - Use cases and business logic
- `src/infrastructure/` - External adapters and services

### LLM and Embedding Adapters
- `src/infrastructure/llm/gemini_adapter.py` - Google Gemini LLM integration with HTTP wrapper
- `src/infrastructure/llm/http_gemini_wrapper.py` - HTTP direct call wrapper for Gemini LLM
- `src/infrastructure/llm/hcx_adapter.py` - Naver HCX LLM integration
- `src/infrastructure/embedding/gemini_http_adapter.py` - HTTP direct call adapter for Gemini Embedding
- `src/infrastructure/embedding/hcx_adapter.py` - Naver HCX Embedding integration
- `src/infrastructure/embedding/bge_m3_adapter.py` - BGE-M3 local embedding with GPU auto-detection

### Web Components
- `src/presentation/web/main.py` - Main dashboard
- `src/presentation/web/components/llm_selector.py` - LLM selection UI
- `src/presentation/web/components/prompt_selector.py` - Prompt type selection

### Data and Documentation
- `data/evaluation_data.json` - Sample evaluation datasets
- `data/db/evaluations.db` - SQLite evaluation history
- `docs/RAGTRACE_METRICS.md` - Comprehensive metric explanations in Korean
- `docs/LLM_Customization_Manual.md` - Guide for adding new LLM models
- `docs/Offline_LLM_Integration_Guide.md` - Guide for offline/air-gapped deployment
- `docs/BGE_M3_GPU_Guide.md` - BGE-M3 GPU optimization guide
- `docs/Troubleshooting_Guide.md` - Comprehensive troubleshooting guide

## Web Dashboard Features

### Interactive Evaluation
- **LLM Selection**: Choose between Gemini and HCX in web UI
- **Prompt Customization**: Default, Korean tech, multilingual options
- **Real-time Progress**: Live evaluation status and metrics
- **Dataset Management**: Upload and select evaluation datasets

### Analytics and Monitoring
- **Historical Tracking**: SQLite-based evaluation history
- **Performance Comparison**: Side-by-side LLM comparisons
- **Detailed Analysis**: Individual QA pair examination with 7 analysis tabs
- **Metrics Visualization**: Interactive charts with Plotly
- **EDA Analysis**: Exploratory data analysis with correlation matrices
- **Time Series Analysis**: Performance trends and moving averages
- **Anomaly Detection**: Automated outlier identification
- **Advanced Statistics**: Normality tests, confidence intervals, hypothesis testing

### Advanced Features
- **Streamlit State Management**: Persistent UI state across pages
- **Error Recovery**: Graceful handling of API failures
- **Export Capabilities**: JSON/CSV/Markdown result export with automatic report generation
- **Responsive Design**: Mobile-friendly interface

## Recent Updates

### ✅ Advanced Analytics and Answer Correctness Integration (December 2024)

Added comprehensive advanced analytics and complete Answer Correctness support:

**New Advanced Analytics Features**:
- **EDA (Exploratory Data Analysis)**: Dataset overview, metric distributions, correlation analysis, scatter plot matrices
- **Time Series Analysis**: Performance trends, moving averages, change rate analysis, periodicity detection
- **Anomaly Detection**: IQR, Z-Score, and Isolation Forest methods for outlier identification
- **Advanced Statistics**: Normality testing, confidence intervals, hypothesis testing, effect size analysis

**Answer Correctness Integration**:
- **Complete UI Support**: Added Answer Correctness to all web UI components and visualizations
- **Metrics Explanation**: Comprehensive Korean explanations with practical examples
- **Export Functionality**: Fixed summary CSV and package export to include Answer Correctness
- **Database Schema**: Updated SQLite schema to store and retrieve Answer Correctness data

**Implementation**:
- `src/presentation/web/components/detailed_analysis.py` - 4 new analysis tabs with advanced features
- `src/presentation/web/components/metrics_explanation.py` - Complete Answer Correctness explanation
- `src/application/services/result_exporter.py` - Enhanced export functionality with Answer Correctness
- `src/infrastructure/repository/sqlite_adapter.py` - Database schema updated for Answer Correctness
- Added scipy and scikit-learn dependencies for advanced statistical analysis

### ✅ BGE-M3 Local Embedding Integration (2024)

Added comprehensive local embedding support with GPU auto-detection:

**New Features**:
- **BGE-M3 Local Embedding**: Complete offline embedding processing using sentence-transformers
- **GPU Auto-Detection**: Automatic CUDA/MPS/CPU detection with device-specific optimization
- **Performance Optimization**: Device-specific batch sizes and memory management
- **Multilingual Support**: BGE-M3 supports 100+ languages with excellent cross-lingual performance
- **Air-gapped Deployment**: Full offline capability for enterprise environments

**Implementation**:
- `src/infrastructure/embedding/bge_m3_adapter.py` - BGE-M3 adapter with auto-detection
- `docs/BGE_M3_GPU_Guide.md` - Comprehensive GPU optimization guide
- `docs/Offline_LLM_Integration_Guide.md` - Complete offline deployment guide
- GPU memory monitoring and automatic cleanup
- Configurable device selection with smart defaults

**Performance Results**:
- CUDA: ~60 docs/sec with GPU acceleration
- MPS (Apple Silicon): ~15 docs/sec with Metal acceleration  
- CPU: ~40 docs/sec with multi-core optimization
- 1024-dimensional embeddings with cosine similarity optimization

### ✅ Enhanced Logging and Configuration Management (2024)

**Embedding Model Visibility**:
- Added comprehensive embedding model logging throughout the evaluation process
- Clear identification of which LLM and embedding models are being used
- Device information display for BGE-M3 (CPU/GPU/MPS)

**Centralized Configuration**:
- Eliminated all hardcoded default values across the codebase
- Centralized model type definitions in `src/config.py`
- Dynamic model validation with clear error messages
- Consistent display names for web UI components

**Files Updated**:
- `src/config.py` - Added SUPPORTED_*_TYPES and DISPLAY_NAMES constants
- `src/presentation/main.py` - Added embedding model logging
- `src/infrastructure/evaluation/ragas_adapter.py` - Enhanced evaluation logging
- `cli.py` - Dynamic model choices from config
- Web UI components - Centralized display names and validation

### ✅ LangChain Timeout Issue Resolution (2024)

The project has successfully resolved the LangChain Google GenAI timeout issue that was causing evaluations to hang at 0% progress:

**Problem**: 
- RAGAS evaluations would start but never progress beyond 0%
- LangChain Google GenAI library calls were hanging due to DNS resolution issues
- Both `ChatGoogleGenerativeAI` and `GoogleGenerativeAIEmbeddings` were affected

**Solution Implemented**:
1. **HttpGeminiWrapper**: Custom LangChain-compatible wrapper that calls Google Gemini API directly via HTTP
2. **GeminiHttpEmbeddingAdapter**: HTTP-based embedding adapter for Google Gemini embeddings  
3. **Container Updates**: Modified dependency injection to use HTTP adapters instead of LangChain libraries
4. **Network Stability**: Improved error handling and timeout management

**Results**:
- ✅ Evaluations now complete successfully with actual RAGAS scores
- ✅ No more 0% progress hangs or timeouts
- ✅ Both CLI and Streamlit work reliably
- ✅ Typical evaluation time: ~1-2 minutes for 8 QA pairs

**Files Modified**:
- `src/infrastructure/llm/http_gemini_wrapper.py` (new)
- `src/infrastructure/embedding/gemini_http_adapter.py` (new)
- `src/infrastructure/llm/gemini_adapter.py` (updated to use HTTP wrapper)
- `src/container.py` (updated DI configuration)

## Development Guidelines

### Requirements
- **Python**: 3.11+ required
- **Virtual Environment**: Use uv for dependency management (ALWAYS use `uv pip` instead of `pip`)
- **Type Hints**: Comprehensive typing throughout codebase
- **Testing**: Built-in test utilities and mock evaluations

### Code Structure
- **Clean Architecture**: Strict layer separation
- **SOLID Principles**: Dependency inversion and single responsibility
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured logging with appropriate levels

### Extension Points
- **New LLM Integration**: Add adapters in `src/infrastructure/llm/`
- **Custom Metrics**: Extend evaluation in `src/domain/`
- **Additional UI**: Add components in `src/presentation/web/components/`
- **Data Sources**: Implement repositories in `src/infrastructure/repository/`

## Troubleshooting

### Common Issues
1. **API Key Errors**: Ensure `.env` file has correct API keys
2. **Evaluation Timeout**: Fixed with HTTP wrapper implementation (no longer an issue)
3. **Import Errors**: Install missing dependencies with `uv sync --all-extras`
4. **Database Issues**: Delete `data/db/evaluations.db` to reset
5. **LangChain Issues**: Uses custom HTTP wrappers to bypass LangChain timeout problems
6. **UV Issues**: Use `uv cache clean` and `uv lock` to fix dependency problems

### Just Commands Reference
```bash
# Setup and installation
just setup              # Complete environment setup
just install            # Install dependencies only
just install-all        # Install with all extras

# Running applications
just dashboard          # Start Streamlit dashboard
just eval              # Run basic evaluation
just eval-llm dataset llm # Run evaluation with specific LLM

# Development
just test              # Run tests
just test-cov          # Run tests with coverage
just format            # Format code with black
just lint              # Lint with ruff
just typecheck         # Type check with mypy
just check             # Run all quality checks

# Maintenance
just clean             # Clean cache and temp files
just update            # Update dependencies
just build             # Build package

# Utilities
just info              # Show project information
just --list            # List all available commands
```

### Debug Commands
```bash
# Test basic connectivity (UV recommended)
uv run python hello.py

# Check container configuration  
uv run python -c "from src.container import container; print('Container OK')"

# Validate datasets
uv run python cli.py list-datasets

# Test LLM adapters
uv run python -c "from src.container import get_evaluation_use_case_with_llm; print('DI OK')"

# Test evaluation directly (should complete without timeout)
uv run python src/presentation/main.py evaluation_data_variant1 --llm gemini --embedding gemini

# API connectivity diagnosis (if needed)
uv run python diagnose_api_issue.py

# Using Just commands (convenient)
just test-connection
just eval
just diagnose
just info
```

## Execution Instructions

### Quick Start (Web Dashboard)
```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone <repository-url>
cd RAGTrace

# 3. Automated setup
chmod +x uv-setup.sh
./uv-setup.sh

# 4. Set up environment (edit .env file with your API keys)
# GEMINI_API_KEY=your_key_here

# 5. Start web dashboard
uv run streamlit run src/presentation/web/main.py

# 6. Open browser to http://localhost:8501
```

### CLI Evaluation
```bash
# Basic evaluation with UV
uv run python cli.py evaluate evaluation_data

# With options
uv run python cli.py evaluate evaluation_data --llm gemini --embedding gemini

# HCX model (requires CLOVA_STUDIO_API_KEY)
uv run python cli.py evaluate evaluation_data --llm hcx --embedding hcx

# Using Just commands
just eval evaluation_data
just eval-llm evaluation_data gemini
```

### Testing System Components
```bash
# Test connectivity with UV
uv run python hello.py

# Test dependency injection
uv run python -c "from src.container import container; print('✅ Container loaded successfully')"

# List available datasets
uv run python cli.py list-datasets

# Validate configuration
uv run python -c "from src.config import settings; print(f'✅ Default LLM: {settings.DEFAULT_LLM}')"

# Using Just commands
just test-connection
just info
```

## AI Collaboration (Claude Code + Gemini)
Claude Code can collaborate with Gemini to solve complex problems through bash commands. This enables a problem-solving dialogue between the two AI assistants.
### How to Collaborate
1. **Execute Gemini commands via bash**: Use the `gemini` command in bash to interact with Gemini
2. **Pass prompts as arguments**: Provide your question or request as arguments to the gemini command
3. **Iterative problem solving**: Use the responses from Gemini to refine your approach and continue the dialogue
### Example Usage
```bash
# Ask Gemini for help with a specific problem
gemini "How should I optimize this Flutter widget for better performance?"
# Request code review or suggestions
gemini "Review this GetX controller implementation and suggest improvements"
# Collaborate on debugging
gemini "This error occurs when running flutter build ios. What could be the cause?"
```
### Collaboration Workflow
1. **Identify complex problems**: When encountering challenging issues, consider leveraging Gemini's perspective
2. **Formulate clear questions**: Create specific, context-rich prompts for better responses
3. **Iterate on solutions**: Use responses to refine your approach and ask follow-up questions
4. **Combine insights**: Merge insights from both Claude Code and Gemini for comprehensive solutions