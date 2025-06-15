# RAGAS 테스트 및 평가 대시보드

이 프로젝트는 RAG(Retrieval-Augmented Generation) 시스템의 성능을 평가하고 분석하기 위한 웹 대시보드입니다. [Ragas](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 핵심 평가 지표(Faithfulness, Answer Relevancy, Context Precision, Context Recall)를 측정하고, 평가 결과를 시각화하여 보여줍니다.

## 주요 기능

- **RAG 파이프라인 성능 평가**: 지정된 데이터셋을 사용하여 RAG 파이프라인의 성능을 정량적으로 평가합니다.
- **상세 평가 지표 제공**: Faithfulness, Answer Relevancy, Context Precision, Context Recall 등 Ragas에서 제공하는 주요 지표를 계산합니다.
- **인터랙티브 대시보드**: [Streamlit](https://streamlit.io/)을 사용하여 평가 결과를 시각적으로 탐색하고 분석할 수 있는 인터랙티브 웹 대시보드를 제공합니다.
- **평가 이력 관리**: 실행된 평가 결과를 로컬 데이터베이스(SQLite)에 저장하여 이력을 추적하고 비교할 수 있습니다.

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
uv pip install -e .
# 또는 pip 사용 시:
# pip install -e .
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

### 6. 테스트 실행

프로젝트의 유닛 및 통합 테스트를 실행하려면 다음 명령어를 사용하세요. `pytest`를 포함한 개발 의존성이 설치되어 있어야 합니다.

```bash
# 개발 의존성 설치 (최초 1회)
uv pip install -e .[dev]

# 테스트 실행
pytest
```

## 프로젝트 구조

```
.
├── data/                      # 평가 데이터셋 저장 위치
│   └── evaluation_dataset.json
├── docs/                      # 프로젝트 문서
│   └── development_manual.md
├── run_dashboard.py           # 대시보드 실행 스크립트
├── src/                       # 소스 코드
│   ├── application/           # 애플리케이션 계층 (유스케이스, 포트)
│   ├── domain/                # 도메인 계층 (엔티티)
│   ├── infrastructure/        # 인프라 계층 (외부 시스템 어댑터)
│   └── presentation/          # 프레젠테이션 계층 (UI)
├── .env.example               # 환경 변수 예시 파일
├── config.py                  # 환경 변수 로드 및 설정
├── pyproject.toml             # 프로젝트 설정 및 의존성 관리
├── tests/                     # 테스트 코드
│   ├── application/
│   ├── domain/
│   └── infrastructure/
└── README.md
```

## 기여하기

프로젝트에 기여하고 싶으신 분들은 `docs/development_manual.md` 문서를 참고해주세요. 이슈 생성이나 Pull Request는 언제나 환영합니다.
