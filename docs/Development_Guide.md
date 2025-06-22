# 🛠️ RAGTrace 통합 개발 가이드

이 문서는 RAGTrace 프로젝트의 아키텍처, 개발 환경 설정, 기능 확장, LLM 통합, 테스트, 배포 및 문제 해결에 대한 모든 정보를 담고 있는 포괄적인 가이드입니다.

## 📖 목차

1. [아키텍처 개요](#-아키텍처-개요)
2. [개발 환경 설정](#-개발-환경-설정)
3. [📊 데이터 Import 가이드](Data_Import_Guide.md) - **Excel/CSV 데이터 활용법**
4. [핵심 기능 확장 가이드](#-핵심-기능-확장-가이드)
5. [LLM 통합 및 커스터마이징](#-llm-통합-및-커스터마이징)
6. [테스트 및 코드 품질](#-테스트-및-코드-품질)
7. [배포 가이드](#-배포-가이드)
8. [문제 해결 가이드](#-문제-해결-가이드-faq)

---

## 🏗️ 아키텍처 개요

### Clean Architecture 구조

본 프로젝트는 Robert C. Martin의 **클린 아키텍처(Clean Architecture)** 패턴을 채택하여 계층 간의 의존성을 명확히 하고, 유지보수성과 테스트 용이성을 극대화했습니다.

```
src/
├── domain/           # 🏛️ 핵심 비즈니스 로직 (외부 의존성 없음)
│   ├── entities/     # EvaluationResult, EvaluationData
│   └── ...
├── application/      # 🔧 유스케이스 및 비즈니스 흐름
│   ├── use_cases/    # RunEvaluationUseCase
│   └── ports/        # 외부와 소통하는 인터페이스(추상 클래스)
├── infrastructure/   # 🔌 외부 시스템 연동 (Ports 구현)
│   ├── llm/          # GeminiAdapter, HcxAdapter 등
│   └── ...
└── presentation/     # 🖥️ UI/CLI (사용자와의 상호작용)
    └── ...
```

### 의존성 규칙

**핵심 원칙**: 의존성은 항상 외부 계층에서 내부 계층으로 향합니다. `Infrastructure`는 `Application`의 `Port`를 구현함으로써 의존성 역전 원칙(DIP)을 따릅니다.

```
Presentation → Application → Domain ← Infrastructure
```

---

## 🚀 개발 환경 설정

### 1. 기본 설정

```bash
# Python 3.11+ 설치 확인
python --version

# 프로젝트 클론 및 가상 환경 생성
git clone https://github.com/your-repo/RAGTrace.git
cd RAGTrace
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# uv를 사용하여 의존성 설치
uv pip sync

# Git hooks 설정 (코드 커밋 전 자동 검사)
pre-commit install
```

### 2. 오프라인/폐쇄망 환경을 위한 의존성 패키징 (필요 시)

외부망 접속이 불가능한 환경으로 프로젝트를 이전해야 할 경우, 아래 절차를 따르세요.

1.  **(외부망)** `packages/` 폴더에 모든 의존성 휠 파일 다운로드:
    ```bash
    mkdir packages
    uv pip download -r requirements.txt --dest packages/
    ```
2.  프로젝트 폴더 전체(`packages/` 포함)를 압축하여 폐쇄망으로 이동.
3.  **(내부망)** `packages/` 폴더를 사용하여 의존성 설치:
    ```bash
    uv pip install --no-index --find-links=./packages -r requirements.txt
    ```

### 3. 환경 변수

프로젝트 루트에 `.env` 파일을 생성하고 필요한 API 키 등을 설정합니다.

```bash
# .env 파일 예시
GEMINI_API_KEY="your_gemini_api_key"
HCX_API_KEY="your_hcx_api_key"
HCX_API_GATEWAY_KEY="your_hcx_gateway_key"
```

---

## 🔧 핵심 기능 확장 가이드

### 1. 새로운 평가 메트릭 추가

1.  **도메인 확장**: `src/domain/entities/evaluation_result.py`의 `EvaluationResult` 데이터 클래스에 새 메트릭 필드를 추가합니다.
2.  **어댑터 수정**: `src/infrastructure/evaluation/ragas_adapter.py`에서 `ragas.metrics`의 새 메트릭을 import하고, `RagasEvalAdapter`의 `metrics` 리스트와 결과 파싱 로직에 추가합니다.
3.  **UI 업데이트**: `src/presentation/web/`의 관련 컴포넌트에서 새 메트릭을 시각화합니다.

### 2. 새로운 데이터 소스 연동 (예: PostgreSQL)

1.  **어댑터 생성**: `src/infrastructure/repository/`에 `PostgresRepositoryAdapter.py` 파일을 생성합니다.
2.  **인터페이스 구현**: `EvaluationRepositoryPort`를 상속받아 `load_data` 메서드를 구현합니다. 이 메서드는 DB에 연결하여 데이터를 조회하고, `EvaluationData` 객체 리스트로 반환합니다.
3.  **컨테이너 수정**: `src/container.py`에서 기존 `FileRepositoryAdapter` 대신 `PostgresRepositoryAdapter`를 주입하도록 수정합니다.

---

## 🤖 LLM 통합 및 커스터마이징

### Part A: 일반 원칙 (온라인 API 기반 LLM 추가)

새로운 LLM을 추가하는 것은 **새로운 어댑터를 만드는 것**과 같습니다.

1.  **어댑터 생성**: `src/infrastructure/llm/` 디렉토리에 `my_llm_adapter.py` 파일을 생성하고, `LlmPort`를 상속받는 어댑터 클래스를 작성합니다.
2.  **인터페이스 구현**: `LlmPort`의 추상 메서드(`generate_answer`, `get_llm` 등)를 새 LLM의 API 명세에 맞게 구현합니다.
3.  **설정 추가**: `.env`와 `src/config.py`에 새 LLM에 필요한 API 키나 모델 이름을 추가합니다.
4.  **컨테이너 수정**: `src/container.py`에서 기존 어댑터 대신 새로 만든 어댑터를 주입하도록 교체합니다. 아키텍처의 다른 부분은 수정할 필요가 없습니다.

### Part B: 로컬/오프라인 모델 통합

인터넷 연결 없이 로컬에 저장된 모델 파일(예: Hugging Face 모델)을 사용하는 방법입니다.

1.  **모델 다운로드**: 외부망에서 `huggingface-cli`나 `snapshot_download` 스크립트를 사용하여 모델 파일을 다운로드하고, 이를 폐쇄망 서버의 특정 경로(예: `/models/bge-m3`)로 옮깁니다.
2.  **오프라인 어댑터 구현**:
    -   `transformers` 라이브러리의 `AutoTokenizer.from_pretrained(local_files_only=True)`와 `AutoModel...from_pretrained(local_files_only=True)`를 사용하여 로컬 경로에서 모델을 로드하는 로직을 작성합니다.
    -   `generate_answer` 메서드 내에서 직접 모델 추론을 수행합니다.
3.  **설정 및 컨테이너 수정**: `config.py`와 `container.py`에서 오프라인 모델의 경로를 받아 어댑터를 초기화하도록 수정합니다.

### Part C: 하드웨어 가속 및 최적화 (BGE-M3 예시)

로컬 임베딩 모델의 성능을 극대화하기 위한 가이드입니다.

-   **자동 디바이스 감지**: 코드는 `torch.cuda.is_available()` (NVIDIA GPU), `torch.backends.mps.is_available()` (Apple Silicon)을 순차적으로 확인하여 최적의 하드웨어를 자동으로 사용합니다.
-   **수동 설정**: `.env` 파일에 `BGE_M3_DEVICE="cuda"`와 같이 명시하여 특정 하드웨어를 강제할 수 있습니다.
-   **성능 최적화**:
    -   **배치 크기**: CUDA 사용 시 더 큰 배치 크기를 적용하여 처리량을 높입니다.
    -   **메모리 관리**: 대용량 처리 후 `torch.cuda.empty_cache()`를 호출하여 GPU 메모리를 정리합니다.
    -   **FP16**: `use_fp16=True` 옵션을 통해 GPU에서 더 빠른 연산을 수행합니다.

---

## 🧪 테스트 및 코드 품질

### 테스트 아키텍처 및 실행

프로젝트는 **테스트 피라미드** 전략을 따릅니다.

-   `tests/domain/`: 외부 의존성 없는 순수 단위 테스트.
-   `tests/application/`: `unittest.mock`을 사용한 유스케이스 테스트.
-   `tests/infrastructure/`: 외부 라이브러리/API를 모킹하는 통합 테스트.
-   `tests/presentation/`: `Streamlit` 렌더링 및 E2E 테스트.

```bash
# 전체 테스트 실행
uv run pytest

# 커버리지 리포트 생성 (목표: 90% 이상)
uv run pytest --cov=src --cov-report=html
```

### 코드 품질 도구 (pre-commit)

`pre-commit`을 통해 커밋 시 자동으로 코드 품질을 검사합니다.
-   `black`: 코드 포맷터
-   `isort`: 임포트 순서 정렬
-   `flake8`: 코드 스타일 및 오류 검사
-   `mypy`: 정적 타입 검사

---

## 🚀 배포 가이드

### Docker 배포

프로젝트는 `Dockerfile`과 `docker-compose.yml`을 제공하여 손쉬운 컨테이너화 배포를 지원합니다.

```bash
# Docker 이미지 빌드
docker build -t ragtrace-app .

# Docker Compose를 사용한 서비스 실행
docker compose up -d
```

`docker-compose.yml`은 RAGTrace 애플리케이션과 로컬 LLM(Ollama) 서버를 함께 실행하는 구성을 포함합니다.

### CI/CD 파이프라인

GitHub Actions를 통해 코드 품질 검사, 테스트, Docker 이미지 빌드 및 배포가 자동화되어 있습니다.

---

## ❓ 문제 해결 가이드 (FAQ)

### 1. 환경 설정 오류

-   **`ModuleNotFoundError: No module named 'src'`**: 프로젝트 루트 디렉토리에서 실행 중인지 확인하세요. `PYTHONPATH`가 올바르게 설정되었는지 확인합니다.
-   **`uv: command not found`**: `uv`가 제대로 설치되지 않았습니다. 공식 홈페이지의 설치 스크립트를 다시 실행하세요.

### 2. API 키 및 인증 오류

-   **`ValueError: ... API_KEY가 설정되지 않았습니다.`**: 프로젝트 루트에 `.env` 파일이 있는지, 파일 내에 올바른 키가 입력되었는지 확인하세요.
-   **`ConnectionError`**: 방화벽이나 프록시 설정을 확인하고, API 엔드포인트(`generativelanguage.googleapis.com` 등)에 대한 네트워크 연결이 가능한지 확인하세요.

### 3. Docker 관련 오류

-   **`failed to solve: process ... did not complete successfully`**: Docker 이미지 빌드 중 의존성 설치 등에서 실패한 경우입니다. `docker system prune -a`로 캐시를 정리하고 다시 시도하거나, `docker build --no-cache` 옵션을 사용해 보세요.
-   **`Error: Port 8501 is already in use`**: 해당 포트를 사용하는 다른 프로세스를 종료(`kill -9 $(lsof -t -i:8501)`)하거나, `docker-compose.yml`에서 다른 포트로 변경하세요.

### 4. 평가 실행 오류

-   **`OutOfMemoryError: CUDA out of memory`**: GPU 메모리가 부족한 경우입니다. 데이터셋을 더 작은 청크로 나누어 처리하거나, `.env` 또는 코드에서 배치 크기를 줄이세요.
-   **`Rate limit exceeded`**: LLM API의 분당/일일 요청 제한을 초과했습니다. 요청 사이에 `time.sleep()`을 추가하거나, 유료 플랜으로 업그레이드를 고려하세요.
