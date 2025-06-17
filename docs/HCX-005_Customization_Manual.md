# RAGTrace 프로젝트 HCX-005 커스터마이징 개발 매뉴얼

이 문서는 기존 RAGTrace 프로젝트를 폐쇄망 환경으로 이전하고, 핵심 언어 모델을 Naver Cloud의 HyperCLOVA X (HCX-005)로 교체하는 전체 과정을 안내합니다.

### **목표**

1.  **폐쇄망 환경 구축**: 인터넷 연결 없이 프로젝트를 실행할 수 있도록 모든 의존성을 패키징합니다.
2.  **LLM 교체**: 기존 `GeminiAdapter`를 HCX-005 API와 통신하는 `HcxAdapter`로 교체합니다.
3.  **안정적인 실행**: 변경된 환경에서 RAG 평가 시스템이 정상적으로 동작하도록 설정하고 검증합니다.

---

### **Phase 1: 사전 준비 (외부망 환경)**

폐쇄망으로 프로젝트를 이전하기 전, 인터넷이 가능한 환경에서 필요한 모든 파일을 다운로드해야 합니다.

#### **1. 소스 코드 다운로드**

프로젝트의 최신 소스 코드를 로컬 환경으로 복제(clone)합니다.

```bash
git clone https://github.com/your-repo/RAGTrace.git
cd RAGTrace
```

#### **2. Python 의존성 패키징**

폐쇄망에서는 `pip install`을 통해 외부 패키지를 다운로드할 수 없으므로, 모든 의존성 패키지를 미리 다운로드하여 프로젝트와 함께 이전해야 합니다.

1.  **가상 환경 생성 및 활성화**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    # .\.venv\Scripts\activate # Windows
    ```

2.  **의존성 목록 생성**
    `uv.lock` 또는 `pyproject.toml`을 기반으로 `requirements.txt` 파일을 생성합니다.
    ```bash
    uv pip freeze > requirements.txt
    ```

3.  **패키지 파일 다운로드**
    `requirements.txt`에 명시된 모든 패키지와 그 하위 의존성까지 `.whl` 또는 `.tar.gz` 형태의 파일로 특정 폴더(`packages/`)에 다운로드합니다.
    ```bash
    mkdir packages
    uv pip download --requirement requirements.txt --dest packages/
    ```

이제 `RAGTrace` 폴더에는 소스 코드와 함께 모든 의존성 파일이 담긴 `packages/` 폴더가 준비되었습니다.

---

### **Phase 2: 프로젝트 이전 및 환경 구성 (내부망 환경)**

#### **1. 프로젝트 파일 전송**

사전 준비 단계에서 구성한 `RAGTrace` 폴더 전체(소스 코드, `packages/` 폴더 등 포함)를 `.zip` 또는 `.tar.gz`로 압축하여 보안 정책에 따라 폐쇄망 서버로 이전합니다.

#### **2. 내부망 서버에 환경 구성**

1.  **압축 해제 및 가상 환경 생성**
    이전한 프로젝트 파일의 압축을 해제하고, 해당 프로젝트 디렉토리 내에 새로운 가상 환경을 생성합니다.
    ```bash
    tar -xzvf RAGTrace.tar.gz
    cd RAGTrace
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **로컬 패키지로 의존성 설치**
    외부 네트워크 연결을 시도하지 않고, 함께 가져온 `packages/` 폴더만을 사용하여 의존성을 설치합니다. `--no-index` 와 `--find-links` 옵션이 핵심입니다.
    ```bash
    uv pip install --no-index --find-links=./packages -r requirements.txt
    ```

이제 폐쇄망 환경에 프로젝트 실행을 위한 모든 준비가 완료되었습니다.

---

### **Phase 3: 코드 커스터마이징 (HCX-005 연동)**

이제 가장 중요한 단계인 LLM 어댑터 교체 작업을 진행합니다. 우리는 클린 아키텍처 원칙에 따라 `infrastructure` 계층만 수정할 것입니다.

#### **1. `HcxAdapter` 파일 생성**

`src/infrastructure/llm/` 디렉토리에 `hcx_adapter.py`라는 새 파일을 생성합니다. 이 파일은 HCX-005 API와의 모든 통신을 책임집니다.

**파일 위치**: `src/infrastructure/llm/hcx_adapter.py`

