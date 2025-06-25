# RAGTrace Troubleshooting Guide

## 🎯 Overview

Comprehensive troubleshooting guide for common issues encountered during RAGTrace installation, configuration, and operation across different platforms and environments.

## 📋 Quick Diagnostic Commands

Before diving into specific issues, run these commands to gather system information:

```bash
# Check system status
uv run python hello.py

# Validate container configuration
uv run python -c "from src.container import container; print('✅ Container OK')"

# Check available datasets
uv run python cli.py list-datasets

# Test LLM connectivity
uv run python cli.py evaluate evaluation_data --llm gemini --verbose
```

## 🚨 Installation Issues

### Python Version Problems

#### Issue: Wrong Python Version
```bash
# Check Python version
python --version
```

**Solutions:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.11
brew link python@3.11

# Update PATH
echo 'export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
```

**Windows:**
1. Download Python 3.11 from https://python.org
2. **IMPORTANT**: Check "Add Python to PATH" during installation
3. Restart command prompt after installation

#### Issue: Multiple Python Versions Conflict
```bash
# Check all Python installations
ls -la /usr/bin/python*

# Use specific Python version
python3.11 -m pip install uv
python3.11 -m venv ragtrace-env
```

### UV Package Manager Issues

#### Issue: UV Not Found
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Restart shell after installation
source ~/.bashrc  # Linux/macOS
```

#### Issue: UV Cache Problems
```bash
# Clear UV cache
uv cache clean

# Reset UV completely
rm -rf ~/.cache/uv
uv sync --all-extras
```

#### Issue: UV Lock File Conflicts
```bash
# Remove lock file and regenerate
rm uv.lock
uv lock
uv sync --all-extras
```

### Dependency Installation Issues

#### Issue: Package Installation Failures
```bash
# Verbose installation to see detailed errors
uv sync --all-extras --verbose

# Manual installation with error details
uv pip install dependency-injector --verbose

# Use pip as fallback
pip install -r requirements.txt
```

#### Issue: Build Tools Missing (Linux)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential python3-dev libffi-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel libffi-devel

# Alpine Linux
apk add build-base python3-dev libffi-dev
```

#### Issue: Missing System Libraries
```bash
# Ubuntu/Debian - common dependencies
sudo apt install libssl-dev libcurl4-openssl-dev libxml2-dev libxslt1-dev

# macOS - Xcode command line tools
xcode-select --install

# macOS - OpenMP for ML libraries
brew install libomp
```

## 💻 Windows-Specific Issues

### PowerShell Execution Policy

#### Issue: Script Execution Blocked
```powershell
# Error: "execution of scripts is disabled on this system"
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# For single session
Set-ExecutionPolicy Bypass -Scope Process -Force
```

### Python PATH Issues

#### Issue: Python Command Not Found
```cmd
# Check if Python is in PATH
where python

# Add Python to PATH manually
set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311
set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\Scripts

# Make permanent via System Properties → Advanced → Environment Variables
```

### Visual C++ Requirements

#### Issue: Microsoft Visual C++ 14.0 Required
**Solutions:**
1. **Install Visual C++ Redistributable (Quick)**
   - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
   
2. **Install Build Tools (Complete)**
   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Select "C++ build tools" workload

### Windows Permissions

#### Issue: Access Denied Errors
```powershell
# Run PowerShell as Administrator
# Right-click PowerShell → "Run as administrator"

# Check current user permissions
whoami /priv

# Create directory with proper permissions
mkdir C:\RAGTrace
icacls C:\RAGTrace /grant "%USERNAME%:(OI)(CI)F"
```

### Network and Proxy Issues

#### Issue: Corporate Firewall/Proxy
```cmd
# Configure pip proxy
pip install --proxy http://proxy.company.com:8080 --trusted-host pypi.org package_name

# Configure UV proxy
set UV_HTTP_PROXY=http://proxy.company.com:8080
set UV_HTTPS_PROXY=http://proxy.company.com:8080

# Bypass SSL verification (if necessary)
pip install --trusted-host pypi.org --trusted-host pypi.python.org package_name
```

### Memory Issues

#### Issue: Out of Memory During Installation
```cmd
# Reduce memory usage
pip install --no-cache-dir package_name

