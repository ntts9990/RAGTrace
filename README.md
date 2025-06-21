# 🔍 RAGTrace

**CLI 기반의 RAG(Retrieval-Augmented Generation) 시스템 성능 평가 및 분석 도구**

RAG 시스템의 핵심 품질 지표를 신뢰성 있게 평가하고 분석하기 위한 커맨드 라인 인터페이스(CLI) 애플리케이션입니다. [Ragas](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 하며, 안정적인 평가를 위한 다양한 기능들을 포함하고 있습니다.

## ✨ 주요 기능 (Key Features)

-   **📊 핵심 RAG 지표 평가**: `Faithfulness`, `Answer Relevancy`, `Context Precision`, `Context Recall` 등 Ragas의 핵심 지표를 측정합니다.
-   **🔎 데이터 사전 검증 (Pre-flight Check)**: 평가 시작 전, 데이터의 누락된 필드나 짧은 콘텐츠 등 품질 문제를 미리 검사하여 "Garbage In, Garbage Out"을 방지합니다.
-   **🛡️ 견고한 API 오류 처리**: 외부 LLM API 호출 실패 시, 전체 프로세스를 중단하는 대신 실패를 기록하고 부분적인 성공을 허용하여 평가의 안정성을 높입니다.
-   **🔧 유연한 아키텍처**: 'Ports and Adapters' 아키텍처를 채택하여, Gemini 외 다른 LLM으로 쉽게 교체하거나 확장할 수 있습니다.
-   **⚙️ 환경 변수 기반 설정**: `.env` 파일을 통해 API 키, 모델명 등을 안전하고 편리하게 관리할 수 있습니다.
-   **📄 다양한 데이터 포맷 지원**: `JSON` 및 `CSV` 형식의 평가 데이터셋을 지원합니다.

## 🚀 시작하기 (Getting Started)

### 사전 준비

-   Python 3.11+
-   `uv` (권장) 또는 `pip`

### 설치

1.  **리포지토리 클론:**
    ```bash
    git clone https://github.com/your-username/RAGTrace.git
    cd RAGTrace
    ```

2.  **가상 환경 생성 및 의존성 설치:**
    ```bash
    # uv 사용 시 (권장)
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt

    # pip 사용 시
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

### 환경 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, 아래와 같이 필요한 환경 변수를 설정합니다.

```env
# .env 파일 예시
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GEMINI_MODEL_NAME="gemini-1.5-flash-latest"
GEMINI_EMBEDDING_MODEL_NAME="models/embedding-001"
GEMINI_REQUESTS_PER_MINUTE=60
EMBEDDING_REQUESTS_PER_MINUTE=60
```

## 🖥️ 사용법 (Usage)

다음 명령어를 사용하여 평가를 실행합니다. `dataset_name`은 `data/` 폴더 내에 있는 파일명(확장자 제외)입니다.

```bash
python -m src.main --dataset_name [your_dataset_name]
```

**예시:** `data/ragas_test.json` 파일로 평가를 실행하려면

```bash
python -m src.main --dataset_name ragas_test
```

`--prompt_type` 인자를 사용하여 특정 프롬프트 템플릿으로 평가를 실행할 수도 있습니다.

```bash
python -m src.main --dataset_name ragas_test --prompt_type simple
```


## 📁 프로젝트 구조 (Project Structure)

```
RAGTrace/
├── data/                   # 평가 데이터셋 (JSON, CSV)
├── docs/                   # 프로젝트 문서
├── src/                    # 소스 코드
│   ├── application/        # 애플리케이션 서비스 및 유스케이스 (Ports 포함)
│   │   ├── ports/
│   │   ├── services/
│   │   └── use_cases/
│   ├── domain/             # 핵심 도메인 모델 (Entities, Exceptions)
│   ├── infrastructure/     # 외부 시스템 연동 (Adapters: LLM, Repository)
│   ├── factories/          # 객체 생성 로직
│   ├── __init__.py
│   ├── config.py           # 환경 변수 및 설정 관리
│   ├── container.py        # 의존성 주입 컨테이너
│   └── main.py             # 애플리케이션 실행 진입점 (CLI)
├── .env.example            # .env 파일 템플릿
├── .gitignore
├── requirements.txt        # Python 의존성
└── README.md
```

## 🙏 Special Thanks

이 프로젝트는 [Ragas](https://github.com/explodinggradients/ragas) 프레임워크에 기반을 두고 있습니다. 