```python
# src/infrastructure/llm/hcx_adapter.py

import os
import requests
import json
import uuid
from typing import List, Dict, Any

from src.application.ports.llm import LLMAdapter
from src.domain.entities import EvaluationData

# HCX-005 API의 상세 스펙을 기반으로 어댑터를 구현합니다.
class HcxAdapter(LLMAdapter):
    def __init__(
        self,
        api_key: str,
        api_gateway_key: str,
        endpoint: str = "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005",
        model_name: str = "HCX-005",
    ):
        if not api_key or not api_gateway_key:
            raise ValueError("HCX API Key와 Gateway Key가 모두 필요합니다.")

        self._api_key = api_key
        self._api_gateway_key = api_gateway_key
        self._endpoint = endpoint.format(modelName=model_name)
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "X-NCP-APIGW-API-KEY": self._api_gateway_key,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Accept": "application/json", # 스트리밍을 원하면 'text/event-stream'
        }

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        단순 텍스트 프롬프트로부터 텍스트를 생성합니다.
        RAGTrace의 기존 구조와 호환성을 위해 이 메서드를 유지할 수 있습니다.
        """
        # HCX API는 messages 형식을 요구하므로, 단순 프롬프트를 변환합니다.
        messages = [{"role": "user", "content": prompt}]
        return self._send_request(messages, **kwargs)

    def generate_response(self, data: EvaluationData, **kwargs) -> str:
        """
        EvaluationData 객체를 기반으로 HCX-005에 요청할 messages payload를 구성하고 응답을 생성합니다.
        """
        # HCX-005는 system, user, assistant 역할을 사용합니다.
        # RAG 시나리오에 맞게 context와 question을 user 메시지로 구성합니다.
        system_prompt = "You are a helpful AI assistant. Answer the user's question based on the given context."
        
        context_str = "\n".join(data.contexts)
        user_content = f"Context:\n{context_str}\n\nQuestion: {data.question}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        
        return self._send_request(messages, **kwargs)

    def _send_request(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        HCX-005 API에 실제 요청을 보내고 결과를 파싱합니다.
        """
        payload = {
            "messages": messages,
            "topP": kwargs.get("topP", 0.8),
            "topK": kwargs.get("topK", 0),
            "maxTokens": kwargs.get("maxTokens", 1024),
            "temperature": kwargs.get("temperature", 0.5),
            "repetitionPenalty": kwargs.get("repetitionPenalty", 1.1),
            "stop": kwargs.get("stop", []),
            "seed": kwargs.get("seed", 0),
        }

        try:
            response = requests.post(
                self._endpoint, headers=self._headers, data=json.dumps(payload), timeout=120
            )
            response.raise_for_status()  # 200번대 상태 코드가 아닐 경우 예외 발생

            response_json = response.json()

            # API 응답 구조에 따라 결과 추출
            if response_json.get("status", {}).get("code") == "20000":
                return response_json["result"]["message"]["content"]
            else:
                error_message = response_json.get("status", {}).get("message", "Unknown error")
                raise Exception(f"HCX API Error: {error_message}")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"HCX API 요청 실패: {e}") from e
```

#### **2. 의존성 주입 컨테이너 수정**

이제 `GeminiAdapter` 대신 방금 만든 `HcxAdapter`를 사용하도록 의존성 주입 컨테이너(`src/container.py`)를 수정합니다.

1.  **필요한 모듈 import**
    `src/container.py` 파일 상단에 `HcxAdapter`를 추가로 import 합니다.

    ```python
    # src/container.py
    # ... 기존 import ...
    from src.infrastructure.llm.gemini_adapter import GeminiAdapter # 이 라인은 제거하거나 주석 처리
    from src.infrastructure.llm.hcx_adapter import HcxAdapter # 이 라인 추가
    from . import config # 설정 로드를 위해 추가
    ```

2.  **`Container` 클래스 수정**
    `__init__` 메서드에서 `GeminiAdapter`를 생성하는 부분을 `HcxAdapter`로 교체합니다.

    ```python
    # src/container.py

    class Container:
        def __init__(self):
            # ... 기존 RagasEvalAdapter, FileRepositoryAdapter 초기화 코드 ...

            # -- 기존 GeminiAdapter 부분 주석 처리 또는 삭제 --
            # self.llm_adapter = GeminiAdapter(
            #     api_key=config.settings.GEMINI_API_KEY,
            #     model_name=config.settings.GEMINI_MODEL_NAME,
            #     requests_per_minute=config.settings.GEMINI_REQUESTS_PER_MINUTE,
            # )

            # ++ HCXAdapter 초기화 코드 추가 ++
            self.llm_adapter = HcxAdapter(
                api_key=config.settings.HCX_API_KEY,
                api_gateway_key=config.settings.HCX_API_GATEWAY_KEY,
                endpoint=config.settings.HCX_ENDPOINT,
            )

        def get_evaluation_use_case(self) -> RunEvaluation:
            return RunEvaluation(
                llm_adapter=self.llm_adapter,
                evaluation_adapter=self.evaluation_adapter,
                repository=self.repository,
            )
    ```

