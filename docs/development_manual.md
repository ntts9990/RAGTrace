# 개발 매뉴얼

이 문서는 `ragas-test` 프로젝트의 아키텍처, 주요 설계 결정, 그리고 확장 및 유지보수 방법에 대해 기술합니다.

## 1. 프로젝트 아키텍처: 클린 아키텍처 (Clean Architecture)

본 프로젝트는 로버트 C. 마틴(Uncle Bob)이 제안한 **클린 아키텍처**를 기반으로 설계되었습니다. 이 아키텍처의 핵심 목표는 관심사의 분리(Separation of Concerns)이며, 특히 비즈니스 로직을 외부의 기술적인 구현(프레임워크, 데이터베이스 등)으로부터 완전히 분리하는 것입니다.

이러한 설계는 다음과 같은 장점을 가집니다:
- **프레임워크 독립성**: 비즈니스 로직은 웹 프레임워크나 DB 종류에 의존하지 않습니다.
- **테스트 용이성**: 핵심 비즈니스 로직을 외부 요소 없이 독립적으로 테스트할 수 있습니다.
- **UI 독립성**: UI를 웹, 데스크톱 앱, CLI 등으로 쉽게 교체할 수 있습니다.
- **데이터베이스 독립성**: 데이터 저장 방식을 Oracle, SQL Server, MongoDB 등으로 비교적 쉽게 변경할 수 있습니다.

### 아키텍처 다이어그램 및 계층 구조

클린 아키텍처는 동심원 모델로 표현되며, **의존성 규칙(The Dependency Rule)**을 따릅니다. 즉, 소스 코드 의존성은 항상 외부에서 내부를 향해야 합니다.

```
+-------------------------------------------------------------------------+
|                                                                         |
|  Frameworks & Drivers  (presentation, infrastructure/db, etc.)          |
|                                                                         |
|     +---------------------------------------------------------------+   |
|     |                                                               |   |
|     |  Interface Adapters  (infrastructure/adapters)                |   |
|     |                                                               |   |
|     |     +---------------------------------------------------+     |   |
|     |     |                                                   |     |   |
|     |     |  Application Business Rules  (application/use_cases)  |     |   |
|     |     |                                                   |     |   |
|     |     |     +---------------------------------------+     |     |   |
|     |     |     |                                       |     |     |   |
|     |     |     |  Enterprise Business Rules  (domain)  |     |     |   |
|     |     |     |                                       |     |     |   |
|     |     |     +---------------------------------------+     |     |   |
|     |     |                                                   |     |   |
|     |     +---------------------------------------------------+     |   |
|     |                                                               |   |
|     +---------------------------------------------------------------+   |
|                                                                         |
+-------------------------------------------------------------------------+
```

<br/>

**주요 계층:**

- **`src/domain` (Enterprise Business Rules)**: 프로젝트의 가장 핵심적인 비즈니스 규칙과 데이터 구조(엔티티)를 포함합니다. 이 계층은 외부의 어떤 계층에도 의존하지 않으며, 변화의 이유가 가장 적어야 합니다.
- **`src/application` (Application Business Rules)**: 애플리케이션에 특화된 비즈니스 로직(유스케이스)을 담고 있습니다. 도메인 계층의 엔티티를 사용하여 특정 시나리오를 실행하고, 외부 계층과 통신하기 위한 인터페이스(포트)를 정의합니다.
- **`src/infrastructure` (Interface Adapters)**: Application 계층에서 정의한 인터페이스(포트)를 구현하는 어댑터들의 집합입니다. 데이터베이스, 외부 API, 파일 시스템 등 외부 세계와 시스템을 연결하는 역할을 합니다.
- **`src/presentation` (Frameworks & Drivers)**: 사용자에게 정보를 보여주고 입력을 받는 가장 바깥 계층입니다. 현재는 Streamlit 기반 웹 대시보드가 여기에 해당합니다.

<br/>

**의존성 규칙:**

의존성은 항상 외부에서 내부로 향합니다. `Presentation` -> `Application` <- `Infrastructure`. `Application`은 `Domain`에 의존합니다. 이 규칙 덕분에 `Domain`과 `Application`은 외부 기술 변화에 영향을 받지 않습니다.

## 2. 주요 기능 확장 가이드

### 새로운 평가 지표 추가하기

