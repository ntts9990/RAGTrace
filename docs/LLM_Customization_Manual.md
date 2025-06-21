# LLM 커스터마이징 매뉴얼

## 1. 개요

이 문서는 RAGTrace 프로젝트에서 기본으로 설정된 Gemini 이외의 다른 대규모 언어 모델(LLM)을 사용하고자 할 때, 필요한 코드 수정 및 설정 방법을 안내합니다. 본 프로젝트는 **'Ports and Adapters' (Hexagonal Architecture)** 설계를 채택하여, 핵심 로직의 변경 없이 새로운 LLM을 쉽게 추가하고 교체할 수 있습니다.

이 매뉴얼에서는 예시로 네이버의 HyperCLOVA X (HCX)를 통합하는 과정을 설명하지만, 다른 어떤 LLM API에도 동일한 원리를 적용할 수 있습니다.

---

## 2. 핵심 아키텍처 이해: Ports and Adapters

-   **Port (포트)**: `src/application/ports/llm_port.py`에 정의된 `LlmPort` 인터페이스입니다. 애플리케이션의 핵심 로직(유스케이스)은 이 추상적인 포트에만 의존합니다. 포트는 'LLM이라면 마땅히 `generate_answer`와 같은 기능을 수행해야 한다'는 계약을 정의합니다.

-   **Adapter (어댑터)**: `LlmPort`라는 계약을 실제로 구현한 클래스입니다. `src/infrastructure/llm/gemini_adapter.py`의 `GeminiAdapter`가 기본 어댑터입니다. 새로운 LLM을 추가하려면, 이 `LlmPort`를 상속받는 새로운 어댑터 클래스를 작성하기만 하면 됩니다.

---

## 3. 새로운 LLM 어댑터 추가 단계 (예: HyperCLOVA X)

### 단계 1: 새로운 어댑터 클래스 생성

1.  `src/infrastructure/llm/` 디렉토리 아래에 `hcx_adapter.py`와 같은 새 파일을 생성합니다.

2.  `hcx_adapter.py` 파일 안에, `LlmPort`를 상속받는 새로운 어댑터 클래스(예: `HcxAdapter`)를 작성합니다. 이 클래스는 `LlmPort`에 정의된 모든 추상 메서드(`generate_answer`, `get_llm`)를 반드시 구현해야 합니다.

    ```python
    # src/infrastructure/llm/hcx_adapter.py

    from langchain_core.language_models import BaseLLM
    from langchain_core.outputs import LLMResult

    from src.application.ports import LlmPort

    # HCX 연동을 위한 LangChain 커뮤니티 패키지가 있다면 import
    # from langchain_community.llms import HyperClovaX

    class HcxAdapter(LlmPort):
        """HyperCLOVA X를 위한 LlmPort 어댑터"""

        def __init__(self, api_key: str, model_name: str, **kwargs):
            # HCX SDK 또는 LangChain 통합 라이브러리를 사용하여 LLM 인스턴스 초기화
            # 아래 코드는 예시이며, 실제 HCX 라이브러리의 사용법에 맞게 수정해야 합니다.
            # self._llm = HyperClovaX(
            #     ncp_clova_api_key=api_key,
            #     model=model_name,
            #     ...kwargs
            # )
            print("HCX Adapter is being initialized (This is a placeholder).")
            # 실제 LLM 객체 대신 임시 객체를 설정합니다. 실제 구현 시 이 부분을 수정해야 합니다.
            self._llm = self._create_placeholder_llm()

        def generate_answer(self, question: str, contexts: list[str]) -> str:
            """
            HCX를 사용하여 질문과 컨텍스트에 기반한 답변을 생성합니다.
            실제 HCX 라이브러리의 API 호출 방식에 맞게 구현해야 합니다.
            """
            prompt = self._create_prompt(question, contexts)
            # result = self._llm.invoke(prompt)
            # return result.content
            return f"This is a placeholder answer from HCX for the question: {question}"

        def get_llm(self) -> BaseLLM:
            """초기화된 LLM 객체를 반환합니다."""
            return self._llm

        def _create_prompt(self, question: str, contexts: list[str]) -> str:
            """LLM에 전달할 프롬프트를 생성하는 내부 헬퍼 메서드"""
            context_str = "\n".join(f"- {ctx}" for ctx in contexts)
            return f"""
            Based on the following context, please provide a precise and relevant answer to the question.

            Contexts:
            {context_str}

            Question:
            {question}

            Answer:
            """
        
        def _create_placeholder_llm(self) -> BaseLLM:
            """실제 LLM 라이브러리 없이 테스트하기 위한 임시 LLM 객체"""
            class PlaceholderLLM(BaseLLM):
                def _llm_type(self) -> str:
                    return "placeholder-hcx"
                def _generate(self, prompts, stop=None, run_manager=None, **kwargs) -> LLMResult:
                    generations = [[{"text": f"Placeholder answer for: {p}"}] for p in prompts]
                    return LLMResult(generations=generations)
                async def _agenerate(self, prompts, stop=None, run_manager=None, **kwargs) -> LLMResult:
                    return self._generate(prompts, stop, run_manager, **kwargs)

            return PlaceholderLLM()
    ```

