# RAGTrace Installation Guide

## 🎯 Overview

Comprehensive installation guide for RAGTrace in various environments including Docker, local development, Windows-specific setups, and enterprise offline deployment.

## 🚀 Quick Start (Recommended)

### Docker Installation (Fastest)
```bash
# Clone repository
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# Start with Docker Compose
docker-compose up -d

# Access dashboard
open http://localhost:8501
```

### Local Installation with UV
```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup environment
uv sync --all-extras

# Start dashboard
uv run streamlit run src/presentation/web/main.py
```

## 📋 Installation Methods

### 1. 🐳 Docker Deployment (Production Ready)

**Prerequisites:**
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum

**Standard Setup:**
```bash
# Clone and setup
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d

# Verify installation
docker-compose ps
curl http://localhost:8501/health
```

**Advanced Docker Configuration:**
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  ragtrace:
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - CLOVA_STUDIO_API_KEY=${CLOVA_STUDIO_API_KEY}
      - DEFAULT_LLM=gemini
      - DEFAULT_EMBEDDING=bge_m3
    volumes:
      - ./custom_data:/app/data
      - ./logs:/app/logs
    ports:
      - "8501:8501"
    restart: unless-stopped
```

### 2. 💻 Local Development Setup

**Prerequisites:**
- Python 3.11+
- Git
- 8GB RAM recommended

**Using UV (Recommended):**
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone repository
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# Setup environment
uv sync --all-extras

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Start applications
uv run streamlit run src/presentation/web/main.py  # Web dashboard
uv run python cli.py --help                       # CLI interface
```

**Using pip:**
```bash
# Create virtual environment
python -m venv ragtrace-env
source ragtrace-env/bin/activate  # Windows: ragtrace-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development extras
pip install -r requirements-dev.txt
```

### 3. 🏢 Windows Enterprise Setup

#### Standard Windows Installation

**Prerequisites:**
- Windows 10/11
- Python 3.11+
- PowerShell 5.1+
- Administrator privileges

**Step-by-Step Process:**
```powershell
# 1. Install Python 3.11 (ensure "Add to PATH" is checked)
# Download from: https://www.python.org/downloads/

# 2. Install UV package manager
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 3. Clone repository
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# 4. Setup environment
uv sync --all-extras

# 5. Configure environment
copy .env.example .env
# Edit .env with your API keys

# 6. Start dashboard
uv run streamlit run src/presentation/web/main.py
```

#### Windows Offline Package Generation

**For Air-Gapped Environments:**

##### Complete Process Overview

1. **Preparation Phase** (Internet-connected PC)
2. **Package Generation** (Internet-connected PC)
3. **File Transfer** (To air-gapped environment)
4. **Installation Phase** (Air-gapped PC)
5. **Verification & Execution** (Air-gapped PC)

##### Phase 1: Preparation (Internet-connected PC)

**Download Required Software:**
```powershell
# 1. Python 3.11.9 (required)
# https://www.python.org/downloads/release/python-3119/
# → python-3.11.9-amd64.exe (30MB)

# 2. Visual C++ Redistributable (required)
# https://aka.ms/vs/17/release/vc_redist.x64.exe
# → vc_redist.x64.exe (14MB)

# 3. Git for Windows (for source code)
# https://git-scm.com/download/win
```

**Clone RAGTrace Repository:**
```bash
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace
git pull origin main
```

##### Phase 2: Package Generation (Internet-connected PC)

**Generate Offline Package:**
```powershell
# Run PowerShell as Administrator

# Navigate to RAGTrace directory
cd C:\Users\[username]\RAGTrace

# Verify Python and UV installation
python --version  # Should show Python 3.11.x
uv --version      # UV package manager

# Create offline package
.\create-windows-offline-safe.ps1

# Duration: 15-45 minutes (depends on internet speed)
```

