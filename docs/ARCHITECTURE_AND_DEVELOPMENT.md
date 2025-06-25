# RAGTrace Architecture and Development Guide

## 🎯 Overview

This comprehensive guide covers RAGTrace's architecture, development setup, feature extension, and contribution guidelines. RAGTrace implements Clean Architecture principles with full dependency injection to ensure maintainability, testability, and extensibility.

## 🏗️ System Architecture

### Clean Architecture Implementation

RAGTrace follows Robert C. Martin's Clean Architecture pattern with strict layer separation and dependency inversion:

```
src/
├── domain/              # 🏛️ Core Business Logic (No external dependencies)
│   ├── entities/        # EvaluationResult, EvaluationData
│   ├── value_objects/   # Immutable value objects
│   ├── exceptions/      # Domain-specific exceptions
│   └── prompts.py       # Domain-specific prompt definitions
│
├── application/         # 🔧 Use Cases and Business Flows
│   ├── use_cases/       # RunEvaluationUseCase, DataImportUseCase
│   ├── services/        # Application services
│   └── ports/           # Abstract interfaces (contracts)
│
├── infrastructure/      # 🔌 External System Integration (Port implementations)
│   ├── llm/            # LLM adapters (Gemini, HCX, etc.)
│   ├── embedding/      # Embedding model adapters
│   ├── evaluation/     # RAGAS evaluation adapters
│   ├── repository/     # Data persistence adapters
│   └── data_import/    # Data import/export adapters
│
└── presentation/       # 🖥️ User Interface (CLI and Web)
    ├── web/           # Streamlit web dashboard
    └── main.py        # CLI interface
```

### Dependency Flow

The dependency rule ensures that dependencies always point inward:

```
Presentation → Application → Domain ← Infrastructure
```

**Key Principles:**
- Domain layer has no external dependencies
- Infrastructure implements Application ports
- Presentation depends only on Application layer
- Dependency injection manages all connections

### Core Components

#### 1. Domain Layer
```python
# Core entities
@dataclass
class EvaluationData:
    question: str
    contexts: List[str]
    answer: str
    ground_truth: str

@dataclass
class EvaluationResult:
    ragas_score: float
    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float
```

#### 2. Application Layer
```python
# Use case interface
class RunEvaluationUseCase:
    def execute(self, dataset_name: str) -> EvaluationResult:
        # Business logic implementation
        pass

# Port interfaces
class LlmProviderPort(ABC):
    @abstractmethod
    def generate_answer(self, question: str, contexts: List[str]) -> str:
        pass

class EmbeddingProviderPort(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass
```

#### 3. Infrastructure Layer
```python
# Adapter implementations
class GeminiLlmAdapter(LlmProviderPort):
    def __init__(self, api_key: str):
        self.client = GoogleGenerativeAI(api_key=api_key)
    
    def generate_answer(self, question: str, contexts: List[str]) -> str:
        # Gemini-specific implementation
        pass

class HcxLlmAdapter(LlmProviderPort):
    def __init__(self, api_key: str, gateway_key: str):
        self.client = HcxClient(api_key, gateway_key)
    
    def generate_answer(self, question: str, contexts: List[str]) -> str:
        # HCX-specific implementation
        pass
```

### Dependency Injection Container

The container manages all dependencies and provides factory methods:

```python
class Container:
    def __init__(self):
        self.config = Config()
        self.llm_providers = {}
        self.embedding_providers = {}
    
    def get_llm_provider(self, llm_type: str) -> LlmProviderPort:
        # Factory method for LLM providers
        
    def get_evaluation_use_case(self, llm_type: str) -> RunEvaluationUseCase:
        # Factory method for use cases
```

## 🚀 Development Environment Setup

### Prerequisites

**Required:**
- Python 3.11+
- Git
- UV package manager (recommended)

**Recommended:**
- Docker for development
- VS Code with Python extension
- Pre-commit hooks

### Quick Setup

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# Setup development environment
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Verify setup
uv run python hello.py
uv run python cli.py --help
```

### Development Dependencies

```bash
# Core dependencies
uv sync

# Include development tools
uv sync --extra dev

# Include all extras (testing, performance, analysis)
uv sync --all-extras
```

### Environment Configuration

Create `.env` file with required settings:

```bash
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
CLOVA_STUDIO_API_KEY=your_clova_studio_api_key_here