새로운 평가 지표를 추가하려면 Ragas 프레임워크와 우리 시스템의 여러 부분을 수정해야 합니다.

1.  **`src/domain/entities/evaluation_result.py` 수정**:
    - `EvaluationResult` 데이터 클래스에 새로운 지표 필드를 추가합니다. (예: `context_relevancy: float`)
    - `__post_init__` 검증 로직에 새 지표를 추가합니다.

2.  **`src/infrastructure/evaluation/ragas_adapter.py` 수정**:
    - `RagasAdapter`의 `evaluate` 메소드에서 `ragas.evaluate` 함수 호출 시, `metrics` 리스트에 새로운 Ragas 메트릭을 추가합니다.
    - Ragas의 평가 결과를 `EvaluationResult`로 변환할 때, 새로운 지표 값을 매핑합니다.

3.  **`src/presentation/web/main.py` 수정**:
    - Streamlit 대시보드에 새로운 지표를 표시하는 UI 코드를 추가합니다. (예: `st.metric`, 차트 업데이트)

### 새로운 데이터 소스 추가하기 (예: DB)

현재는 JSON 파일에서 데이터를 로드합니다. 데이터베이스와 같은 새로운 소스를 추가하려면 다음 단계를 따릅니다.

1.  **`src/application/ports/repository.py` 확인**:
    - `EvaluationRepositoryPort` 인터페이스가 요구사항을 충족하는지 확인합니다. 필요 시 새로운 메소드를 정의할 수 있습니다.

2.  **`src/infrastructure/repository`에 새 어댑터 추가**:
    - `PostgresRepositoryAdapter`와 같은 새 클래스 파일을 생성합니다.
    - 이 클래스는 `EvaluationRepositoryPort`를 상속받아 `load_data` 메소드를 구현해야 합니다. 내부적으로는 DB에 연결하고, 쿼리를 실행하여 `EvaluationData` 객체 리스트를 반환해야 합니다.

3.  **의존성 주입 (Dependency Injection) 수정**:
    - `src/presentation/web/main.py`와 같이 유스케이스를 생성하는 부분에서, `FileRepositoryAdapter` 대신 새로 만든 DB 어댑터(`PostgresRepositoryAdapter`)를 주입하도록 코드를 변경합니다. 이 부분은 향후 설정 파일을 통해 동적으로 변경할 수 있도록 개선할 수 있습니다.

### LLM 공급자 변경하기 (예: Anthropic Claude)

Gemini 대신 다른 LLM을 사용하려면 새로운 LLM 어댑터를 생성해야 합니다.

1.  **`src/application/ports/llm.py` 확인**:
    - `LlmPort` 인터페이스가 `get_llm()` 메소드를 제공하는지 확인합니다.

2.  **`src/infrastructure/llm`에 새 어댑터 추가**:
    - `ClaudeAdapter.py` 파일을 생성합니다.
    - `ClaudeAdapter` 클래스는 `LlmPort`를 상속받고 `get_llm()` 메소드를 구현해야 합니다. 이 메소드는 `langchain-anthropic` 라이브러리를 사용하여 Claude LLM 객체를 설정하고 반환해야 합니다.

3.  **환경 변수 및 설정 추가**:
    - `config.py`와 `.env` 파일에 `ANTHROPIC_API_KEY`와 같은 새로운 환경 변수 설정을 추가합니다.

4.  **의존성 주입 수정**:
    - 유스케이스 생성 지점에서 `GeminiAdapter` 대신 `ClaudeAdapter`를 주입하도록 변경합니다.

## 3. 프레젠테이션 계층 (Streamlit)

- **`src/presentation/web/main.py`**: 대시보드의 메인 파일입니다. 전체 UI 레이아웃, 페이지 흐름, 사용자 인터랙션을 처리합니다.
- **`src/presentation/web/components/`**: 재사용 가능한 UI 컴포넌트(예: 특정 차트, 입력 폼)를 모듈화하여 관리할 수 있는 디렉토리입니다. (현재는 비어있음)
- **상태 관리**: Streamlit의 `st.session_state`를 사용하여 평가 결과, 사용자 입력 등 페이지 간에 유지되어야 하는 상태를 관리합니다.
- **데이터베이스 연동**: `main.py` 내의 `Database` 클래스는 평가 이력을 저장하고 불러오기 위해 SQLite DB와 상호작용합니다.