**Generated Package Structure:**
```
RAGTrace-Windows-Offline/
├── 01_Prerequisites/          # Python installers (manual addition required)
│   ├── README.txt            # Instructions for required files
│   ├── python-3.11.9-amd64.exe  # Add manually
│   └── vc_redist.x64.exe        # Add manually
├── 02_Dependencies/           # Python packages
│   ├── wheels/               # 200+ .whl files
│   ├── requirements.txt      # Dependency list
│   └── checksums.txt        # Integrity verification
├── 03_Source/                # Complete RAGTrace source
│   ├── src/                  # Main source code
│   ├── data/                 # Sample datasets
│   ├── cli.py               # CLI entry point
│   ├── .env.example         # Environment template
│   └── models/              # Create for BGE-M3 (optional)
├── 04_Scripts/               # Installation scripts
│   ├── install.bat          # Offline installation script
│   ├── run-web.bat          # Web dashboard launcher
│   ├── run-cli.bat          # CLI launcher
│   ├── verify.bat           # Verification launcher
│   └── verify.py            # Installation validator
└── README-안전설치가이드.txt    # Korean setup guide
```

##### Phase 3: File Transfer

**Files to Transfer to Air-gapped PC:**
1. `RAGTrace-Windows-Offline.zip` (generated package)
2. `python-3.11.9-amd64.exe` (Python installer)
3. `vc_redist.x64.exe` (VC++ redistributable)
4. BGE-M3 model folder (if using local embeddings, ~2GB)

**Prepare on Air-gapped PC:**
```powershell
# Create working directory
mkdir C:\RAGTrace-Install
cd C:\RAGTrace-Install

# Extract package
# Extract RAGTrace-Windows-Offline.zip here

# Copy prerequisites
# Copy python-3.11.9-amd64.exe → 01_Prerequisites/
# Copy vc_redist.x64.exe → 01_Prerequisites/
```

##### Phase 4: Installation (Air-gapped PC)

**Step 1: Install Python 3.11**
```powershell
cd 01_Prerequisites
.\python-3.11.9-amd64.exe

# Installation options:
# ✅ "Add Python 3.11 to PATH" - MUST CHECK
# ✅ "Install for all users" - Recommended
# Restart recommended after installation
```

**Step 2: Install Visual C++ Redistributable**
```powershell
.\vc_redist.x64.exe
# Use default settings
```

**Step 3: Install RAGTrace**
```powershell
# Run PowerShell as Administrator
cd C:\RAGTrace-Install\RAGTrace-Windows-Offline

# Execute installation script
.\04_Scripts\install.bat

# Installation process:
# - Creates Python virtual environment
# - Installs offline packages (10-30 minutes)
# - Shows completion message
```

**Step 4: Configure BGE-M3 Model (Optional)**
```powershell
# If using BGE-M3 local embeddings
# Create model directory
mkdir 03_Source\models

# Copy BGE-M3 model files
xcopy /E /I [BGE-M3_source_path] 03_Source\models\bge-m3

# Verify model files
dir 03_Source\models\bge-m3
```

**Step 5: Configure Environment**
```powershell
cd 03_Source

# Create .env from template
copy .env.example .env

# Edit configuration
notepad .env
```

**Example .env Configuration:**
```ini
# Google Gemini API Key (required)
GEMINI_API_KEY=your_gemini_api_key_here

# Naver HCX API Key (optional)
CLOVA_STUDIO_API_KEY=your_hcx_key_here

# BGE-M3 Local Model Path (if using local embeddings)
BGE_M3_MODEL_PATH="./models/bge-m3"

# Default Settings
DEFAULT_LLM="gemini"
DEFAULT_EMBEDDING="bge_m3"  # or "gemini" for online embeddings
```

##### Phase 5: Verification & Execution

**Verify Installation:**
```powershell
# Run verification script
.\04_Scripts\verify.bat

# Expected output:
# ✅ Python version OK
# ✅ Virtual environment activated
# ✅ Core packages installed
# ✅ PyTorch CPU only
# ✅ .env file exists
# ✅ Data files found
```

