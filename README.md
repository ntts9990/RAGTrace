# 🔍 RAGTrace

**Multi-LLM RAG 시스템 성능 평가 및 분석 플랫폼**

RAGTrace는 RAG(Retrieval-Augmented Generation) 시스템의 핵심 품질 지표를 신뢰성 있게 평가하고 분석하기 위한 종합 플랫폼입니다. [RAGAS](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 하며, Clean Architecture를 통해 확장 가능하고 유지보수성이 높은 구조를 제공합니다.

- 📖 **[통합 개발 가이드](docs/Development_Guide.md)에서 더 자세한 내용을 확인하세요.**

## ✨ 주요 기능

- **🤖 Multi-LLM & Multi-Embedding**: Gemini, HCX, BGE-M3 등 다양한 모델을 런타임에 선택하고 독립적으로 조합할 수 있습니다.
- **🔌 Port-Adapter 패턴**: 새로운 LLM, 임베딩 모델, 데이터 소스를 최소한의 코드로 쉽게 추가하고 교체할 수 있습니다.
- **🚀 로컬 환경 최적화**:
  - **BGE-M3 로컬 임베딩**: 인터넷 연결 없이 완전한 오프라인 임베딩 처리가 가능합니다.
  - **GPU 자동 최적화**: CUDA, MPS(Apple Silicon)를 자동 감지하여 최적의 성능을 제공합니다.
- **🌐 인터랙티브 웹 대시보드**: Streamlit 기반의 UI를 통해 평가 과정을 실시간으로 모니터링하고 결과를 심층 분석할 수 있습니다.
- **🛡️ 안정성 및 품질**: 데이터 사전 검증, 안정적인 HTTP 직접 호출, 상세한 오류 처리 및 90% 이상의 높은 테스트 커버리지를 통해 신뢰성을 확보합니다.

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.11+
- [UV](https://docs.astral.sh/uv/) 패키지 매니저
- API 키 (`.env` 파일에 설정)

### 설치 및 설정

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/RAGTrace.git
cd RAGTrace

# 2. (선택) 자동 설정 스크립트 실행
# 이 스크립트는 가상 환경 생성, 의존성 설치, .env 파일 복사를 한번에 수행합니다.
chmod +x uv-setup.sh
./uv-setup.sh

# 3. (수동 설정 시) 의존성 설치
uv sync --all-extras

# 4. .env 파일 생성 및 API 키 입력
# cp .env.example .env # 예제 파일 복사
# nano .env
```

`.env` 파일에 `GEMINI_API_KEY` 등을 설정해야 합니다.

## 💻 사용법

### 🐳 Docker를 통한 배포 (가장 간단)

```bash
# Docker 이미지 실행 (1분 이내 시작)
docker run -d -p 8501:8501 \
  -e GEMINI_API_KEY="your-api-key" \
  ghcr.io/ntts9990/ragtrace:latest

# 브라우저에서 http://localhost:8501 접속
```

자세한 Docker 배포 방법은 [Docker 배포 가이드](docs/Docker_Deployment_Guide.md)를 참고하세요.

### 웹 대시보드 (로컬 실행)

```bash
# uv를 사용하여 대시보드 실행
uv run streamlit run src/presentation/web/main.py

# 또는 justfile을 사용 (Just 설치 시)
just dashboard
```
브라우저에서 `http://localhost:8501`에 접속하여 평가를 시작하세요.

### CLI

CLI를 통해 더 세밀한 제어가 가능합니다.

```bash
# Excel/CSV 데이터를 JSON으로 변환 (검증 포함)
uv run python cli.py import-data your_data.xlsx --validate

# 변환된 데이터로 평가 실행
uv run python cli.py evaluate your_data --llm gemini --embedding bge_m3

# 기본 평가 실행 (기본값: evaluation_data.json)
uv run python cli.py evaluate evaluation_data --llm gemini --embedding gemini

# 사용 가능한 옵션 확인
uv run python cli.py --help
```

#### 📊 Excel/CSV 데이터 형식

Excel 또는 CSV 파일은 다음 4개 컬럼을 포함해야 합니다:

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `question` | 평가할 질문 | "원자력 발전소의 주요 구성요소는?" |
| `contexts` | 참고 문맥들 | JSON 배열 또는 `;` 구분 |
| `answer` | 시스템 답변 | "원자로, 증기발생기, 터빈발전기..." |
| `ground_truth` | 정답 기준 | "원자로, 증기발생기, 터빈발전기" |

**contexts 작성 방법:**
- JSON 배열: `["첫 번째 문맥", "두 번째 문맥"]` (권장)
- 세미콜론 구분: `첫 번째 문맥;두 번째 문맥`
- 파이프 구분: `첫 번째 문맥|두 번째 문맥`
- 단일 문맥: `하나의 긴 문맥 내용`

## 📁 프로젝트 구조

```
RAGTrace/
├── 📂 src/                          # 소스 코드 (Clean Architecture)
│   ├── 📂 application/              # 애플리케이션 계층 (Use Cases, Ports)
│   │   ├── ports/
│   │   ├── services/
│   │   └── use_cases/
│   ├── 📂 container/                # 의존성 주입 (DI) 컨테이너
│   ├── 📂 domain/                   # 도메인 계층 (Entities, Value Objects)
│   │   ├── entities/
│   │   └── value_objects/
│   ├── 📂 infrastructure/           # 인프라 계층 (DB, API, Adapters)
│   │   ├── data_import/
│   │   ├── evaluation/
│   │   ├── llm/
│   │   └── repository/
│   ├── 📂 presentation/             # 프레젠테이션 계층 (CLI, Web UI)
│   │   └── web/
│   └── 📂 utils/                    # 공통 유틸리티
│
├── 📂 data/                         # 평가 데이터 및 DB
├── 📂 docs/                         # 핵심 문서
├── 📂 models/                       # (Git 추적 제외) 로컬 모델 저장소
├── 📂 tests/                        # 테스트 코드 (90%+ 커버리지)
│
├── cli.py                           # CLI 애플리케이션 진입점
├── run_dashboard.py                 # 웹 대시보드 실행 스크립트
├── pyproject.toml                   # 프로젝트 및 의존성 설정
└── README.md                        # 이 파일
```

## 🔧 기술 스택 및 특징

- **언어**: Python 3.11+
- **패키지 관리**: `uv`
- **핵심 프레임워크**: `Ragas`, `Streamlit`, `dependency-injector`
- **코드 품질**: `black`, `isort`, `ruff`, `mypy` (pre-commit으로 자동화)
- **테스트**: `pytest`, `pytest-cov`
- **CI/CD**: GitHub Actions

## 🤝 기여하기

Pull Request는 언제나 환영합니다. 기여하기 전에 `docs/Development_Guide.md`를 참고해주세요.

## 📄 라이선스

이 프로젝트는 Apache License 2.0 하에 배포됩니다.