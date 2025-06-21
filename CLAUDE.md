# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAGTrace is a comprehensive RAG (Retrieval-Augmented Generation) evaluation framework that provides quantitative assessment and analysis of RAG system performance. Built on the [RAGAS](https://github.com/explodinggradients/ragas) framework by ExplodingGradients, it implements Clean Architecture principles with full dependency injection.

**Key Features:**
- **Multi-LLM Support**: Google Gemini 2.5 Flash and Naver HCX-005
- **Multi-Embedding Support**: Google Gemini Embedding and Naver HCX Embedding  
- **Interactive Web Dashboard**: Real-time evaluation with Streamlit
- **Complete Dependency Injection**: Using dependency-injector framework
- **Clean Architecture**: Domain, Application, Infrastructure, Presentation layers
- **Flexible Data Handling**: Supports multiple datasets with automatic detection
- **Comprehensive Metrics**: Faithfulness, Answer Relevancy, Context Recall/Precision
- **Historical Tracking**: SQLite-based evaluation history with visualization
- **Production Ready**: Error handling, timeout management, and user-friendly interfaces

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
# Start the interactive web dashboard
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
# Basic evaluation (supports both with and without .json extension)
python cli.py evaluate evaluation_data
python cli.py evaluate evaluation_data.json

# LLM selection
python cli.py evaluate evaluation_data.json --llm gemini
python cli.py evaluate evaluation_data.json --llm hcx

# Independent LLM and embedding model selection
python cli.py evaluate evaluation_data.json --llm gemini --embedding hcx
python cli.py evaluate evaluation_data.json --llm hcx --embedding gemini

# Custom prompt types
python cli.py evaluate evaluation_data.json --prompt-type nuclear_hydro_tech
python cli.py evaluate evaluation_data.json --prompt-type korean_formal

# Save results to file
python cli.py evaluate evaluation_data.json --output results.json

# Verbose output with detailed logs
python cli.py evaluate evaluation_data.json --verbose

# Information commands
python cli.py list-datasets
python cli.py list-prompts
python cli.py --help
```

### Simple Evaluation (Basic)
```bash
# Quick evaluation with default settings
python src/presentation/main.py
```

## Environment Setup

### Required API Keys

Create a `.env` file with your API credentials:

```bash
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Naver Cloud CLOVA Studio API Key (for HCX-005)
CLOVA_STUDIO_API_KEY=your_clova_studio_api_key_here

# Optional: Override default LLM
DEFAULT_LLM=gemini  # or "hcx"
```

### Dependencies Installation

```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install dependency-injector ragas google-generativeai python-dotenv
pip install streamlit plotly pandas numpy requests
```

### Full Requirements
```txt
# Core evaluation
dependency-injector>=4.48.1
ragas>=0.1.0
google-generativeai>=0.3.0
python-dotenv>=1.0.0

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
- **Multi-Embedding Support**: Google Gemini Embedding and Naver HCX Embedding
- **Optimized Performance**: No rate limiting for improved evaluation speed
- **Error Handling**: Comprehensive timeout and retry mechanisms
- **Runtime Selection**: Dynamic LLM and embedding model switching via CLI and web UI
- **Independent Selection**: LLM and embedding models can be chosen independently

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
- **RAGAS Score**: Combined metric average

## Important Files

### Entry Points
- `cli.py` - Advanced CLI with LLM selection
- `src/presentation/main.py` - Simple CLI entry point
- `run_dashboard.py` - Web dashboard launcher

### Core Architecture  
- `src/container.py` - Dependency injection container
- `src/config.py` - Configuration management
- `src/domain/` - Domain models and entities
- `src/application/` - Use cases and business logic
- `src/infrastructure/` - External adapters and services

### LLM and Embedding Adapters
- `src/infrastructure/llm/gemini_adapter.py` - Google Gemini LLM integration
- `src/infrastructure/llm/hcx_adapter.py` - Naver HCX LLM integration
- `src/infrastructure/embedding/hcx_adapter.py` - Naver HCX Embedding integration

### Web Components
- `src/presentation/web/main.py` - Main dashboard
- `src/presentation/web/components/llm_selector.py` - LLM selection UI
- `src/presentation/web/components/prompt_selector.py` - Prompt type selection

### Data and Documentation
- `data/evaluation_data.json` - Sample evaluation datasets
- `data/db/evaluations.db` - SQLite evaluation history
- `docs/RAGTRACE_METRICS.md` - Comprehensive metric explanations in Korean

## Web Dashboard Features

### Interactive Evaluation
- **LLM Selection**: Choose between Gemini and HCX in web UI
- **Prompt Customization**: Default, Korean tech, multilingual options
- **Real-time Progress**: Live evaluation status and metrics
- **Dataset Management**: Upload and select evaluation datasets

### Analytics and Monitoring
- **Historical Tracking**: SQLite-based evaluation history
- **Performance Comparison**: Side-by-side LLM comparisons
- **Detailed Analysis**: Individual QA pair examination
- **Metrics Visualization**: Interactive charts with Plotly

### Advanced Features
- **Streamlit State Management**: Persistent UI state across pages
- **Error Recovery**: Graceful handling of API failures
- **Export Capabilities**: JSON/CSV result export
- **Responsive Design**: Mobile-friendly interface

## Development Guidelines

### Requirements
- **Python**: 3.11+ required
- **Virtual Environment**: Use uv for dependency management
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
2. **Rate Limiting**: Adjust `*_REQUESTS_PER_MINUTE` in config
3. **Import Errors**: Install missing dependencies with `uv pip install`
4. **Database Issues**: Delete `data/db/evaluations.db` to reset

### Debug Commands
```bash
# Test basic connectivity
python hello.py

# Check container configuration  
python -c "from src.container import container; print('Container OK')"

# Validate datasets
python cli.py list-datasets

# Test LLM adapters
python -c "from src.container import get_evaluation_use_case_with_llm; print('DI OK')"
```

## Execution Instructions

### Quick Start (Web Dashboard)
```bash
# 1. Set up environment
echo "GEMINI_API_KEY=your_key_here" > .env

# 2. Install dependencies
uv pip install dependency-injector ragas google-generativeai python-dotenv streamlit plotly pandas numpy

# 3. Start web dashboard
streamlit run src/presentation/web/main.py

# 4. Open browser to http://localhost:8501
```

### CLI Evaluation
```bash
# Basic evaluation
python cli.py

# With options
python cli.py --dataset evaluation_data --llm gemini --embedding gemini

# HCX model (requires CLOVA_STUDIO_API_KEY)
python cli.py --llm hcx --embedding hcx
```

### Testing System Components
```bash
# Test connectivity
python hello.py

# Test dependency injection
python -c "from src.container import container; print('✅ Container loaded successfully')"

# List available datasets
python cli.py list-datasets

# Validate configuration
python -c "from src.config import settings; print(f'✅ Default LLM: {settings.DEFAULT_LLM}')"
```