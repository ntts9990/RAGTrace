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

## 4. 테스트

각 계층은 독립적으로 테스트할 수 있습니다.

- **Domain**: 순수 함수와 클래스이므로 표준 유닛 테스트로 쉽게 테스트할 수 있습니다.
- **Application**: 모의(Mock) 리포지토리 및 LLM 어댑터를 주입하여 유스케이스의 로직을 테스트할 수 있습니다.
- **Infrastructure**: 실제 외부 시스템(API, DB)과 연동하여 통합 테스트를 수행해야 합니다. API 키와 같은 민감 정보는 테스트 환경에서 별도로 관리해야 합니다.

### 테스트 실행

테스트를 실행하기 전에, 개발용 의존성을 설치해야 합니다.

```bash
uv pip install -e .[dev]
```

그 후, 프로젝트 루트 디렉토리에서 다음 명령어로 모든 테스트를 실행할 수 있습니다.

```bash
pytest
```

### 테스트 전략

- **Domain 계층**: 이 계층은 순수한 비즈니스 로직을 담고 있으므로, 외부 의존성 없이 표준 유닛 테스트로 검증합니다. `pytest`를 사용하여 엔티티의 생성, 유효성 검사 규칙 등을 테스트합니다. (`tests/domain/` 참조)

- **Application 계층**: 유스케이스는 여러 포트에 의존합니다. 이 의존성을 `pytest-mock`을 사용하여 모의(Mock) 객체로 대체하여 테스트합니다. 이를 통해 외부 시스템의 상태와 관계없이 유스케이스의 비즈니스 로직 흐름이 올바른지만을 고립하여 검증할 수 있습니다. (`tests/application/` 참조)

- **Infrastructure 계층**: 어댑터는 실제 외부 기술과 연동되므로, 이는 통합 테스트의 성격을 가집니다.
  - **파일 어댑터**: `pytest`의 `tmp_path` fixture를 사용하여 임시 파일을 생성하고, 실제 파일 I/O를 테스트합니다.
  - **API 어댑터 (LLM 등)**: 실제 API를 호출하는 테스트는 비용이 발생하고 외부 상태에 의존적이므로, 일반적으로 CI 환경에서는 실행하지 않도록 `@pytest.mark.skip` 등으로 표시하거나, 모의 API 서버(Pact, WireMock 등)를 사용하는 전략을 고려할 수 있습니다. 현재 프로젝트에서는 핵심 로직 테스트에 집중합니다.
  - **DB 어댑터**: 테스트용 인메모리 DB(예: SQLite `:memory:`)나 테스트 전용 Docker 컨테이너를 사용하여 DB 연동을 테스트할 수 있습니다. 