# Model Configuration
DEFAULT_LLM=gemini
DEFAULT_EMBEDDING=bge_m3

# BGE-M3 Local Configuration
BGE_M3_MODEL_PATH="./models/bge-m3"
BGE_M3_DEVICE="auto"

# Development Settings
RAGTRACE_LOG_LEVEL=DEBUG
RAGTRACE_ENV=development
```

## 🔧 Feature Extension Guide

### Adding New LLM Providers

#### 1. Create LLM Adapter

```python
# src/infrastructure/llm/new_llm_adapter.py
from src.application.ports.llm_provider_port import LlmProviderPort

class NewLlmAdapter(LlmProviderPort):
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.client = NewLlmClient(api_key)
    
    def generate_answer(self, question: str, contexts: List[str]) -> str:
        # Implement LLM-specific logic
        prompt = self._build_prompt(question, contexts)
        response = self.client.generate(prompt)
        return response.text
    
    def _build_prompt(self, question: str, contexts: List[str]) -> str:
        # Format prompt for specific LLM
        context_text = "\n".join(contexts)
        return f"Context: {context_text}\n\nQuestion: {question}\n\nAnswer:"
```

#### 2. Update Configuration

```python
# src/config.py
SUPPORTED_LLM_TYPES = [
    "gemini",
    "hcx", 
    "new_llm"  # Add new LLM type
]

LLM_DISPLAY_NAMES = {
    "gemini": "Google Gemini 2.5 Flash",
    "hcx": "Naver HCX-005",
    "new_llm": "New LLM Provider"  # Add display name
}
```

#### 3. Register in Container

```python
# src/container.py
def _create_llm_provider(self, llm_type: str) -> LlmProviderPort:
    if llm_type == "gemini":
        return GeminiLlmAdapter(self.settings.GEMINI_API_KEY)
    elif llm_type == "hcx":
        return HcxLlmAdapter(self.settings.CLOVA_STUDIO_API_KEY)
    elif llm_type == "new_llm":
        return NewLlmAdapter(self.settings.NEW_LLM_API_KEY)  # Add new provider
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")
```

### Adding New Evaluation Metrics

#### 1. Define Domain Entity

```python
# src/domain/entities/evaluation_result.py
@dataclass
class EvaluationResult:
    # Existing metrics
    ragas_score: float
    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float
    
    # New metric
    answer_correctness: Optional[float] = None
```

#### 2. Implement Evaluation Logic

```python
# src/infrastructure/evaluation/custom_metrics.py
class CustomMetricEvaluator:
    def evaluate_answer_correctness(self, 
                                   answer: str, 
                                   ground_truth: str) -> float:
        # Implement custom metric logic
        similarity_score = self._calculate_similarity(answer, ground_truth)
        return similarity_score
```

#### 3. Update RAGAS Adapter

```python
# src/infrastructure/evaluation/ragas_adapter.py
def evaluate(self, dataset: Dataset) -> EvaluationResult:
    # Run standard RAGAS evaluation
    ragas_result = evaluate(dataset, metrics=[...])
    
    # Add custom metrics
    custom_evaluator = CustomMetricEvaluator()
    answer_correctness = custom_evaluator.evaluate_answer_correctness(
        dataset["answer"], dataset["ground_truth"]
    )
    
    return EvaluationResult(
        # Standard metrics
        ragas_score=ragas_result["ragas_score"],
        # ... other metrics
        
        # Custom metric
        answer_correctness=answer_correctness
    )
```

### Adding New Data Import Formats

#### 1. Create Format-Specific Importer

```python
# src/infrastructure/data_import/importers/json_importer.py
from src.infrastructure.data_import.importers.base_importer import BaseImporter

class JsonImporter(BaseImporter):
    def validate_format(self, file_path: str) -> bool:
        return file_path.lower().endswith('.json')
    
    def import_data(self, file_path: str) -> List[EvaluationData]:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [self._convert_to_evaluation_data(item) for item in data]
    
    def _convert_to_evaluation_data(self, item: dict) -> EvaluationData:
        return EvaluationData(
            question=item['question'],
            contexts=item['contexts'],
            answer=item['answer'],
            ground_truth=item['ground_truth']
        )
