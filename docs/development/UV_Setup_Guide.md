# UV Setup Guide for RAGTrace

This document provides detailed setup instructions for RAGTrace using UV package manager.

## Prerequisites

- Python 3.11+ 
- UV package manager

## Install UV

If you don't have UV installed:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell  
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip
pip install uv

# Using Homebrew (macOS)
brew install uv
```

## Quick Setup

### Option 1: Automated Setup Script

```bash
# Make the script executable and run it
chmod +x uv-setup.sh
./uv-setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
uv venv --python 3.11

# 2. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# 3. Install all dependencies
uv sync --all-extras

# 4. Create .env file
cp .env.example .env  # Edit with your API keys
```

## UV Commands Reference

### Environment Management
```bash
# Create virtual environment
uv venv --python 3.11

# Sync dependencies from pyproject.toml
uv sync

# Install with extras
uv sync --extra dev
uv sync --extra performance  
uv sync --all-extras

# Install in production mode (no dev dependencies)
uv sync --no-dev
```

### Running Applications
```bash
# Run with uv (automatically activates venv)
uv run streamlit run src/presentation/web/main.py
uv run python cli.py evaluate evaluation_data
uv run python hello.py

# Direct script execution
uv run ragtrace-dashboard  # Custom script entry point
uv run ragtrace evaluate evaluation_data  # CLI entry point
```

### Development Commands
```bash
# Install development dependencies
uv add --dev pytest black ruff mypy

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Lint code  
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

### Dependency Management
```bash
# Add new dependency
uv add numpy pandas

# Add development dependency
uv add --dev pytest

# Add optional dependency
uv add --optional analysis matplotlib

# Update dependencies
uv lock --upgrade

# Remove dependency
uv remove numpy

# Show dependency tree
uv tree

# Export requirements
uv export > requirements.txt
```

## Project Structure with UV

```
RAGTrace/
├── pyproject.toml       # Project metadata and dependencies
├── uv.toml             # UV-specific configuration
├── uv.lock             # Locked dependency versions
├── .python-version     # Python version specification
├── uv-setup.sh         # Automated setup script
├── justfile            # Task runner with UV commands
└── src/                # Source code
```

## Configuration Files

### pyproject.toml
- Project metadata
- Dependencies and optional dependencies
- Tool configurations (black, ruff, mypy)
- UV-specific settings in `[tool.uv]` section

### uv.toml  
- Global UV configuration
- Cache settings
- Resolution strategy
- Index URLs

### uv.lock
- Locked dependency versions
- Automatically generated and updated
- Should be committed to version control

## Extras Available

- `dev`: Development tools (pytest, black, ruff, mypy)
- `performance`: Performance monitoring (watchdog)
- `analysis`: Data analysis tools (jupyter, matplotlib, seaborn)

Install specific extras:
```bash
uv sync --extra dev
uv sync --extra performance
uv sync --extra analysis
uv sync --all-extras  # Install all
```

## Environment Variables

Create a `.env` file with:
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional  
CLOVA_STUDIO_API_KEY=your_clova_studio_api_key_here
DEFAULT_LLM=gemini

# Model Configuration
GEMINI_MODEL_NAME=models/gemini-2.5-flash-preview-05-20
GEMINI_EMBEDDING_MODEL_NAME=models/gemini-embedding-exp-03-07
HCX_MODEL_NAME=HCX-005
```

## Troubleshooting

### Common Issues

1. **UV not found**
   ```bash
   # Reload shell after installation
   source ~/.bashrc  # or ~/.zshrc
   ```

2. **Python version issues**
   ```bash
   # Install specific Python version with UV
   uv python install 3.11
   uv venv --python 3.11
   ```

3. **Lock file conflicts**
   ```bash
   # Regenerate lock file
   rm uv.lock
   uv lock
   ```

4. **Cache issues**
   ```bash
   # Clear UV cache
   uv cache clean
   ```

### Performance Tips

- Use `uv run` instead of activating venv manually
- Keep `uv.lock` in version control for reproducible builds
- Use `--no-dev` for production installations
- Enable compile-bytecode for faster imports (set in uv.toml)

## Integration with IDEs

### VS Code
Install the Python extension and set the interpreter to `.venv/bin/python`

### PyCharm  
Point the project interpreter to `.venv/bin/python`

### Vim/Neovim
Use plugins like `vim-python-pep8-indent` and point to `.venv/bin/python`

## Comparison with Other Tools

| Feature | UV | pip | poetry | pipenv |
|---------|----|----|--------|--------|
| Speed | ⚡⚡⚡ | ⚡ | ⚡⚡ | ⚡ |
| Dependency Resolution | ✅ | ❌ | ✅ | ✅ |
| Lock Files | ✅ | ❌ | ✅ | ✅ |
| Virtual Environments | ✅ | ❌ | ✅ | ✅ |
| Python Installation | ✅ | ❌ | ❌ | ❌ |

## Migration from Other Tools

### From pip
```bash
# Convert requirements.txt
uv add $(cat requirements.txt)
```

### From poetry
```bash
# UV can read pyproject.toml directly
uv sync
```

### From pipenv
```bash  
# Convert Pipfile
uv add $(pipenv requirements)
```