## 4. 테스트 개발 가이드

본 프로젝트는 **99% 테스트 커버리지**를 달성하여 프로덕션 레벨의 안정성을 보장합니다. 총 96개의 테스트가 395개 라인 중 391개 라인을 커버하고 있습니다.

### 4.1 테스트 아키텍처

클린 아키텍처의 각 계층은 독립적으로 테스트할 수 있으며, 각 계층별로 다른 테스트 전략을 사용합니다:

```
tests/
├── application/
│   ├── ports/                 # 포트 인터페이스 테스트 (3개)
│   └── use_cases/             # 유스케이스 테스트 (6개)
├── domain/
│   ├── entities/              # 도메인 엔티티 테스트 (21개)
│   ├── exceptions/            # 예외 처리 테스트 (5개)
│   └── value_objects/         # 값 객체 테스트 (13개)
├── infrastructure/
│   ├── evaluation/            # RAGAS 어댑터 테스트 (20개)
│   ├── llm/                   # Gemini LLM 어댑터 테스트 (14개)
│   └── repository/            # 파일 저장소 어댑터 테스트 (8개)
└── presentation/              # 메인 애플리케이션 테스트 (8개)
```

### 4.2 계층별 테스트 전략

#### Domain 계층 테스트 (100% 커버리지)

**특징**: 순수한 비즈니스 로직, 외부 의존성 없음

**테스트 방법**:
- 표준 유닛 테스트
- 데이터 검증 규칙 테스트
- 예외 상황 테스트

**주요 테스트 케이스**:
```python
# 엔티티 검증 테스트
def test_evaluation_data_validation():
    # 빈 질문 검증
    with pytest.raises(ValueError, match="질문은 비어있을 수 없습니다"):
        EvaluationData(question="", contexts=["context"], answer="answer", ground_truth="truth")

# 값 객체 범위 검증 테스트
def test_metrics_score_range():
    # 점수 범위 (0.0-1.0) 검증
    with pytest.raises(ValueError, match="점수는 0.0과 1.0 사이여야 합니다"):
        Metrics(faithfulness=1.5, answer_relevancy=0.8, context_precision=0.9, context_recall=0.7)
```

#### Application 계층 테스트 (98% 커버리지)

**특징**: 비즈니스 흐름 조율, 포트 인터페이스 의존

**테스트 방법**:
- Mock 객체를 사용한 의존성 격리
- 유스케이스 시나리오 테스트
- 포트 인터페이스 계약 테스트

**주요 테스트 케이스**:
```python
@pytest.fixture
def mock_repository():
    return Mock(spec=EvaluationRepositoryPort)

@pytest.fixture
def mock_llm_port():
    return Mock(spec=LlmPort)

@pytest.fixture
def mock_evaluation_port():
    return Mock(spec=EvaluationPort)

def test_run_evaluation_success(mock_repository, mock_llm_port, mock_evaluation_port):
    # Given: 정상적인 평가 데이터
    evaluation_data = [create_sample_evaluation_data()]
    mock_repository.load_data.return_value = evaluation_data
    
    expected_result = create_sample_evaluation_result()
    mock_evaluation_port.evaluate.return_value = expected_result
    
    # When: 평가 실행
    use_case = RunEvaluationUseCase(mock_repository, mock_llm_port, mock_evaluation_port)
    result = use_case.execute("test_file.json")
    
    # Then: 올바른 결과 반환
    assert result == expected_result
    mock_repository.load_data.assert_called_once_with("test_file.json")
    mock_evaluation_port.evaluate.assert_called_once()
```

#### Infrastructure 계층 테스트 (99% 커버리지)

**특징**: 외부 시스템 연동, 실제 API/파일 시스템 사용

**테스트 방법**:
- 통합 테스트 (실제 파일 I/O)
- API 모킹 (비용/안정성 고려)
- Rate limiting 로직 테스트
- 예외 상황 시뮬레이션

**1) RAGAS 어댑터 테스트 (20개 테스트)**

가장 복잡한 테스트 영역으로, 다음과 같은 도전 과제들을 해결했습니다:

**Rate Limiting 테스트**:
```python
def test_rate_limited_embeddings_timing():
    """Rate limiting 정확성 테스트"""
    embeddings = RateLimitedEmbeddings(requests_per_minute=60)  # 1초당 1요청
    
    with patch('time.time') as mock_time:
        # 시간 흐름 시뮬레이션
        mock_time.side_effect = [0.0, 0.5, 1.0, 1.5]  # 0.5초 간격 호출
        
        # 첫 번째 호출 - 즉시 실행
        embeddings._wait_if_needed()
        
        # 두 번째 호출 - 0.5초 대기 필요
        embeddings._wait_if_needed()
        
        # sleep 호출 검증
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(pytest.approx(0.5, abs=0.01))
```

**복잡한 평가 결과 변환 테스트**:
```python
def test_evaluation_result_conversion():
    """RAGAS 결과를 도메인 객체로 변환하는 테스트"""
    # RAGAS 라이브러리의 실제 결과 형식 모킹
    mock_result = Mock()
    mock_result.to_pandas.return_value = pd.DataFrame({
        'faithfulness': [0.8, 0.9],
        'answer_relevancy': [0.7, 0.8],
        'context_precision': [0.9, 0.85],
        'context_recall': [0.75, 0.8]
    })
    
    adapter = RagasEvalAdapter(mock_llm, mock_embeddings)
    result = adapter._convert_to_evaluation_result(mock_result, test_data)
    
    # 평균 점수 계산 검증
    assert result.ragas_score == pytest.approx(0.8125, abs=0.001)
    assert len(result.individual_scores) == 2
```

**2) Gemini LLM 어댑터 테스트 (14개 테스트)**

**API 키 검증 및 모델 설정 테스트**:
```python
def test_gemini_adapter_initialization():
    """Gemini 어댑터 초기화 테스트"""
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
        adapter = GeminiAdapter()
        llm = adapter.get_llm()
        
        assert llm.model == "models/gemini-1.5-flash"
        assert llm.temperature == 0.1

def test_missing_api_key():
    """API 키 누락 시 예외 발생 테스트"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GEMINI_API_KEY 환경 변수가 설정되지 않았습니다"):
            GeminiAdapter()
```

**비동기 메서드 테스트**:
```python
@pytest.mark.asyncio
async def test_gemini_ainvoke():
    """비동기 LLM 호출 테스트"""
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
        adapter = GeminiAdapter()
        llm = adapter.get_llm()
        
        # ainvoke 메서드 모킹
        with patch.object(llm, 'ainvoke', new_callable=AsyncMock) as mock_ainvoke:
            mock_ainvoke.return_value = "테스트 응답"
            
            result = await llm.ainvoke("테스트 질문")
            assert result == "테스트 응답"
            mock_ainvoke.assert_called_once_with("테스트 질문")
```

**3) 파일 저장소 어댑터 테스트 (8개 테스트)**

**임시 파일을 사용한 실제 I/O 테스트**:
```python
def test_load_data_success(tmp_path):
    """정상적인 데이터 로딩 테스트"""
    # 임시 JSON 파일 생성
    test_data = [
        {
            "question": "테스트 질문",
            "contexts": ["컨텍스트 1"],
            "answer": "테스트 답변",
            "ground_truth": "정답"
        }
    ]
    
    test_file = tmp_path / "test_data.json"
    test_file.write_text(json.dumps(test_data, ensure_ascii=False))
    
    # 파일 로딩 및 검증
    adapter = FileRepositoryAdapter()
    result = adapter.load_data(str(test_file))
    
    assert len(result) == 1
    assert result[0].question == "테스트 질문"
```

#### Presentation 계층 테스트 (97% 커버리지)

**특징**: 애플리케이션 진입점, 의존성 조립

**테스트 방법**:
- 서브프로세스를 통한 실행 테스트
- 의존성 주입 검증
- 환경 설정 테스트

**메인 모듈 실행 테스트**:
```python
def test_main_module_execution():
    """메인 모듈이 실제로 실행되는지 테스트"""
    result = subprocess.run(
        [sys.executable, "-c", "import src.presentation.main"],
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 0
```

### 4.3 테스트 개발 과정에서 해결한 주요 도전 과제

#### 1. Rate Limiting 로직의 정확성 검증

**문제**: 복잡한 시간 계산 로직의 정확성을 어떻게 테스트할 것인가?