```

#### 2. Register in Factory

```python
# src/infrastructure/data_import/importers/importer_factory.py
class ImporterFactory:
    @staticmethod
    def create_importer(file_path: str) -> BaseImporter:
        if file_path.endswith('.json'):
            return JsonImporter()
        elif file_path.endswith(('.xlsx', '.xls')):
            return ExcelImporter()
        elif file_path.endswith('.csv'):
            return CsvImporter()
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
```

## 🧪 Testing and Quality Assurance

### Testing Framework

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src tests/

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/
```

### Test Structure

```
tests/
├── unit/                # Unit tests for individual components
│   ├── test_llm_adapters.py
│   ├── test_use_cases.py
│   └── test_domain_entities.py
├── integration/         # Integration tests
│   ├── test_container.py
│   ├── test_evaluation_flow.py
│   └── test_data_import.py
├── e2e/                # End-to-end tests
│   ├── test_cli.py
│   └── test_web_dashboard.py
└── fixtures/           # Test data and mocks
    ├── sample_data.json
    └── mock_responses.py
```

### Code Quality Tools

```bash
# Linting with ruff
uv run ruff check src/

# Code formatting with black
uv run black src/

# Type checking with mypy
uv run mypy src/

# Run all quality checks
uv run pre-commit run --all-files
```

### Writing Tests

#### Unit Test Example

```python
# tests/unit/test_gemini_adapter.py
import pytest
from unittest.mock import Mock, patch
from src.infrastructure.llm.gemini_adapter import GeminiLlmAdapter

class TestGeminiLlmAdapter:
    @pytest.fixture
    def adapter(self):
        return GeminiLlmAdapter(api_key="test_key")
    
    @patch('src.infrastructure.llm.gemini_adapter.GoogleGenerativeAI')
    def test_generate_answer(self, mock_client, adapter):
        # Setup mock
        mock_response = Mock()
        mock_response.text = "Test answer"
        mock_client.return_value.generate.return_value = mock_response
        
        # Execute
        result = adapter.generate_answer("Test question", ["Test context"])
        
        # Assert
        assert result == "Test answer"
        mock_client.return_value.generate.assert_called_once()
```

#### Integration Test Example

```python
# tests/integration/test_evaluation_flow.py
import pytest
from src.container import container
from src.domain.entities.evaluation_data import EvaluationData

class TestEvaluationFlow:
    def test_complete_evaluation_flow(self):
        # Setup
        evaluation_use_case = container.get_evaluation_use_case("gemini")
        
        # Execute
        result = evaluation_use_case.execute("test_dataset")
        
        # Assert
        assert result.ragas_score >= 0.0
        assert result.ragas_score <= 1.0
        assert result.faithfulness is not None
```

## 📦 Deployment and Distribution

### Production Deployment

#### Docker Deployment

```bash
# Build production image
docker build -t ragtrace:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost:8501/health
```

#### Environment-Specific Configuration

```bash
# Production environment
RAGTRACE_ENV=production
RAGTRACE_LOG_LEVEL=INFO
RAGTRACE_DEBUG=false

# Performance tuning
RAGTRACE_BATCH_SIZE=20
RAGTRACE_TIMEOUT=300
RAGTRACE_MAX_WORKERS=4
```

### Package Distribution

#### Creating Offline Packages

```bash
# Enterprise package
python scripts/offline-packaging/create-enterprise-offline.py

# Windows package
.\scripts\offline-packaging\create-windows-offline-safe.ps1

# Simple package
bash scripts/offline-packaging/create-simple-offline.sh
```

## 🔍 Architecture Patterns and Best Practices

### Design Patterns Used

#### 1. Dependency Injection Pattern
```python
# Container manages all dependencies
class Container:
    def __init__(self):
        self._llm_providers = {}
        self._embedding_providers = {}
    
    def get_evaluation_use_case(self, llm_type: str) -> RunEvaluationUseCase:
        llm_provider = self.get_llm_provider(llm_type)
        embedding_provider = self.get_embedding_provider("default")
        
        return RunEvaluationUseCase(
            llm_provider=llm_provider,
            embedding_provider=embedding_provider,
            evaluation_repository=self.get_evaluation_repository()
        )
```