#### **3. 환경 변수 설정 파일 수정**

HCX-005 API 키와 엔드포인트를 관리하기 위해 `src/config.py` 파일을 수정합니다.

```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- 기존 Gemini 설정 (필요 시 삭제) ---
    # GEMINI_API_KEY: str = ""
    # GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    # ...

    # +++ HCX-005 설정 추가 +++
    HCX_API_KEY: str
    HCX_API_GATEWAY_KEY: str
    HCX_ENDPOINT: str = "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{modelName}"

    # .env 파일을 사용하도록 설정
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
```

---

### **Phase 4: 환경 설정 및 실행**

#### **1. `.env` 파일 생성**

프로젝트의 루트 디렉토리(최상위 `RAGTrace/`)에 `.env` 파일을 생성하고, Naver Cloud Platform에서 발급받은 API 키 정보를 입력합니다.

**파일 위치**: `/path/to/RAGTrace/.env`

```
# .env
HCX_API_KEY="여기에_CLOVA_Studio_API_키를_입력하세요"
HCX_API_GATEWAY_KEY="여기에_API_Gateway_API_키를_입력하세요"
# 엔드포인트를 변경할 경우 아래 라인의 주석을 해제하고 수정
# HCX_ENDPOINT="https://your/custom/endpoint/v3/chat-completions/{modelName}"
```

**중요**: `.env` 파일은 민감한 정보를 담고 있으므로, Git 추적에서 제외하기 위해 `.gitignore` 파일에 `.env`가 포함되어 있는지 반드시 확인하세요.

#### **2. 애플리케이션 실행**

이제 모든 설정이 완료되었습니다. 대시보드를 실행하여 애플리케이션이 정상적으로 동작하는지 확인합니다.

```bash
# 가상 환경이 활성화된 상태인지 확인
python run_dashboard.py
```

브라우저에서 대시보드에 접속하여 RAG 평가를 실행했을 때, 오류 없이 HCX-005 모델로부터 답변이 생성되고 평가가 완료되는지 확인합니다.

---

### **Phase 5: 테스트 및 검증**

#### **1. 단위 테스트 수정**

기존 `tests/infrastructure/llm/test_gemini_adapter.py` 파일을 복사하여 `tests/infrastructure/llm/test_hcx_adapter.py` 파일을 생성합니다. `requests.post`를 모킹(mocking)하여 `HcxAdapter`가 올바른 요청 헤더와 본문을 생성하는지, 그리고 API 응답을 정확히 파싱하는지 검증하는 테스트 코드를 작성합니다.

#### **2. 통합 테스트**

`run_dashboard.py`를 실행하여 실제 평가 데이터로 E2E(End-to-End) 테스트를 진행합니다.

1.  샘플 평가 데이터를 업로드합니다.
2.  평가를 실행합니다.
3.  결과 화면에 HCX-005가 생성한 답변과 Ragas 평가 점수가 정상적으로 표시되는지 확인합니다.
4.  오류가 발생할 경우, 터미널에 출력되는 로그를 확인하여 `HcxAdapter` 또는 `container.py`의 설정 문제를 디버깅합니다.

---

### **부록: Gemini vs. HCX-005 API 비교**

| 항목 | Google Gemini (`gemini-pro`) | Naver HyperCLOVA X (`HCX-005`) | RAGTrace 수정 사항 |
| :--- | :--- | :--- | :--- |
| **인증** | API Key in URL parameter | `Authorization` 및 `X-NCP-APIGW-API-KEY` 헤더 | `HcxAdapter`에서 HTTP 헤더를 올바르게 구성 |
| **엔드포인트** | `generativelanguage.googleapis.com` | `clovastudio.stream.ntruss.com` | `.env` 및 `HcxAdapter`에서 엔드포인트 관리 |
| **요청 본문** | `contents: [{"parts": [{"text": ...}]}]` | `messages: [{"role": ..., "content": ...}]` | `HcxAdapter`가 `EvaluationData`를 HCX `messages` 형식으로 변환 |
| **역할(Role)** | `user`, `model` | `system`, `user`, `assistant` | RAG 시나리오에 맞게 `system`, `user` 역할 할당 |
| **응답 파싱** | `candidates[0].content.parts[0].text` | `result.message.content` | `HcxAdapter`가 HCX 응답 JSON 구조에 맞게 파싱 |
| **주요 파라미터** | `generationConfig` (temperature 등) | `topP`, `topK`, `temperature` 등 | `_send_request` 메서드에서 파라미터 매핑 |

</rewritten_file> 