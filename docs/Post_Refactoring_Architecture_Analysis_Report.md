# RAGTrace 프로젝트 상태 분석 및 리팩토링 계획

**문서 버전: 1.0**
**작성일: 2024-05-21**
**작성자: AI Assistant**

---

## 1. 개요

이 문서는 `refactor/architecture-improvement` 브랜치에 있는 RAGTrace 프로젝트의 현재 아키텍처 상태를 정밀하게 분석하고, 반복적으로 발생하는 런타임 오류의 근본 원인을 진단하여, 시스템의 안정성과 유지보수성을 향상시키기 위한 구체적인 리팩토링 실행 계획을 제안하는 것을 목적으로 한다.

## 2. 현 상태 분석: 빛과 그림자

프로젝트는 클린 아키텍처를 지향하며 계층 분리를 시도했으나, 일부 계층 간의 상호작용 방식에 불일치가 존재하며 이것이 현재 문제의 핵심 원인이다.

### 2.1. 도메인 계층 (Domain Layer) - `src/domain`

-   **역할**: 비즈니스의 핵심 규칙과 데이터 구조(Entities, Value Objects)를 정의.
-   **분석**: `EvaluationData`, `EvaluationResult`, `Metrics` 등 핵심 객체들이 잘 정의되어 있다. 외부 계층에 대한 의존성이 없으며, 안정적인 비즈니스 로직의 기반을 잘 형성하고 있다.
-   **평가**: **매우 건강 (Healthy)**. 프로젝트에서 가장 안정적이고 잘 설계된 부분이다.

### 2.2. 애플리케이션 계층 (Application Layer) - `src/application`

-   **역할**: 시스템의 유스케이스(Use Cases)를 정의하고, 도메인 객체를 사용하여 비즈니스 로직을 오케스트레이션한다.
-   **분석**:
    -   `RunEvaluationUseCase`가 핵심적인 역할을 수행한다.
    -   `execute` 메소드의 시그니처(호출 방식)는 `execute(self, dataset_name: str, ...)` 형태일 것으로 강력히 추정된다. (최신 오류 로그 `got an unexpected keyword argument 'dataset_path'`가 결정적 증거)
    -   이 계층은 도메인에만 의존해야 한다는 원칙을 잘 따르고 있으나, 자신을 호출하는 상위 계층(프레젠테이션)과의 '계약'이 깨져있다.
-   **평가**: **대체로 건강 (Mostly Healthy)**. 자체 로직은 견고하나, 외부와의 인터페이스 약속이 명확하게 관리되지 않고 있다.

### 2.3. 인프라 계층 (Infrastructure Layer) - `src/infrastructure`

-   **역할**: 데이터베이스, 외부 API, 파일 시스템 등 외부 세계와의 통신을 담당.
-   **분석**: `repository/file_adapter.py`는 `dataset_name`을 받아 `data/` 디렉토리에서 파일을 찾는 로직을 포함할 것이며, `evaluation/ragas_adapter.py`는 RAGAS 라이브러리와의 연동을 담당한다. 이들은 애플리케이션 계층의 포트(인터페이스)를 구현하는 형태로 잘 분리되어 있다.
-   **평가**: **건강 (Healthy)**. 의존성 역전 원칙이 잘 적용되어 있다.

### 2.4. 프레젠테이션 계층 (Presentation Layer) - `src/presentation`, `cli.py`

-   **역할**: 사용자(사람 또는 다른 시스템)와의 상호작용을 처리.
-   **분석**:
    -   **현재 모든 문제의 근원지이다.**
    -   **`cli.py`는 리팩토링 과정에서 완전히 뒤처져, 과거의 유물(Legacy) 코드로 남아있다.**
    -   **(증상 1) 계약 위반**: `RunEvaluationUseCase`의 `execute` 메소드가 `dataset_name`을 기대함에도 불구하고, `cli.py`는 `dataset_path`라는 존재하지 않는 인자를 전달하려 시도했다. 이는 두 계층 간의 약속(API Signature)이 깨졌다는 명백한 증거다.
    -   **(증상 2) 잘못된 의존성 관리**: 이전 오류 로그(`__init__() missing ... arguments`, `has no attribute 'evaluation_use_case_factory'`)들은 `cli.py`가 의존성 주입 컨테이너를 올바르게 사용하지 않고, 과거의 방식으로 직접 객체를 생성하거나 잘못된 이름으로 접근하려 했음을 보여준다.