### 단계 2: 환경 변수 및 설정 추가

1.  `.env` 파일에 새로 추가한 LLM(HCX)에 필요한 환경 변수를 정의합니다.
    ```env
    # .env
    # ... 기존 Gemini 설정 ...

    # HyperCLOVA X 설정
    HCX_API_KEY="YOUR_HCX_API_KEY"
    HCX_MODEL_NAME="HCX-005"
    ```

2.  `src/config.py` 파일에 새로운 설정 값을 읽어오는 코드를 추가합니다.
    ```python
    # src/config.py
    # ...
    class Settings(BaseSettings):
        # ... 기존 설정 ...

        # HCX Settings
        HCX_API_KEY: str = "default_hcx_key"
        HCX_MODEL_NAME: str = "default_hcx_model"

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"

    settings = Settings()
    ```

### 단계 3: 의존성 주입 컨테이너 수정

`src/container.py` 파일에서 어떤 어댑터를 사용할지 결정합니다. 이것이 아키텍처의 핵심입니다. `GeminiAdapter`를 `HcxAdapter`로 교체하기만 하면, 애플리케이션의 다른 모든 부분은 변경 없이 새 LLM을 사용하게 됩니다.

1.  새로 만든 어댑터를 import 합니다.
    ```python
    # src/container.py
    # from src.infrastructure.llm.gemini_adapter import GeminiAdapter
    from src.infrastructure.llm.hcx_adapter import HcxAdapter
    ```

2.  `Container` 클래스의 `__init__` 메서드에서 `llm_adapter`를 생성하는 부분을 수정합니다.

    ```python
    # src/container.py
    class Container:
        def __init__(self):
            # ...
            
            # self.llm_adapter: LlmPort = GeminiAdapter(...) # 기존 코드
            
            # 아래 코드로 교체
            self.llm_adapter: LlmPort = HcxAdapter(
                api_key=self.settings.HCX_API_KEY,
                model_name=self.settings.HCX_MODEL_NAME,
            )

            # ... 나머지 코드는 동일 ...
    ```

### 단계 4: 실행 및 확인

모든 수정이 완료되었다면, 평소와 같이 애플리케이션을 실행합니다.

```bash
python -m src.main --dataset_name your_dataset_name
```

이제 RAGTrace는 내부적으로 Gemini 대신 새로 추가한 `HcxAdapter`를 통해 LLM API를 호출하여 평가를 수행합니다.

---

## 4. 결론

이러한 분리된 아키텍처 덕분에, 새로운 기술을 도입하거나 외부 서비스를 교체하는 작업이 매우 간단하고 안전해집니다. `LlmPort`라는 '계약'만 준수한다면, 어떤 종류의 LLM이든 RAGTrace 시스템에 손쉽게 통합할 수 있습니다. 