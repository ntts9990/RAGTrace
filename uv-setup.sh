#!/bin/bash
# RAGTrace UV Environment Setup Script

set -e

echo "🔍 RAGTrace - UV Environment Setup"
echo "=================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv is installed: $(uv --version)"

# Check Python version
echo "🐍 Checking Python version..."
if ! python3.11 --version &> /dev/null; then
    echo "⚠️  Python 3.11 not found. Installing with uv..."
    uv python install 3.11
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
uv venv --python 3.11

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
uv pip install -e .

# Install development dependencies
echo "🛠️  Installing development dependencies..."
uv pip install -e .[dev]

# Install performance dependencies (optional)
echo "⚡ Installing performance dependencies..."
uv pip install -e .[performance]

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file template..."
    cat > .env << 'EOF'
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Naver CLOVA Studio API Key (for HCX models)
CLOVA_STUDIO_API_KEY=your_clova_studio_api_key_here

# Optional: Default LLM selection
DEFAULT_LLM=gemini

# Model Configuration
GEMINI_MODEL_NAME=models/gemini-2.5-flash-preview-05-20
GEMINI_EMBEDDING_MODEL_NAME=models/gemini-embedding-exp-03-07
HCX_MODEL_NAME=HCX-005
EOF
    echo "📝 .env file created. Please update with your API keys."
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Test the installation:"
echo "   uv run python hello.py"
echo "3. Start the dashboard:"
echo "   uv run streamlit run src/presentation/web/main.py"
echo "4. Or run CLI evaluation:"
echo "   uv run python cli.py evaluate evaluation_data"
echo ""
echo "For more information, see README.md"