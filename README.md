# 🔍 RAGTrace
**RAG(Retrieval-Augmented Generation) 시스템의 성능 추적, 평가, 분석을 위한 종합 트레이싱 솔루션**

ExplodingGradients의 RAGAS 프레임워크를 기반으로 하여 RAG 시스템의 
Faithfulness, Answer Relevancy, Context Precision, Context Recall을 측정하고, 
직관적인 웹 대시보드로 성능을 추적 및 분석합니다.

## ✨ Features

- **📊 Interactive Dashboard**: Streamlit 기반의 대화형 대시보드 제공
- **📈 RAGAS Metrics Evaluation**: `faithfulness`, `answer_relevancy`, `context_recall`, `context_precision` 등 핵심 RAGAS 메트릭 평가
- **🔍 Detailed Analysis**: 평가 결과에 대한 상세 분석 및 시각화
- **📄 Various Data Formats**: JSON, CSV, Excel 등 다양한 형식의 데이터 로드 지원
- **🐳 Docker Support**: Docker를 통한 간편한 배포 및 실행 환경 제공

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ntts9990/RAGTrace.git
   cd RAGTrace
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

## 🖥️ Usage

Streamlit 대시보드를 실행하려면 다음 명령어를 사용하세요:

```bash
streamlit run src/presentation/web/main.py
```

## 🐳 Docker

Docker를 사용하여 프로젝트를 실행할 수도 있습니다.

```bash
docker-compose up --build
```

## 📁 Project Structure

```
RAGTrace/
├── .github/                # GitHub Actions Workflows
├── .vscode/                # VSCode settings
├── data/                   # Evaluation data
├── docs/                   # Project documentation
├── scripts/                # Utility scripts
├── src/                    # Source code
│   ├── application/        # Application logic
│   ├── domain/             # Core domain models
│   ├── infrastructure/     # Data sources, external services
│   └── presentation/       # UI layer (Streamlit)
├── tests/                  # Tests
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── pyproject.toml
└── README.md
```

## 🙏 Acknowledgements

This project is based on the [Ragas](https://github.com/explodinggradients/ragas) framework. 