-   **평가**: **심각하게 불안정 (Unhealthy)**. 아키텍처 개선의 가장 시급한 대상이다.

## 3. 근본 원인: "깨진 계약"

**점진적 리팩토링 과정에서 발생한 프레젠테이션 계층과 애플리케이션 계층 간의 인터페이스 불일치(Interface Mismatch)**가 모든 문제의 근본 원인이다.

`RunEvaluationUseCase`는 더 이상 파일의 '경로'를 직접 받지 않고, 데이터셋의 '이름'을 받아 리포지토리를 통해 데이터를 찾는 방식으로 변경되었지만, 이를 호출하는 `cli.py`는 이 변경사항을 전혀 인지하지 못하고 있다. 이는 마치 API 서버의 엔드포인트 사양이 변경되었는데, 클라이언트는 예전 사양으로 계속 호출하는 것과 같은 상황이다.

## 4. 실행 계획: 계약의 재정립과 이행

### 4.1. Phase 1: `cli.py` 완전 재정비

**목표: `cli.py`가 애플리케이션 계층의 '공식적인 클라이언트'로서의 역할을 올바르게 수행하도록 전면 수정한다.**

-   **액션 1.1: `RunEvaluationUseCase` 호출 방식 수정**
    -   `evaluate_dataset` 함수 내에서 `evaluation_use_case.execute()`를 호출하는 부분을 아래와 같이 수정한다.
    -   **변경 전 (오류 원인):** `execute(dataset_path=str(data_path), ...)`
    -   **변경 후 (올바른 방식):** `execute(dataset_name=dataset_name, ...)`
    -   **이유**: `RunEvaluationUseCase`는 이제 파일 시스템의 세부 정보(`path`)를 알 필요가 없다. 단지 데이터셋의 논리적인 `name`만 받아서, 데이터 접근은 리포지토리에게 위임하는 것이 클린 아키텍처의 원칙에 부합한다.

-   **액션 1.2: 데이터 준비 로직 수정**
    -   `evaluate_dataset` 함수에서 `get_evaluation_data_path(dataset_name)`를 호출하는 로직을 재검토한다.
    -   `cli.py`는 더 이상 파일 경로를 직접 다루지 않으므로, 이 함수는 데이터 존재 유무를 확인하는 용도로만 사용하거나, 혹은 `dataset_name`만 `execute` 메소드로 넘겨주고 파일 존재 여부 확인은 애플리케이션 계층 내부에서 처리하도록 위임하는 것이 더 나은 구조다.
    -   우선은 `dataset_name`만 정확히 전달하는 데 집중한다.

### 4.2. Phase 2: 테스트 및 검증

-   **액션 2.1: 테스트 시나리오 재실행**
    1.  `test_run/sample_data.json` 파일을 `data/` 디렉토리로 **복사**한다 (`cp test_run/sample_data.json data/`).
    2.  수정된 `cli.py`를 통해 **이름만으로** 평가를 실행한다:
        ```bash
        .venv/bin/python cli.py evaluate sample_data.json --llm gemini --embedding bge_m3 --output test_run/evaluation_results.json
        ```
-   **액션 2.2: 결과 확인**
    -   `test_run/evaluation_results.json` 파일이 정상적으로 생성되고, 내부에 유효한 평가 결과가 담겨 있는지 확인한다.

### 4.3. Phase 3: 정리

-   **액션 3.1: 테스트 환경 원상복구**
    -   테스트가 성공적으로 완료되면, `data/` 디렉토리에 복사했던 임시 파일(`sample_data.json`)을 삭제하여 프로젝트를 깨끗한 상태로 유지한다.

## 5. 기대 효과

-   **안정성 향상**: 런타임 오류의 근본 원인을 해결하여, CLI 기능이 예측 가능하고 안정적으로 동작하게 된다.
-   **유지보수성 증대**: 각 계층의 역할과 책임이 명확해지고, 계층 간의 계약(API)이 통일되어 향후 기능 추가 및 수정이 용이해진다.
-   **아키텍처 완성도 제고**: `refactor/architecture-improvement` 브랜치의 본래 목적에 맞게, 프로젝트 전체가 일관된 아키텍처 원칙을 따르게 된다.

---

**분석자**: Claude Code  
**분석 완료일**: 2025-06-22  
**리포트 버전**: 1.0