**Test BGE-M3 Model (if installed):**
```powershell
cd 03_Source
.venv\Scripts\activate
python

# In Python shell:
>>> from pathlib import Path
>>> bge_path = Path("./models/bge-m3")
>>> print(f"BGE-M3 exists: {bge_path.exists()}")
>>> print(f"Model files: {list(bge_path.glob('*'))[:5]}")
>>> exit()
```

**Launch RAGTrace:**
```powershell
# Web Dashboard (recommended)
.\04_Scripts\run-web.bat
# Access at: http://localhost:8501

# CLI Mode
.\04_Scripts\run-cli.bat
# Example: python cli.py evaluate evaluation_data --llm gemini --embedding bge_m3
```

##### Common Issues & Solutions

**Python PATH Issues:**
```powershell
# Add Python to PATH manually
set PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts

# Or add to system environment variables permanently
```

**Virtual Environment Activation:**
```powershell
# If activation fails
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Manual activation
cd 03_Source
.venv\Scripts\activate.bat
```

**BGE-M3 Path Issues:**
```powershell
# Use absolute path in .env if relative path fails
BGE_M3_MODEL_PATH="C:\RAGTrace-Install\RAGTrace-Windows-Offline\03_Source\models\bge-m3"
```

**Package Installation Failures:**
```powershell
# Manual package installation
cd 03_Source
.venv\Scripts\activate
pip install --no-index --find-links ..\02_Dependencies\wheels [package_name]

# Complete reinstallation
pip install --no-index --find-links ..\02_Dependencies\wheels -r ..\02_Dependencies\requirements.txt --force-reinstall
```

### 4. 🏭 Enterprise Offline Deployment

#### Enterprise Package System Features

**Security & Integrity:**
- SHA-256 checksum verification
- Vulnerability scanning with Safety
- Digital signature validation
- Minimal privilege requirements

**Cross-Platform Support:**
- Windows (x64)
- Linux (x64, ARM64)
- macOS (Intel, Apple Silicon)
- Platform-specific optimizations

**Enterprise Features:**
- Automated dependency resolution
- Rollback and recovery systems
- Comprehensive validation
- Performance benchmarking
- Centralized logging

#### Creating Enterprise Packages

**Generate Enterprise Package:**
```bash
# Full enterprise package with all features
python scripts/offline-packaging/create-enterprise-offline.py \
  --project-root . \
  --output-dir ./packages \
  --include-security-scan \
  --generate-manifest

# Quick enterprise package
python scripts/offline-packaging/create-enterprise-offline.py --quick
```

**Package Contents:**
```
RAGTrace-Enterprise-[platform]-[arch].tar.gz
├── 01_Prerequisites/          # System requirements
├── 02_Dependencies/
│   ├── wheels/               # Platform-specific wheels
│   ├── requirements-*.txt    # Environment-specific deps
│   └── checksums.sha256     # Security verification
├── 03_Source/               # RAGTrace source code
├── 04_Scripts/
│   ├── install.py          # Universal installer
│   ├── install.bat/.sh     # Platform wrappers
│   └── enterprise-validator.py # Comprehensive validator
├── 05_Documentation/        # Complete guides
├── 06_Verification/         # Validation tools
├── 07_Models/              # BGE-M3 Local Embedding Models
│   └── bge-m3/            # Complete offline embedding (~2GB)
│       ├── config.json
│       ├── pytorch_model.bin
│       ├── tokenizer.json
│       └── (other model files)
└── MANIFEST.json           # Package metadata
```

#### Enterprise Installation Process

**Phase 1: Pre-Installation Validation**
```bash
# Comprehensive system check
python enterprise-validator.py

# Generate diagnostic report
python enterprise-validator.py --output system_report.json
```

**Phase 2: Installation**
```bash
# Extract package
tar -xzf RAGTrace-Enterprise-*.tar.gz
cd RAGTrace-Enterprise-Offline

# Install with validation
python 04_Scripts/install.py --validate --backup

# Platform-specific installation
# Windows: 04_Scripts\install.bat
# Unix: bash 04_Scripts/install.sh
```

**Phase 3: Post-Installation Verification**
```bash
# Complete validation
python enterprise-validator.py

# Performance benchmarking
python enterprise-validator.py --benchmark

# Generate compliance report
python enterprise-validator.py --compliance-report
```

