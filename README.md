# RAGAS 테스트 및 평가 대시보드

이 프로젝트는 RAG(Retrieval-Augmented Generation) 시스템의 성능을 평가하고 분석하기 위한 웹 대시보드입니다. [Ragas](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 핵심 평가 지표(Faithfulness, Answer Relevancy, Context Precision, Context Recall)를 측정하고, 평가 결과를 시각화하여 보여줍니다.

## 주요 기능

- **RAG 파이프라인 성능 평가**: 지정된 데이터셋을 사용하여 RAG 파이프라인의 성능을 정량적으로 평가합니다.
- **상세 평가 지표 제공**: Faithfulness, Answer Relevancy, Context Precision, Context Recall 등 Ragas에서 제공하는 주요 지표를 계산합니다.
- **인터랙티브 대시보드**: [Streamlit](https://streamlit.io/)을 사용하여 평가 결과를 시각적으로 탐색하고 분석할 수 있는 인터랙티브 웹 대시보드를 제공합니다.
- **평가 이력 관리**: 실행된 평가 결과를 로컬 데이터베이스(SQLite)에 저장하여 이력을 추적하고 비교할 수 있습니다.
- **포괄적 테스트 커버리지**: 99% 테스트 커버리지로 프로덕션 레벨의 안정성을 보장합니다.

## 시스템 아키텍처

본 프로젝트는 **클린 아키텍처(Clean Architecture)** 를 채택하여 각 계층의 역할을 명확히 분리하고, 유연하고 확장 가능한 구조를 지향합니다. 클린 아키텍처는 헥사고날 아키텍처(Hexagonal Architecture)와 핵심 원칙을 공유하지만, 내부 계층을 더욱 명확하게 정의하여 비즈니스 로직을 외부 기술 변화로부터 강력하게 보호합니다.

- **Domain (Entities)**: 프로젝트의 핵심 비즈니스 규칙과 데이터 모델을 정의하는 가장 안쪽 계층입니다.
- **Application (Use Cases)**: 애플리케이션의 특정 비즈니스 흐름을 정의하고, 도메인 객체를 조율하는 유스케이스를 포함합니다.
- **Infrastructure (Interface Adapters)**: 외부 시스템(LLM, 데이터베이스, 파일 시스템 등)과의 연동을 담당하는 구체적인 구현체(어댑터)를 포함합니다. Application 계층에 정의된 포트(인터페이스)를 구현합니다.
- **Presentation (Frameworks & Drivers)**: 사용자 인터페이스(Streamlit 웹 대시보드)를 담당하는 가장 바깥쪽 계층입니다.

## 시작하기

### 1. 사전 요구사항

- Python 3.11 이상
- Git
- [uv](https://github.com/astral-sh/uv): `pip`보다 빠른 Python 패키지 설치 도구 (선택사항이지만 권장)

### 2. 프로젝트 클론 및 설정

```bash
# 1. 프로젝트를 클론합니다.
git clone https://github.com/your-username/ragas-test.git
cd ragas-test

# 2. 가상환경을 생성하고 활성화합니다. (uv 사용)
uv venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\activate  # Windows

# 3. 필요한 패키지를 설치합니다. (uv 사용)
uv sync --dev  # 개발 의존성 포함
# 또는 pip 사용 시:
# pip install -e .[dev]
```

### 3. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, Google Gemini API 키를 추가합니다.

```
GEMINI_API_KEY="여기에_당신의_API_키를_입력하세요"
```

### 4. 평가 데이터 준비

평가에 사용할 데이터셋을 `data/evaluation_dataset.json` 형식으로 준비합니다. JSON 파일은 다음 구조를 따르는 객체들의 리스트여야 합니다.

```json
[
  {
    "question": "첫 번째 질문 내용",
    "contexts": ["관련 컨텍스트 1", "관련 컨텍스트 2"],
    "answer": "RAG 시스템이 생성한 답변",
    "ground_truth": "실제 정답"
  },
  {
    "question": "두 번째 질문 내용",
    "contexts": ["다른 컨텍스트"],
    "answer": "RAG 시스템이 생성한 두 번째 답변",
    "ground_truth": "두 번째 실제 정답"
  }
]
```

### 5. 대시보드 실행

다음 스크립트를 실행하여 Streamlit 대시보드를 시작합니다.

```bash
python run_dashboard.py
```

실행 후, 터미널에 나타나는 URL (기본값: `http://localhost:8501`)에 접속하여 대시보드를 확인할 수 있습니다.

## 테스트

### 테스트 실행

프로젝트는 **99% 테스트 커버리지**를 달성하여 프로덕션 레벨의 안정성을 보장합니다.

```bash
# 모든 테스트 실행
pytest

# 커버리지 리포트와 함께 테스트 실행
pytest --cov=src --cov-report=html --cov-report=term-missing

# 특정 모듈 테스트
pytest tests/domain/
pytest tests/application/
pytest tests/infrastructure/

# 상세 출력으로 테스트 실행
pytest -v

# 실패한 테스트만 재실행
pytest --lf
```

### 테스트 구조

```
tests/
├── application/
│   ├── ports/                 # 포트 인터페이스 테스트
│   └── use_cases/             # 유스케이스 테스트
├── domain/
│   ├── entities/              # 도메인 엔티티 테스트
│   ├── exceptions/            # 예외 처리 테스트
│   └── value_objects/         # 값 객체 테스트
├── infrastructure/
│   ├── evaluation/            # RAGAS 어댑터 테스트
│   ├── llm/                   # Gemini LLM 어댑터 테스트
│   └── repository/            # 파일 저장소 어댑터 테스트
└── presentation/              # 메인 애플리케이션 테스트
```

### 테스트 커버리지 현황

| 모듈 | 커버리지 | 주요 테스트 내용 |
|------|----------|------------------|
| **전체** | **99%** | **395개 중 391개 라인 커버** |
| Domain | 100% | 엔티티 검증, 예외 처리, 값 객체 |
| Application | 98% | 유스케이스 로직, 포트 인터페이스 |
| Infrastructure | 99% | 외부 API 연동, 파일 처리, Rate limiting |
| Presentation | 97% | 메인 애플리케이션 실행 |

### 테스트가 보장하는 것들

#### 1. **아키텍처 무결성**
- ✅ Clean Architecture 계층 분리
- ✅ 의존성 역전 원칙 (DIP) 준수
- ✅ 포트-어댑터 패턴 정확한 구현

#### 2. **비즈니스 로직 정확성**
- ✅ 평가 데이터 검증 (빈 값, 필수 필드)
- ✅ 평가 결과 점수 범위 (0.0-1.0) 강제
- ✅ 필수 메트릭 누락 시 적절한 예외 발생

#### 3. **외부 시스템 연동 안정성**
- ✅ Gemini API Rate limiting (1000 RPM)
- ✅ 임베딩 API Rate limiting (10 RPM)
- ✅ 네트워크 오류 시 graceful degradation
- ✅ API 키 누락 시 적절한 예외 처리

#### 4. **오류 처리 및 복구**
- ✅ 계층별 예외 처리 (EvaluationError, TimeoutError 등)
- ✅ 파일 시스템 오류 처리 (파일 없음, 권한 오류)
- ✅ JSON 파싱 오류 처리

#### 5. **한국어 RAG 평가 정확성**
- ✅ 4가지 핵심 메트릭 정확한 계산
- ✅ 종합 점수(ragas_score) 계산
- ✅ 개별 QA 쌍별 상세 점수 제공

### 테스트 실행 예시

```bash
# 전체 테스트 실행 결과
$ pytest --cov=src --cov-report=term-missing
================================= test session starts =================================
collected 96 items

tests/application/ports/test_ports.py ...                              [  3%]
tests/application/use_cases/test_run_evaluation.py ......              [  9%]
tests/domain/exceptions/test_evaluation_exceptions.py .....            [ 14%]
tests/domain/test_evaluation_data.py ........                          [ 22%]
tests/domain/test_evaluation_result.py .............                   [ 36%]
tests/domain/value_objects/test_metrics.py .............               [ 50%]
tests/infrastructure/evaluation/test_ragas_adapter.py ..................[ 68%]
tests/infrastructure/llm/test_gemini_adapter.py ..............         [ 83%]
tests/infrastructure/repository/test_file_adapter.py ........          [ 91%]
tests/presentation/test_main.py ......                                 [ 97%]
tests/presentation/test_main_module.py ..                              [100%]

========================== 96 passed in 11.71s ==========================

Name                                             Stmts   Miss  Cover   Missing
------------------------------------------------------------------------------
src/application/ports/evaluation.py                  7      0   100%
src/application/ports/llm.py                         6      0   100%
src/application/ports/repository.py                  7      0   100%
src/application/use_cases/run_evaluation.py         41      1    98%   73
src/domain/entities/evaluation_data.py              17      0   100%
src/domain/entities/evaluation_result.py            22      1    95%   40
src/domain/exceptions/evaluation_exceptions.py      14      0   100%
src/domain/value_objects/metrics.py                 31      0   100%
src/infrastructure/evaluation/ragas_adapter.py     138      1    99%   206
src/infrastructure/llm/gemini_adapter.py            37      0   100%
src/infrastructure/repository/file_adapter.py       21      0   100%
src/presentation/main.py                            31      1    97%   66
------------------------------------------------------------------------------
TOTAL                                              395      4    99%
```

## 프로젝트 구조

```
.
├── data/                      # 평가 데이터셋 저장 위치
│   └── evaluation_dataset.json
├── docs/                      # 프로젝트 문서
│   └── development_manual.md
├── htmlcov/                   # 테스트 커버리지 HTML 리포트
├── run_dashboard.py           # 대시보드 실행 스크립트
├── src/                       # 소스 코드
│   ├── application/           # 애플리케이션 계층 (유스케이스, 포트)
│   ├── domain/                # 도메인 계층 (엔티티)
│   ├── infrastructure/        # 인프라 계층 (외부 시스템 어댑터)
│   └── presentation/          # 프레젠테이션 계층 (UI)
├── tests/                     # 테스트 코드 (96개 테스트, 99% 커버리지)
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── presentation/
├── .env.example               # 환경 변수 예시 파일
├── config.py                  # 환경 변수 로드 및 설정
├── pyproject.toml             # 프로젝트 설정 및 의존성 관리
└── README.md
```

## 기여하기

프로젝트에 기여하고 싶으신 분들은 `docs/development_manual.md` 문서를 참고해주세요. 이슈 생성이나 Pull Request는 언제나 환영합니다.

### 기여 가이드라인

1. **테스트 작성**: 새로운 기능 추가 시 반드시 테스트를 작성해주세요.
2. **커버리지 유지**: 99% 커버리지를 유지해주세요.
3. **Clean Architecture**: 계층 분리 원칙을 준수해주세요.
4. **한국어 지원**: 사용자 메시지는 한국어로 작성해주세요.