# Install packages one by one
for /f %i in (requirements.txt) do pip install --no-cache-dir "%i"
```

## 🐳 Docker Issues

### Docker Installation Problems

#### Issue: Docker Daemon Not Running
```bash
# Start Docker daemon
sudo systemctl start docker

# Enable auto-start
sudo systemctl enable docker

# macOS - start Docker Desktop
open /Applications/Docker.app
```

#### Issue: Permission Denied
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker run hello-world
```

### Container Build Failures

#### Issue: Build Context Too Large
```bash
# Add .dockerignore file
echo "*.log" >> .dockerignore
echo "node_modules" >> .dockerignore
echo "__pycache__" >> .dockerignore
echo "*.pyc" >> .dockerignore

# Build with specific context
docker build --no-cache -t ragtrace .
```

#### Issue: Layer Caching Problems
```bash
# Force rebuild without cache
docker build --no-cache -t ragtrace .

# Clean up Docker system
docker system prune -a
```

### Runtime Issues

#### Issue: Container Memory Limits
```bash
# Increase memory limit
docker run --memory="8g" ragtrace

# Check container resource usage
docker stats
```

#### Issue: Port Conflicts
```bash
# Check what's using port 8501
netstat -tulpn | grep 8501
lsof -i :8501

# Use different port
docker run -p 8502:8501 ragtrace
```

## 🤖 LLM and API Issues

### API Key Problems

#### Issue: Invalid API Keys
```bash
# Verify API key format
echo $GEMINI_API_KEY | wc -c

# Test API connectivity
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     https://generativelanguage.googleapis.com/v1/models
```

#### Issue: API Key Not Found
```bash
# Check environment variables
env | grep API_KEY

# Verify .env file location and format
cat .env
ls -la .env

# Source .env manually
export $(grep -v '^#' .env | xargs)
```

### Network Connectivity

#### Issue: Timeout Errors
```bash
# Test basic connectivity
ping google.com
curl -I https://generativelanguage.googleapis.com

# Configure longer timeouts
export RAGTRACE_TIMEOUT=600
```

#### Issue: SSL Certificate Problems
```bash
# Update certificates
sudo apt update && sudo apt install ca-certificates

# macOS
brew install ca-certificates
```

### Rate Limiting

#### Issue: API Rate Limits Exceeded
```python
# Configure rate limiting in code
import time

class RateLimitedLLMAdapter:
    def __init__(self, base_adapter, requests_per_minute=60):
        self.base_adapter = base_adapter
        self.min_interval = 60.0 / requests_per_minute
        self.last_request = 0
    
    def generate_answer(self, question, contexts):
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        self.last_request = time.time()
        return self.base_adapter.generate_answer(question, contexts)
```

## 📊 Evaluation and Runtime Issues

### Memory Problems

#### Issue: Out of Memory During Evaluation
```python
# Reduce batch size in evaluation
# src/config.py
BATCH_SIZE = 5  # Reduce from default 10

# Clear memory between evaluations
import gc
gc.collect()
```

#### Issue: Large Dataset Handling
```python
# Process datasets in chunks
def evaluate_in_chunks(dataset, chunk_size=10):
    results = []
    for i in range(0, len(dataset), chunk_size):
        chunk = dataset[i:i + chunk_size]
        result = evaluate_chunk(chunk)
        results.append(result)
        gc.collect()  # Clear memory
    return combine_results(results)
```

### Performance Issues

#### Issue: Slow Evaluation
```bash
# Enable performance monitoring
export RAGTRACE_PROFILE=true

# Use faster embedding models
export DEFAULT_EMBEDDING=bge_m3  # Instead of api-based
```

#### Issue: GPU Not Utilized
```python
# Check GPU availability
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA devices: {torch.cuda.device_count()}")

# Force GPU usage for BGE-M3
export BGE_M3_DEVICE=cuda
```

### Data Import Issues

#### Issue: File Format Problems
```python
# Check file encoding
file -bi filename.csv
chardet filename.csv

# Convert encoding if needed
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
```

#### Issue: Large File Processing
```python
# Process large files in chunks
import pandas as pd

def process_large_csv(filename, chunk_size=1000):
    for chunk in pd.read_csv(filename, chunksize=chunk_size):
        process_chunk(chunk)
```