## 🤖 BGE-M3 Local Embedding Setup

### Automatic Model Download (Internet Required)

BGE-M3 models are automatically downloaded when first needed:

```bash
# Automatic download during first use
uv run python hello.py --prepare-models

# Force re-download if needed
uv run python hello.py --prepare-models --force-download
```

### Manual Model Setup for Offline Environments

For air-gapped or offline environments, BGE-M3 model files must be pre-installed:

**1. Download Model Files (on internet-connected machine):**
```bash
# Download and save BGE-M3 model
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')
model.save('./models/bge-m3')
print('BGE-M3 model downloaded to ./models/bge-m3')
"
```

**2. Model Directory Structure:**
```
models/bge-m3/
├── config.json              # Model configuration
├── pytorch_model.bin        # Model weights (~2GB)
├── tokenizer.json          # Tokenizer
├── tokenizer_config.json   # Tokenizer configuration
├── special_tokens_map.json # Special tokens
└── vocab.txt              # Vocabulary
```

**3. Environment Configuration:**
```bash
# Configure .env for local BGE-M3
BGE_M3_MODEL_PATH="./models/bge-m3"
DEFAULT_EMBEDDING="bge_m3"
```

**4. Verification:**
```bash
# Test BGE-M3 functionality
uv run python -c "
from src.infrastructure.embedding.bge_m3_adapter import BGEm3EmbeddingAdapter
adapter = BGEm3EmbeddingAdapter('./models/bge-m3')
print('✅ BGE-M3 model loaded successfully')
"
```

### Performance Optimization

**Device Auto-Detection:**
- **CUDA**: GPU acceleration (~60 docs/sec)
- **MPS**: Apple Silicon optimization (~15 docs/sec)
- **CPU**: Multi-core processing (~40 docs/sec)

**Memory Requirements:**
- Model storage: ~2GB disk space
- Runtime memory: ~2-4GB RAM
- GPU memory: ~2GB VRAM (if using CUDA)

## 🔧 Environment Configuration

### Required API Keys

Create `.env` file:
```bash
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Naver Cloud CLOVA Studio API Key (for HCX-005)
CLOVA_STUDIO_API_KEY=your_clova_studio_api_key_here

# Optional: Model overrides
DEFAULT_LLM=gemini          # or "hcx"
DEFAULT_EMBEDDING=bge_m3    # or "gemini", "hcx"

# BGE-M3 Local Embedding Configuration
BGE_M3_MODEL_PATH="./models/bge-m3"  # Path to BGE-M3 model files
BGE_M3_DEVICE="auto"                  # auto, cpu, cuda, mps

# Note: For offline environments, ensure BGE-M3 model files
# are included in the models/ directory before deployment
```

### System Requirements

**Minimum Requirements:**
- Python 3.11+
- 4GB RAM
- 2GB disk space
- Internet connection (for initial setup)

**Recommended Requirements:**
- Python 3.11+
- 8GB RAM
- 10GB disk space
- SSD storage
- GPU (CUDA/MPS) for BGE-M3 optimization

**Enterprise Requirements:**
- Python 3.11+
- 16GB RAM
- 50GB disk space (includes BGE-M3 model storage)
- Dedicated GPU (recommended for BGE-M3 acceleration)
- Network isolation capability
- BGE-M3 model files in models/ directory for offline deployment

## 🚨 Troubleshooting

### Common Installation Issues

#### Python Version Problems
```bash
# Check Python version
python --version

# Install specific version (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip

# macOS with Homebrew
brew install python@3.11
```

#### Package Installation Failures
```bash
# Clear UV cache
uv cache clean

# Reinstall with verbose output
uv sync --all-extras --verbose

# Manual dependency installation
uv pip install dependency-injector ragas streamlit plotly
```

#### Windows-Specific Issues

**PowerShell Execution Policy:**
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Python PATH Issues:**
```cmd
# Add Python to PATH manually
set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311
```