#### 2. Adapter Pattern
```python
# Adapters implement common interfaces for different providers
class GeminiLlmAdapter(LlmProviderPort):
    def generate_answer(self, question: str, contexts: List[str]) -> str:
        # Gemini-specific implementation
        pass

class HcxLlmAdapter(LlmProviderPort):
    def generate_answer(self, question: str, contexts: List[str]) -> str:
        # HCX-specific implementation
        pass
```

#### 3. Factory Pattern
```python
# Factories create objects based on configuration
class LlmProviderFactory:
    @staticmethod
    def create_provider(llm_type: str, config: dict) -> LlmProviderPort:
        if llm_type == "gemini":
            return GeminiLlmAdapter(**config)
        elif llm_type == "hcx":
            return HcxLlmAdapter(**config)
        else:
            raise ValueError(f"Unknown LLM type: {llm_type}")
```

### Best Practices

#### 1. Error Handling
```python
# Use domain-specific exceptions
class RAGTraceError(Exception):
    """Base exception for RAGTrace"""
    pass

class LlmProviderError(RAGTraceError):
    """LLM provider specific errors"""
    pass

class EvaluationError(RAGTraceError):
    """Evaluation process errors"""
    pass

# Implement graceful error handling
try:
    result = llm_provider.generate_answer(question, contexts)
except LlmProviderError as e:
    logger.error(f"LLM provider failed: {e}")
    # Implement fallback or retry logic
    result = fallback_provider.generate_answer(question, contexts)
```

#### 2. Logging and Monitoring
```python
import logging
from src.utils.logging import get_logger

logger = get_logger(__name__)

class EvaluationUseCase:
    def execute(self, dataset_name: str) -> EvaluationResult:
        logger.info(f"Starting evaluation for dataset: {dataset_name}")
        
        try:
            result = self._run_evaluation(dataset_name)
            logger.info(f"Evaluation completed successfully. Score: {result.ragas_score}")
            return result
        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            raise
```

#### 3. Configuration Management
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str
    CLOVA_STUDIO_API_KEY: Optional[str] = None
    
    # Model Configuration
    DEFAULT_LLM: str = "gemini"
    DEFAULT_EMBEDDING: str = "bge_m3"
    
    # Performance Settings
    BATCH_SIZE: int = 10
    TIMEOUT: int = 300
    MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 🚨 Troubleshooting and Debugging

### Common Development Issues

#### 1. Container Configuration Problems
```python
# Debug container setup
def debug_container():
    try:
        container = Container()
        use_case = container.get_evaluation_use_case("gemini")
        print("✅ Container configured correctly")
    except Exception as e:
        print(f"❌ Container error: {e}")
        # Check configuration and dependencies
```

#### 2. LLM Provider Issues
```bash
# Test LLM connectivity
uv run python -c "
from src.container import container
provider = container.get_llm_provider('gemini')
result = provider.generate_answer('Test question', ['Test context'])
print(f'Response: {result}')
"
```

#### 3. Memory and Performance Issues
```python
# Profile memory usage
import psutil
import time

def profile_evaluation():
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    
    # Run evaluation
    result = evaluation_use_case.execute("dataset")
    
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"Memory used: {end_memory - start_memory:.2f} MB")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
```

### Debugging Tools

```bash
# Enable debug logging
export RAGTRACE_LOG_LEVEL=DEBUG

# Run with profiling
uv run python -m cProfile -o profile.stats cli.py evaluate dataset

# Analyze profile
uv run python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

## 📚 Additional Resources

### Documentation
- [Data Import Guide](Data_Import_Guide.md) - Excel/CSV data handling
- [RAGAS Metrics Guide](RAGTRACE_METRICS.md) - Understanding evaluation metrics
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [Docker Deployment Guide](Docker_Deployment_Guide.md) - Container deployment

### External References
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [RAGAS Framework](https://github.com/explodinggradients/ragas)
- [Dependency Injector](https://python-dependency-injector.ets-labs.org/)
- [Streamlit Documentation](https://docs.streamlit.io/)

### Community and Support
- [GitHub Issues](https://github.com/ntts9990/RAGTrace/issues)
- [Discussions](https://github.com/ntts9990/RAGTrace/discussions)
- [Contributing Guidelines](../CONTRIBUTING.md)

---

This architecture guide provides the foundation for understanding and extending RAGTrace. The Clean Architecture approach ensures that the system remains maintainable and testable as it grows in complexity and features.