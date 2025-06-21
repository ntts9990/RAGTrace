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

# HCX-005 모델 연동 가이드

이 문서는 RAGTrace 프로젝트에서 Naver Cloud CLOVA Studio의 HCX-005 모델을 사용하기 위한 핵심 API 명세를 정리한 가이드입니다.

## 1. 개요

- **모델**: HCX-005 (Vision/Language Model)
- **주요 기능**:
  - `Chat Completions v3` API를 통한 텍스트 및 이미지 처리
  - `Function Calling` 지원
- **특징**: 이 모델은 평가 파이프라인에서 LLM의 성능을 측정하는 데 사용될 수 있습니다.

## 2. 인증 및 기본 설정

- **API Key 발급**: 네이버 클라우드 플랫폼 콘솔의 `CLOVA Studio` > `API 키` 메뉴에서 발급받습니다.
- **API URL**: `https://clovastudio.stream.ntruss.com`
- **공통 요청 헤더**:
  - `Authorization`: `Bearer {발급받은 API Key}`
  - `Content-Type`: `application/json`

## 3. Chat Completions API (v3) 핵심 명세

HCX-005 모델을 사용하기 위한 기본 API 명세입니다.

### 3.1. 엔드포인트

- **Method**: `POST`
- **URI**: `/v3/chat-completions/{modelName}`
  - **`modelName`**: `HCX-005`

### 3.2. 주요 요청 파라미터 (Request Body)

| 필드                | 타입          | 필수 | 설명                                                                                                |
| ------------------- | ------------- | ---- | --------------------------------------------------------------------------------------------------- |
| `messages`          | Array         | O    | 대화 메시지 목록. `role`과 `content`로 구성.                                                        |
| `maxTokens`         | Integer       | X    | 최대 생성 토큰 수. (기본값: 100, **최대: 4096**)                                                    |
| `temperature`       | Double        | X    | 다양성 조절 (0.0 ~ 1.0). 높을수록 다양함. (기본값: 0.5)                                             |
| `topP`              | Double        | X    | 누적 확률 기반 샘플링 (0.0 ~ 1.0). (기본값: 0.8)                                                    |
| `repetitionPenalty` | Double        | X    | 반복 패널티 (0.0 ~ 2.0). (기본값: 1.1)                                                              |
| `tools`             | Array         | X    | Function Calling을 위한 도구(함수) 목록 정의.                                                       |
| `toolChoice`        | String/Object | X    | 도구 호출 방식 지정 (`auto`, `none`, 또는 특정 함수 강제).                                          |

### 3.3. `messages` 구조

- **`role`**: `system`, `user`, `assistant`, `tool`
- **`content`**:
  - **텍스트**: `String`
  - **텍스트+이미지**: `Array`
    - `type`: "text", `text`: "설명"
    - `type`: "image_url", `imageUrl`: { `url`: "..." } 또는 `dataUri`: { `data`: "base64..." }

### 3.4. 요청 예시 (텍스트 및 이미지)

```shell
curl --request POST 'https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005' \
--header 'Authorization: Bearer {CLOVA Studio API Key}' \
--header 'Content-Type: application/json' \
--data '{
    "messages": [
      {
        "role": "system",
        "content": "- 친절하게 답변하는 AI 어시스턴트입니다."
      },
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "imageUrl": {
              "url": "https://.../image.png"
            }
          },
          {
            "type": "text",
            "text": "이 사진에 대해서 설명해줘"
          }
        ]
      }
    ],
    "maxTokens": 256,
    "temperature": 0.5
  }'
```

### 3.5. 주요 응답 파라미터 (Response Body)

- `result.message.content`: 모델이 생성한 답변 텍스트.
- `result.usage`: 토큰 사용량 (`promptTokens`, `completionTokens`, `totalTokens`).
- `result.finishReason`: 생성 중단 이유 (`length`, `stop`, `tool_calls`).

### 3.6. HCX-005 모델 제약 사항

- **토큰 제한**: 입력 토큰과 출력 토큰의 합은 **128,000**을 초과할 수 없습니다.
- **이미지 제한**: 요청당 최대 **5개**의 이미지를 포함할 수 있습니다 (턴당 1개).
- **Request Body 크기**: 50MB 이하여야 합니다.

## 4. Function Calling 사용법

외부 함수나 API를 호출하여 동적인 정보를 답변에 활용하는 기능입니다.

### 4.1. 동작 흐름

1.  **[사용자 -> 모델]** `messages`와 함께 사용 가능한 함수 목록(`tools`)을 전달합니다.
2.  **[모델 -> 사용자]** 모델이 함수 호출이 필요하다고 판단하면, `finishReason: "tool_calls"`와 함께 호출할 함수 정보(`toolCalls`)를 응답합니다.
3.  **[사용자]** 응답받은 정보를 바탕으로 실제 함수(클라이언트 측 코드)를 실행합니다.
4.  **[사용자 -> 모델]** 함수 실행 결과를 `role: "tool"` 메시지에 담아 다시 모델에 전달합니다.
5.  **[모델 -> 사용자]** 모델이 함수 실행 결과를 바탕으로 최종 답변을 생성하여 응답합니다.

### 4.2. 요청 예시 (Python)

```python
import requests
import json

# Step 1 & 2: 함수 정의 전달 및 모델의 함수 호출 요청 받기
response = requests.post(
    "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005",
    headers={...},
    json={
        "messages": [{"role": "user", "content": "오늘 서울 날씨 알려줘"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "특정 지역의 날씨 정보를 가져옵니다.",
                "parameters": { ... }
            }
        }],
        "toolChoice": "auto"
    }
)
result = response.json()
tool_call = result["result"]["message"]["toolCalls"][0]

# Step 3: 실제 함수 실행
arguments = json.loads(tool_call["function"]["arguments"])
function_result = get_weather(**arguments) # 로컬/외부 API 호출

# Step 4 & 5: 함수 실행 결과 전달 및 최종 답변 받기
final_response = requests.post(
    "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005",
    headers={...},
    json={
        "messages": [
            {"role": "user", "content": "오늘 서울 날씨 알려줘"},
            result["result"]["message"], # 이전 모델 응답
            {
                "role": "tool",
                "toolCallId": tool_call["id"],
                "content": json.dumps(function_result)
            }
        ],
        ...
    }
)
final_result = final_response.json()
print(final_result["result"]["message"]["content"])
``` 