**Permission Errors:**
```powershell
# Run as administrator
Right-click PowerShell → "Run as administrator"
```

#### Memory Issues
```bash
# Reduce memory usage during installation
UV_CACHE_SIZE=1GB uv sync --all-extras

# Use pip with memory optimization
pip install --no-cache-dir -r requirements.txt
```

#### Network/Proxy Issues
```bash
# Configure proxy for UV
export UV_HTTP_PROXY=http://proxy.company.com:8080
export UV_HTTPS_PROXY=http://proxy.company.com:8080

# Configure proxy for pip
pip install --proxy http://proxy.company.com:8080 package_name
```

### Platform-Specific Troubleshooting

#### macOS Issues
```bash
# Install Xcode command line tools
xcode-select --install

# Fix OpenMP issues
brew install libomp

# Apple Silicon specific
arch -arm64 uv sync --all-extras
```

#### Linux Issues
```bash
# Install build dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install build-essential python3-dev libffi-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel libffi-devel
```

### Advanced Troubleshooting

**Diagnostic Commands:**
```bash
# Test basic connectivity
uv run python hello.py

# Validate container configuration
uv run python -c "from src.container import container; print('Container OK')"

# Check available datasets
uv run python cli.py list-datasets

# Test LLM adapters
uv run python cli.py evaluate evaluation_data --llm gemini --verbose
```

**Log Analysis:**
```bash
# Enable debug logging
export RAGTRACE_LOG_LEVEL=DEBUG

# Check logs
tail -f logs/ragtrace.log

# Windows log location
type %USERPROFILE%\.ragtrace\logs\ragtrace.log
```

## ✅ Verification

### Installation Verification

**Basic Verification:**
```bash
# Test CLI
uv run python cli.py --help

# Test web dashboard
uv run streamlit run src/presentation/web/main.py &
curl http://localhost:8501

# Test evaluation
uv run python cli.py evaluate evaluation_data --llm gemini
```

**Comprehensive Verification:**
```bash
# Run all tests
uv run pytest tests/

# Performance benchmark
uv run python scripts/benchmark.py

# Memory usage test
uv run python scripts/memory_test.py
```

### Enterprise Verification

**Security Validation:**
```bash
# Security scan
python enterprise-validator.py --security-scan

# Compliance check
python enterprise-validator.py --compliance

# Vulnerability assessment
python enterprise-validator.py --vulnerability-scan
```

**Performance Validation:**
```bash
# System performance
python enterprise-validator.py --benchmark

# Load testing
python enterprise-validator.py --load-test

# Resource monitoring
python enterprise-validator.py --monitor
```

## 🎯 Next Steps

### After Installation

1. **Configure API Keys** - Set up Gemini and optionally HCX API keys
2. **Test Evaluation** - Run sample evaluation to verify setup
3. **Import Data** - Use Excel/CSV import features for your data
4. **Explore Dashboard** - Familiarize yourself with web interface
5. **Read Documentation** - Review user guides and metrics explanation

### Production Deployment

1. **Security Review** - Validate API key security and access controls
2. **Performance Tuning** - Optimize for your hardware and data volumes
3. **Monitoring Setup** - Configure logging and performance monitoring
4. **Backup Strategy** - Plan for data backup and disaster recovery
5. **User Training** - Train team members on RAGTrace usage

### Development Setup

1. **Development Environment** - Set up with development extras
2. **Code Quality Tools** - Configure linting, formatting, and testing
3. **Debugging Setup** - Enable debug logging and development tools
4. **Contribution Guidelines** - Review if planning to contribute
5. **Architecture Study** - Understand Clean Architecture implementation

---

For specific issues not covered here, refer to:
- **Windows Issues**: [Windows Troubleshooting Guide](Windows_Troubleshooting_Guide.md)
- **Docker Issues**: [Docker Deployment Guide](Docker_Deployment_Guide.md)
- **Development**: [Architecture and Development Guide](ARCHITECTURE_AND_DEVELOPMENT.md)
- **Data Import**: [Data Import Guide](Data_Import_Guide.md)