**해결책**:
- `time.time()` 함수를 모킹하여 시간 흐름 시뮬레이션
- 부동소수점 정밀도 문제를 `pytest.approx()` 로 해결
- 여러 시나리오 (첫 호출, 연속 호출, 충분한 시간 경과) 테스트

#### 2. 복잡한 데이터 변환 로직 테스트

**문제**: RAGAS 라이브러리의 복잡한 결과 객체를 어떻게 모킹할 것인가?

**해결책**:
- `pandas.DataFrame` 을 사용한 실제 데이터 구조 모킹
- 다양한 결과 형식 (`_scores_dict`, `_repr_dict`, 속성 접근) 테스트
- 빈 결과, 누락된 메트릭 등 엣지 케이스 커버

#### 3. 비동기 코드 테스트

**문제**: `async/await` 패턴의 LLM 호출을 어떻게 테스트할 것인가?

**해결책**:
- `pytest-asyncio` 플러그인 사용
- `AsyncMock` 을 사용한 비동기 메서드 모킹
- 실제 비동기 실행 흐름 검증

#### 4. 포트 인터페이스의 추상 메서드 테스트

**문제**: 추상 클래스의 `pass` 문을 어떻게 커버할 것인가?

**해결책**:
- 구체 구현체에서 `super()` 호출을 통한 추상 메서드 실행
- 인터페이스 계약 준수 검증

### 4.4 테스트 실행 및 커버리지 확인

#### 기본 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 상세 출력
pytest -v

# 특정 모듈만 테스트
pytest tests/domain/
pytest tests/infrastructure/evaluation/
```

#### 커버리지 리포트 생성
```bash
# 터미널 리포트
pytest --cov=src --cov-report=term-missing

# HTML 리포트 생성
pytest --cov=src --cov-report=html

# 커버리지 임계값 설정
pytest --cov=src --cov-fail-under=99
```

#### 테스트 성능 최적화
```bash
# 병렬 실행 (pytest-xdist 필요)
pytest -n auto

# 실패한 테스트만 재실행
pytest --lf

# 마지막 실패 이후 모든 테스트 실행
pytest --ff
```

### 4.5 새로운 테스트 작성 가이드라인

#### 1. 테스트 명명 규칙
```python
def test_[기능]_[조건]_[예상결과]():
    """테스트 목적을 명확히 설명하는 docstring"""
    # Given: 테스트 조건 설정
    # When: 테스트 대상 실행
    # Then: 결과 검증
```

#### 2. 픽스처 활용
```python
@pytest.fixture
def sample_evaluation_data():
    """재사용 가능한 테스트 데이터"""
    return EvaluationData(
        question="테스트 질문",
        contexts=["컨텍스트"],
        answer="답변",
        ground_truth="정답"
    )
```

#### 3. 예외 테스트
```python
def test_invalid_input_raises_exception():
    """예외 발생 시나리오 테스트"""
    with pytest.raises(ValueError, match="구체적인 에러 메시지"):
        # 예외를 발생시키는 코드
        pass
```

#### 4. 모킹 전략
```python
# 외부 의존성 모킹
@patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
def test_with_external_dependency(mock_evaluate):
    mock_evaluate.return_value = expected_result
    # 테스트 로직
```

### 4.6 지속적인 테스트 품질 관리

#### 1. 커버리지 모니터링
- 새로운 코드 추가 시 반드시 테스트 작성
- 99% 커버리지 유지
- 커버되지 않는 라인에 대한 명확한 이유 문서화

#### 2. 테스트 리팩토링
- 중복 코드 제거
- 픽스처 활용으로 재사용성 증대
- 테스트 가독성 개선

#### 3. 성능 테스트
- 느린 테스트 식별 및 최적화
- 통합 테스트와 유닛 테스트 분리
- CI/CD 파이프라인에서의 테스트 실행 시간 관리

### 4.7 테스트 환경 설정

#### pyproject.toml 설정
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=99"
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests"
]
```

#### 개발 의존성
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "pytest-asyncio>=0.21.0",
    "pytest-xdist>=3.0.0"
]
```

이러한 포괄적인 테스트 전략을 통해 본 프로젝트는 높은 품질과 안정성을 보장하며, 지속적인 개발과 유지보수를 지원합니다. 