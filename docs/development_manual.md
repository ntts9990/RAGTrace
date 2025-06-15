# 🛠️ RAGAS 평가 시스템 개발 매뉴얼

## 📖 목차

1. [아키텍처 개요](#-아키텍처-개요)
2. [개발 환경 설정](#-개발-환경-설정)
3. [핵심 기능 확장](#-핵심-기능-확장)
4. [로컬 LLM 통합](#-로컬-llm-통합)
5. [테스트 전략](#-테스트-전략)
6. [배포 가이드](#-배포-가이드)

## 🏗️ 아키텍처 개요

### RAGAS 프레임워크 통합

본 프로젝트는 ExplodingGradients의 [RAGAS](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 구축되었습니다:

> 🎯 **RAGAS**: "Supercharge Your LLM Application Evaluations"
> - 객관적 메트릭으로 LLM 애플리케이션 정밀 평가
> - 지능적 테스트 데이터 자동 생성
> - LangChain 등 주요 LLM 프레임워크와 완벽 통합
> - 프로덕션 환경에서 피드백 루프 구축 지원

### Clean Architecture 구조

```
src/
├── domain/           # 🏛️ 핵심 비즈니스 로직
│   ├── entities/     # EvaluationResult, EvaluationData
│   ├── value_objects/# Metrics
│   └── exceptions/   # EvaluationError
├── application/      # 🔧 유스케이스
│   ├── use_cases/    # RunEvaluationUseCase
│   └── ports/        # 인터페이스 정의
├── infrastructure/   # 🔌 외부 시스템 어댑터
│   ├── evaluation/   # RagasEvalAdapter
│   ├── llm/          # GeminiAdapter, LocalLLMAdapter
│   └── repository/   # FileRepositoryAdapter, DBAdapter
└── presentation/     # 🖥️ UI 레이어
    ├── main.py       # CLI 인터페이스
    └── web/          # Streamlit 대시보드
```

### 의존성 규칙

**핵심 원칙**: 의존성은 항상 외부→내부 방향

```
Presentation → Application → Domain ← Infrastructure
```

- **Domain**: 외부 의존성 없음 (순수 비즈니스 로직)
- **Application**: Domain만 의존 (유스케이스 구현)
- **Infrastructure**: Application 포트 구현
- **Presentation**: Application 유스케이스 사용

## 🚀 개발 환경 설정

### 필수 도구

```bash
# Python 3.11+ 설치 확인
python --version

# 프로젝트 클론 및 환경 설정
git clone https://github.com/ntts9990/ragas-test.git
cd ragas-test
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 개발 의존성 설치 (자동으로 코드 품질 도구도 포함)
pip install -e ".[dev]"

# Git hooks 설정
pre-commit install
```

### IDE 설정 (VS Code)

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black"
}
```

### 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 개발용 설정
GEMINI_API_KEY=your_api_key
DEBUG_MODE=True
VERBOSE_LOGGING=True
```

## 🔧 핵심 기능 확장

### 1. 새로운 평가 메트릭 추가

#### Step 1: 도메인 엔티티 확장

```python
# src/domain/entities/evaluation_result.py
@dataclass
class EvaluationResult:
    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float
    ragas_score: float
    # 새 메트릭 추가
    semantic_similarity: float = 0.0
    
    def __post_init__(self):
        # 검증 로직에 새 메트릭 추가
        self._validate_score("semantic_similarity", self.semantic_similarity)
```

#### Step 2: RAGAS 어댑터 수정

```python
# src/infrastructure/evaluation/ragas_adapter.py
from ragas.metrics import semantic_similarity

class RagasEvalAdapter:
    def __init__(self):
        self.metrics = [
            faithfulness,
            answer_relevancy, 
            context_recall,
            context_precision,
            semantic_similarity  # 새 메트릭 추가
        ]
    
    def _extract_scores(self, result) -> dict:
        # 새 메트릭 점수 추출 로직 추가
        return {
            # 기존 메트릭들...
            "semantic_similarity": self._get_metric_score(result, "semantic_similarity")
        }
```

#### Step 3: 프레젠테이션 업데이트

```python
# src/presentation/web/main.py
def display_metrics(result: EvaluationResult):
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Faithfulness", f"{result.faithfulness:.3f}")
    # ... 기존 메트릭들
    with col5:
        st.metric("Semantic Similarity", f"{result.semantic_similarity:.3f}")
```

### 2. 새로운 데이터 소스 연동

#### PostgreSQL 어댑터 예시

```python
# src/infrastructure/repository/postgres_adapter.py
import psycopg2
from src.application.ports.repository import EvaluationRepositoryPort
from src.domain.entities.evaluation_data import EvaluationData

class PostgresRepositoryAdapter(EvaluationRepositoryPort):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def load_data(self) -> List[EvaluationData]:
        with psycopg2.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT question, contexts, answer, ground_truth 
                FROM evaluation_datasets 
                WHERE active = true
            """)
            
            return [
                EvaluationData(
                    question=row[0],
                    contexts=row[1], 
                    answer=row[2],
                    ground_truth=row[3]
                ) for row in cursor.fetchall()
            ]
```

#### 의존성 주입 수정

```python
# src/presentation/web/main.py
def create_use_case():
    # 환경 변수에 따라 어댑터 선택
    if os.getenv("USE_POSTGRES", "false").lower() == "true":
        repository = PostgresRepositoryAdapter(os.getenv("DATABASE_URL"))
    else:
        repository = FileRepositoryAdapter("data/evaluation_data.json")
    
    return RunEvaluationUseCase(
        repository_port=repository,
        llm_port=GeminiAdapter(),
        evaluation_runner=RagasEvalAdapter()
    )
```

## 🤖 로컬 LLM 통합

### Ollama 통합

#### 1. Ollama 어댑터 구현

```python
# src/infrastructure/llm/ollama_adapter.py
from langchain_community.llms import Ollama
from src.application.ports.llm import LlmPort

class OllamaAdapter(LlmPort):
    def __init__(self, model_name: str = "qwen2.5:14b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
    
    def get_llm(self):
        return Ollama(
            model=self.model_name,
            base_url=self.base_url,
            temperature=0.1
        )
```

#### 2. 환경 설정

```bash
# .env 파일
USE_LOCAL_LLM=True
LOCAL_LLM_TYPE=ollama
LOCAL_LLM_MODEL=qwen2.5:14b
LOCAL_LLM_BASE_URL=http://localhost:11434
```

#### 3. 어댁터 팩토리 패턴

```python
# src/infrastructure/llm/llm_factory.py
def create_llm_adapter() -> LlmPort:
    if os.getenv("USE_LOCAL_LLM", "false").lower() == "true":
        llm_type = os.getenv("LOCAL_LLM_TYPE", "ollama")
        
        if llm_type == "ollama":
            return OllamaAdapter(
                model_name=os.getenv("LOCAL_LLM_MODEL", "qwen2.5:14b"),
                base_url=os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
            )
        elif llm_type == "hcx":
            return HCXAdapter(
                model_name=os.getenv("LOCAL_LLM_MODEL", "hcx-005"),
                endpoint=os.getenv("LOCAL_LLM_ENDPOINT")
            )
    else:
        return GeminiAdapter()
```

### HCX-005 통합 (폐쇄망 환경)

```python
# src/infrastructure/llm/hcx_adapter.py
import requests
from langchain_core.language_models import BaseLLM

class HCXAdapter(LlmPort):
    def __init__(self, model_name: str, endpoint: str, api_key: str = None):
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_key = api_key
    
    def get_llm(self):
        return HCXLanguageModel(
            model_name=self.model_name,
            endpoint=self.endpoint,
            api_key=self.api_key,
            temperature=0.1
        )

class HCXLanguageModel(BaseLLM):
    def __init__(self, model_name: str, endpoint: str, api_key: str = None, **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_key = api_key
    
    def _call(self, prompt: str, stop: list = None, **kwargs) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": 4096
        }
        
        response = requests.post(f"{self.endpoint}/generate", json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()["response"]
```

## 🧪 테스트 전략

### 테스트 아키텍처

```
tests/
├── domain/           # 순수 유닛 테스트
├── application/      # 모킹 기반 유스케이스 테스트
├── infrastructure/   # 통합 테스트 + 모킹
└── presentation/     # E2E 테스트
```

### 핵심 테스트 패턴

#### 1. 도메인 테스트 (순수 유닛)

```python
# tests/domain/test_evaluation_result.py
def test_evaluation_result_validation():
    """점수 범위 검증 테스트"""
    with pytest.raises(ValueError, match="점수는 0.0과 1.0 사이여야 합니다"):
        EvaluationResult(
            faithfulness=1.5,  # 잘못된 값
            answer_relevancy=0.8,
            context_recall=0.7,
            context_precision=0.9,
            ragas_score=0.85
        )
```

#### 2. 애플리케이션 테스트 (모킹)

```python
# tests/application/test_run_evaluation.py
@pytest.fixture
def mock_dependencies():
    return {
        "repository_port": Mock(spec=EvaluationRepositoryPort),
        "llm_port": Mock(spec=LlmPort), 
        "evaluation_runner": Mock(spec=EvaluationPort)
    }

def test_run_evaluation_success(mock_dependencies):
    # Given
    mock_dependencies["repository_port"].load_data.return_value = [sample_data]
    mock_dependencies["evaluation_runner"].evaluate.return_value = expected_result
    
    # When
    use_case = RunEvaluationUseCase(**mock_dependencies)
    result = use_case.execute()
    
    # Then
    assert result.ragas_score == expected_result["ragas_score"]
```

#### 3. 인프라 테스트 (통합 + 모킹)

```python
# tests/infrastructure/test_ragas_adapter.py
@patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
def test_ragas_evaluation(mock_evaluate):
    # RAGAS 라이브러리 모킹
    mock_result = create_mock_ragas_result()
    mock_evaluate.return_value = mock_result
    
    adapter = RagasEvalAdapter()
    result = adapter.evaluate(test_dataset, test_llm)
    
    assert result["faithfulness"] == pytest.approx(0.85, abs=0.01)
```

### 테스트 실행

```bash
# 전체 테스트 (149개 테스트 실행)
pytest

# 커버리지 확인 (99.75% 달성)
pytest --cov=src --cov-report=html --cov-fail-under=80

# 특정 레이어 테스트
pytest tests/domain/              # 도메인 로직 테스트
pytest tests/application/         # 유스케이스 테스트  
pytest tests/infrastructure/      # 외부 어댑터 테스트
pytest tests/presentation/        # UI 레이어 테스트

# 코드 품질 검사 (CI/CD에서 사용하는 것과 동일)
black --check src/
isort --check-only src/
flake8 src/ --count --select=E9,F63,F7,F82
mypy src/ --ignore-missing-imports

# 자동 리포트 생성
python scripts/generate_test_report.py
```

## 🚀 배포 가이드

### Docker 배포

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/ ./data/
COPY run_dashboard.py .

EXPOSE 8501
CMD ["streamlit", "run", "src/presentation/web/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  ragas-eval:
    build: .
    container_name: ragas-evaluation
    ports:
      - "8501:8501"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - USE_LOCAL_LLM=${USE_LOCAL_LLM:-false}
      - LOCAL_LLM_BASE_URL=http://ollama:11434
    volumes:
      - ./data:/app/data
      - ./reports:/app/reports
      - evaluation_db:/app/data/db
    networks:
      - ragas-network
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: ragas-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - ragas-network
    restart: unless-stopped

volumes:
  ollama_data:
    driver: local
  evaluation_db:
    driver: local

networks:
  ragas-network:
    driver: bridge
```

### 프로덕션 설정

#### 환경별 설정 분리

```bash
# .env.production
GEMINI_API_KEY=prod_api_key
DEBUG_MODE=False
VERBOSE_LOGGING=False
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 보안 설정
SSL_ENABLED=True
SSL_CERT_PATH=/etc/ssl/certs/ragas.crt
SSL_KEY_PATH=/etc/ssl/private/ragas.key
```

#### CI/CD 파이프라인

프로젝트는 완전 자동화된 CI/CD 파이프라인을 제공합니다:

**🧪 현재 구현된 워크플로우:**

1. **테스트 파이프라인** (`.github/workflows/test.yml`):
   - Python 3.11, 3.12 매트릭스 테스트
   - 코드 품질 검사: black, isort, flake8, mypy
   - 99.75% 테스트 커버리지 검증
   - 149개 테스트 실행

2. **Docker 빌드** (`.github/workflows/docker.yml`):
   - 멀티스테이지 Docker 이미지 빌드
   - 보안 강화된 컨테이너 (non-root)
   - 자동 레지스트리 푸시

3. **자동 배포** (`.github/workflows/deploy.yml`):
   - 스테이징 환경 자동 배포 (main 브랜치)
   - 프로덕션 배포 (태그 기반)
   - 배포 상태 알림

**📊 CI/CD 현재 상태:**
- ✅ 모든 파이프라인 정상 작동
- ✅ 6개 성공, 1개 건너뛰기 (프로덕션)
- ✅ 완전 자동화된 배포 프로세스

```yaml
# 로컬에서 CI/CD 검증하기
name: Local CI Check
steps:
  - run: pytest --cov=src --cov-fail-under=80
  - run: black --check src/
  - run: isort --check-only src/
  - run: flake8 src/ --count --select=E9,F63,F7,F82
  - run: mypy src/ --ignore-missing-imports
  - run: docker build -t ragas-eval .
```

## 📚 추가 참고자료

### 핵심 문서

- **[Clean Architecture 가이드](./clean_architecture_summary.md)**: 아키텍처 상세 설명
- **[RAGAS 메트릭 가이드](./RAGAS_METRICS.md)**: 평가 지표 설명
- **[테스트 리포트](../reports/)**: 자동 생성된 테스트 분석

### 유용한 스크립트

```bash
# 데이터 검증
python scripts/analysis/validate_dataset.py data/your_data.json

# 성능 모니터링  
python scripts/monitor_api_usage.py

# 테스트 리포트 생성
python scripts/generate_test_report.py
```

### 개발 베스트 프랙티스

1. **테스트 우선 개발**: 새 기능 구현 전 테스트 작성
2. **의존성 역전 준수**: 인터페이스를 통한 느슨한 결합
3. **단일 책임 원칙**: 각 클래스는 하나의 책임만
4. **커버리지 유지**: 99.75% 테스트 커버리지 달성 및 유지
5. **코드 품질**: black, isort, flake8, mypy 모든 검사 통과
6. **CI/CD 친화적**: 모든 변경사항이 자동 파이프라인 통과
7. **문서화**: 코드 변경 시 문서도 함께 업데이트

### 🎯 현재 프로젝트 성과

- ✅ **149개 테스트** 모두 통과
- ✅ **99.75% 커버리지** 달성
- ✅ **완전 자동화된 CI/CD** 파이프라인 구축
- ✅ **Docker 프로덕션** 준비 완료
- ✅ **Clean Architecture** 완전 구현
- ✅ **코드 품질** A+ 등급 달성

---

더 자세한 정보가 필요하면 [GitHub Issues](https://github.com/ntts9990/ragas-test/issues)를 통해 문의해주세요.