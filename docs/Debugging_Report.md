# RAGTrace 프로젝트 디버깅 보고서

## 1. 개요

본 문서는 현재 RAGTrace 프로젝트의 `pytest` 테스트 스위트에서 발견된 8개의 실패 항목에 대한 상세 분석 및 해결 방안을 제시합니다. 기능 추가 과정에서 발생한 것으로 보이는 이 오류들은 애플리케이션의 핵심 기능인 **의존성 주입**, **웹 대시보드 컴포넌트 렌더링**, **데이터 처리** 등 다방면에 걸쳐 영향을 미치고 있습니다.

본 보고서는 각 문제의 원인을 기능적 관점에서 분석하고, 명확한 소스 코드 수정 방안을 제안하여 프로젝트의 안정성을 회복하는 것을 목표로 합니다.

---

## 2. 핵심 기능 장애 분석 및 해결 방안

### 2.1. 의존성 주입 컨테이너(`Container`) 기능 장애

**가장 시급하고 중대한 문제**로, 애플리케이션의 모든 구성요소를 생성하고 연결하는 `Container` 클래스가 정상적으로 동작하지 않고 있습니다. 이로 인해 애플리케이션의 시작 및 유스케이스 실행이 불가한 상태입니다.

-   **장애 지점**: `src/container.py`, `tests/test_container.py`
-   **관련 테스트 실패**: 5건

#### 상세 분석 및 해결 방안

**[문제 1] 유스케이스 생성 불가 (`AttributeError`)**

-   **기능 장애**: `Container`가 `RunEvaluation` 유스케이스 인스턴스를 생성하여 제공하는 핵심 기능을 수행하지 못합니다.
-   **원인**: `Container` 클래스에 유스케이스를 반환하는 `get_evaluation_use_case` 메서드가 존재하지 않습니다. 테스트 코드(`test_container_get_evaluation_use_case`, `test_container_with_file_repository`)에서 해당 메서드를 호출하려다 `AttributeError`가 발생했습니다.
-   **수정 제안**:
    -   **파일**: `src/container.py`
    -   **내용**: `Container` 클래스 내부에 아래와 같이 `get_evaluation_use_case` 메서드를 추가하여, 필요한 어댑터들을 주입한 `RunEvaluation` 인스턴스를 생성하고 반환하도록 구현해야 합니다.

    ```python
    # src/container.py 내 Container 클래스에 추가

    from .application.use_cases import RunEvaluation
    # ...

    class Container:
        def __init__(self):
            # ... 어댑터 초기화 로직 ...

        # 아래 메서드 추가
        def get_evaluation_use_case(self) -> RunEvaluation:
            return RunEvaluation(
                llm_adapter=self.llm_adapter,
                evaluation_adapter=self.evaluation_adapter,
                repository=self.repository,
            )
    ```

**[문제 2] 잘못된 Mocking 전략으로 인한 테스트 오작동 (`AssertionError`)**

-   **기능 장애**: `Container`가 `GeminiAdapter`를 올바르게 초기화하는지, 설정에 따라 적절히 구성되는지를 검증하는 테스트가 모두 실패하고 있습니다.
-   **원인**: `tests/test_container.py`에서 `unittest.mock.patch`의 **대상 경로가 잘못 지정**되었습니다. `patch`는 객체가 정의된 위치가 아니라 **사용되는 위치**를 기준으로 경로를 지정해야 합니다. `container.py` 모듈이 `GeminiAdapter`를 `import`하여 사용하므로, `patch` 대상은 `'src.container.GeminiAdapter'`가 되어야 합니다. 현재는 원본 경로(`'src.infrastructure.llm.gemini_adapter.GeminiAdapter'`)를 대상으로 하고 있어 Mock 객체가 실제 `Container` 초기화 로직에 적용되지 못했습니다.
-   **수정 제안**:
    -   **파일**: `tests/test_container.py`
    -   **내용**: 파일 내 모든 `patch` 구문의 대상 경로를 아래와 같이 수정해야 합니다.

    ```python
    # tests/test_container.py 수정 예시

    # 변경 전
    # with patch('src.infrastructure.llm.gemini_adapter.GeminiAdapter') as mock_gemini:

    # 변경 후
    # from src import container # 상단에 import 추가
    # with patch('src.container.GeminiAdapter') as mock_gemini:
    # 또는, from 문을 사용하지 않고 전체 경로 명시
    # with patch('src.container.GeminiAdapter') as mock_gemini:
    ```
    *참고: `RagasEvalAdapter`, `FileRepositoryAdapter` 등 다른 patch 대상도 동일한 원칙으로 수정이 필요할 수 있습니다.*

**[문제 3] 불일치하는 예외 메시지 (`AssertionError`)**