## 🔧 Advanced Troubleshooting

### Debug Mode

#### Enable Comprehensive Logging
```bash
# Set debug logging
export RAGTRACE_LOG_LEVEL=DEBUG
export RAGTRACE_DEBUG=true

# Run with verbose output
uv run python cli.py evaluate dataset --verbose
```

#### Memory Profiling
```python
# Install memory profiler
uv pip install memory-profiler

# Profile memory usage
@profile
def evaluate_dataset(dataset_name):
    # Your evaluation code here
    pass

# Run with profiler
python -m memory_profiler cli.py evaluate dataset
```

#### Performance Profiling
```bash
# CPU profiling
uv run python -m cProfile -o profile.stats cli.py evaluate dataset

# Analyze profile
uv run python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

### Container Debugging

#### Issue: Dependency Injection Problems
```python
# Debug container setup
def debug_container():
    from src.container import container
    
    try:
        # Test each component
        llm_provider = container.get_llm_provider("gemini")
        print("✅ LLM provider created")
        
        embedding_provider = container.get_embedding_provider("bge_m3")
        print("✅ Embedding provider created")
        
        use_case = container.get_evaluation_use_case("gemini")
        print("✅ Use case created")
        
    except Exception as e:
        print(f"❌ Container error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_container()
```

### System Diagnostics

#### Create Diagnostic Report
```python
import platform
import sys
import psutil
import subprocess

def create_diagnostic_report():
    report = {
        "system": {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
        },
        "resources": {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total // (1024**3),
            "disk_free": psutil.disk_usage("/").free // (1024**3),
        },
        "environment": {
            "path": os.environ.get("PATH"),
            "python_path": sys.path,
        }
    }
    
    # Check Python packages
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True)
        report["packages"] = result.stdout
    except Exception as e:
        report["packages_error"] = str(e)
    
    return report
```

## 🆘 Emergency Recovery

### Complete Reset
```bash
# Remove all caches and virtual environments
rm -rf ~/.cache/uv
rm -rf .venv
rm -rf __pycache__
rm -rf *.egg-info

# Clean reinstall
uv sync --all-extras
```

### Backup and Restore
```bash
# Backup working configuration
tar -czf ragtrace-backup.tar.gz .env src/ data/

# Restore from backup
tar -xzf ragtrace-backup.tar.gz
```

### Rollback Strategy
```bash
# Git-based rollback
git stash
git checkout HEAD~1  # Go back one commit
uv sync --all-extras

# Or reset to specific working commit
git reset --hard <commit-hash>
```

## 📞 Getting Help

### Information to Collect

When reporting issues, include:

1. **System Information**
   ```bash
   uv run python -c "
   import platform, sys
   print(f'OS: {platform.platform()}')
   print(f'Python: {sys.version}')
   print(f'Architecture: {platform.architecture()}')
   "
   ```

2. **Error Logs**
   ```bash
   # Enable debug logging and capture output
   export RAGTRACE_LOG_LEVEL=DEBUG
   uv run python cli.py evaluate dataset 2>&1 | tee error.log
   ```

3. **Environment Details**
   ```bash
   uv pip list > packages.txt
   env | grep -i ragtrace > environment.txt
   ```

4. **Configuration**
   ```bash
   # Sanitized config (remove API keys)
   cat .env | sed 's/=.*/=***/' > config.txt
   ```

### Support Channels

- **GitHub Issues**: [Create an issue](https://github.com/ntts9990/RAGTrace/issues)
- **Discussions**: [Community discussions](https://github.com/ntts9990/RAGTrace/discussions)
- **Documentation**: Check other guides in `docs/` folder

### Self-Help Checklist

Before seeking help:

- [ ] Check this troubleshooting guide
- [ ] Run diagnostic commands
- [ ] Search existing GitHub issues
- [ ] Try with debug logging enabled
- [ ] Test with minimal configuration
- [ ] Verify system requirements
- [ ] Check for updates

---

Most issues can be resolved by following this guide systematically. When in doubt, start with the basic diagnostic commands and work through the relevant sections based on your specific error messages.