-   **기능 장애**: 설정(API 키) 누락 시 `Container`가 올바른 예외를 발생시키는지 검증하는 테스트가 실패합니다.
-   **원인**: `test_container_with_missing_config` 테스트는 영문 오류 메시지(`"API key is required"`)를 기대하지만, 실제 `GeminiAdapter`는 한글 오류 메시지(`"GEMINI_API_KEY가 설정되지 않았습니다."`)를 발생시킵니다.
-   **수정 제안**:
    -   **파일**: `tests/test_container.py`
    -   **내용**: `pytest.raises`의 `match` 인자를 실제 발생하는 한글 오류 메시지로 변경해야 합니다.

    ```python
    # tests/test_container.py 수정 예시

    # 변경 전
    # with pytest.raises(ValueError, match="API key is required"):

    # 변경 후
    with pytest.raises(ValueError, match="GEMINI_API_KEY가 설정되지 않았습니다."):
        Container()
    ```

---

### 2.2. 웹 대시보드 컴포넌트 기능 장애

대시보드를 구성하는 각 페이지 컴포넌트의 데이터 처리 및 렌더링 로직에 문제가 발생하여 정상적인 UI 표시가 어렵습니다.

**[문제 1] 상세 분석 페이지: 데이터 검증 로직 오류 (`NameError`)**

-   **기능 장애**: 평가 결과의 상세 분석을 위한 데이터 유효성 검증 기능이 동작하지 않습니다.
-   **원인**: `tests/presentation/web/components/test_detailed_analysis.py`의 `test_data_validation_functions` 함수 내부에, 테스트 흐름과 무관하며 정의되지 않은 `distribution` 변수를 참조하는 불필요한 코드가 남아있어 `NameError`를 발생시킵니다.
-   **수정 제안**:
    -   **파일**: `tests/presentation/web/components/test_detailed_analysis.py`, 296번째 줄
    -   **내용**: 아래 코드 라인을 완전히 삭제해야 합니다.
    ```python
    # 삭제할 라인
    for metric_stats in distribution.values():
    ```

**[문제 2] 성능 모니터링 페이지: 데이터 로딩 실패 (`AssertionError`)**

-   **기능 장애**: 과거 평가 이력을 불러와 성능 추이를 보여주는 `PerformanceMonitor` 컴포넌트가 데이터를 로드하지 못합니다.
-   **원인**: 테스트 코드(`test_load_evaluation_history_for_performance_success`)는 `sqlite3.connect`를 모킹했지만, 실제 `load_evaluation_history_for_performance` 함수는 `pandas.read_sql_query`를 사용하여 데이터베이스와 상호작용할 가능성이 높습니다 (pytest 경고 메시지에서 `pandas` 사용 암시). 모킹이 실제 데이터 로드 로직을 가로채지 못하여 빈 리스트(`[]`)가 반환되었고, `assert len(result) == 1`이 실패했습니다.
-   **수정 제안**:
    -   **파일**: `tests/presentation/web/components/test_performance_monitor.py`
    -   **내용**: `sqlite3.connect` 모킹을 제거하고, `pandas.read_sql_query`를 직접 모킹하여 테스트용 `DataFrame` 객체를 반환하도록 수정해야 합니다.

    ```python
    # tests/presentation/web/components/test_performance_monitor.py 수정 예시
    from unittest.mock import patch
    import pandas as pd

    # ...
    # @patch('sqlite3.connect') # 이 부분 삭제
    @patch('pandas.read_sql_query')
    def test_load_evaluation_history_for_performance_success(self, mock_read_sql):
        # mock DataFrame 생성
        mock_df = pd.DataFrame([{
            'id': 1, 'evaluated_at': '2024-01-01 10:00:00',
            'faithfulness': 0.95, 'answer_relevancy': 0.90,
            # ... 기타 필드
        }])
        mock_read_sql.return_value = mock_df

        # ... 테스트 로직 ...
        result = load_evaluation_history_for_performance()
        assert len(result) == 1
    ```

**[문제 3] 메인 대시보드 페이지: 부동소수점 연산 오류 (`AssertionError`)**

-   **기능 장애**: 평가 결과의 평균 점수를 계산하고 표시하는 로직이 정확하지 않습니다.
-   **원인**: `tests/presentation/web/test_main.py`의 `test_data_processing_functions` 함수에서 부동소수점 연산으로 인한 미세한 오차(`0.8500000000000001`)가 발생하여, 정확한 값(`0.85`)과의 비교가 실패했습니다.
-   **수정 제안**:
    -   **파일**: `tests/presentation/web/test_main.py`, 203번째 줄
    -   **내용**: 정확한 값 비교 대신 `pytest.approx`를 사용하여 근사치 비교를 수행하도록 수정해야 합니다.

    ```python
    # tests/presentation/web/test_main.py 수정 예시
    import pytest

    # 변경 전
    # assert processed["avg_ragas_score"] == 0.85

    # 변경 후
    assert processed["avg_ragas_score"] == pytest.approx(0.85)
    ```

---

## 3. 결론

현재 발생한 8개의 테스트 실패는 **의존성 주입 컨테이너의 설정 오류**와 **웹 컴포넌트 테스트의 부정확한 모킹 및 단언(assertion) 방식**에 기인합니다. 특히 `Container` 관련 문제는 애플리케이션의 근간을 흔드는 심각한 오류이므로 최우선으로 해결해야 합니다.

위에 제안된 해결 방안들을 순서대로 적용하면 모든 테스트가 통과하고, 프로젝트의 핵심 기능들이 안정적으로 동작하는 상태로 복구될 것으로 기대됩니다. 