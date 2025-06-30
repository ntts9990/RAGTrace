import requests
from typing import List, Any, Dict
import threading
import time
import json
import re

from src.application.ports.llm import LlmPort
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk, Generation, LLMResult
from langchain_core.prompt_values import StringPromptValue


# 글로벌 HCX API 요청 제한을 위한 세마포어
_hcx_semaphore = threading.Semaphore(1)  # 동시에 1개 요청만 허용
_last_hcx_request_time = 0
_min_request_interval = 1.0  # 최소 1초 간격으로 줄임


class HcxAdapter(LlmPort):
    """Naver Cloud CLOVA Studio HCX 모델 연동을 위한 어댑터"""

    def __init__(
        self,
        api_key: str,
        model_name: str,
    ):
        if not api_key:
            raise ValueError("CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
        if not api_key.startswith("nv-"):
            raise ValueError("CLOVA_STUDIO_API_KEY는 'nv-'로 시작해야 합니다.")
        self.api_key = api_key
        self.model_name = model_name if model_name else "HCX-005"  # 기본값을 HCX-005로 설정
        self.model = self.model_name  # RagasEvalAdapter 호환성을 위해 추가
        # 작동하는 엔드포인트 사용 (테스트로 확인됨)
        self.api_url = f"https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{self.model_name}"
        
        # 디버그: API 키와 URL 확인
        print(f"🔧 HCX 어댑터 초기화: {self.model_name}")
        print(f"   API URL: {self.api_url}")
        print(f"   API 키 확인: {self.api_key[:10]}...{self.api_key[-5:]}")

    def generate_answer(self, question: str, contexts: List[str]) -> str:
        """
        HCX 모델을 사용하여 질문과 컨텍스트 기반의 답변을 생성합니다.
        """
        global _last_hcx_request_time
        
        # 글로벌 세마포어로 동시 요청 제한
        with _hcx_semaphore:
            # 최소 간격 보장
            current_time = time.time()
            elapsed = current_time - _last_hcx_request_time
            if elapsed < _min_request_interval:
                sleep_time = _min_request_interval - elapsed
                # 로그 출력 제거 - 너무 많은 로그 방지
                time.sleep(sleep_time)
            
            _last_hcx_request_time = time.time()
            return self._make_api_request(question, contexts)
    
    def _make_api_request(self, question: str, contexts: List[str]) -> str:
        """실제 API 요청 수행"""
        context_text = "\\n\\n".join(contexts)
        
        # HCX API 간단한 형식으로 시작 (문제 해결 후 Array 형식으로 변경 가능)
        messages = [
            {
                "role": "system",
                "content": "당신은 도움이 되는 AI 어시스턴트입니다. 주어진 컨텍스트를 바탕으로 질문에 정확하고 간결하게 답변하세요."
            },
            {
                "role": "user",
                "content": f"""다음 컨텍스트를 바탕으로 질문에 답변하세요.

# 컨텍스트:
{context_text}

# 질문: {question}

# 답변:"""
            }
        ]

        import uuid
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-NCP-CLOVASTUDIO-API-KEY": self.api_key,
            "X-NCP-APIGW-API-KEY": self.api_key,  # API Gateway 키도 추가
            "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = {
            "messages": messages,
            "maxTokens": 4096,
            "temperature": 0.5,
            "topP": 0.8,
            "topK": 0,
            "repetitionPenalty": 1.1,
            "stop": [],
            "includeAiFilters": False,  # AI 필터 비활성화로 응답 속도 개선
        }

        import random
        
        max_retries = 3   # 재시도 횟수 더 줄임
        base_delay = 2    # 기본 지연 시간 더 줄임
        
        for attempt in range(max_retries):
            try:
                # 첫 번째 시도와 재시도만 로그 출력
                if attempt == 0 or attempt == max_retries - 1:
                    print(f"🔄 HCX API 호출 {'(최종)' if attempt == max_retries - 1 else ''}")
                response = requests.post(self.api_url, headers=headers, json=body, timeout=60)
                
                # 상태 코드 로그 (디버깅용)
                if attempt == max_retries - 1 or response.status_code != 200:
                    print(f"   응답 코드: {response.status_code}")
                
                if response.status_code == 403:  # Forbidden
                    if attempt == max_retries - 1:
                        print(f"❌ HCX API 403 오류 - API 키 확인 필요")
                        return "API 권한 오류로 인해 평가를 완료할 수 없습니다."
                    else:
                        delay = base_delay * (1.5 ** attempt) + random.uniform(0.5, 1.0)
                        time.sleep(delay)
                        continue
                
                if response.status_code == 429:  # Too Many Requests
                    if attempt == max_retries - 1:
                        print(f"⚠️ HCX API 사용량 초과")
                        return "API 한도 초과"
                    else:
                        delay = min(base_delay * (2 ** attempt) + random.uniform(2.0, 5.0), 30)  # 최대 30초
                        time.sleep(delay)
                        continue
                
                response.raise_for_status()  # 다른 HTTP 오류 발생 시 예외 발생
                
                result = response.json()
                # API v3 응답 구조에 맞게 수정
                content = ""
                if "result" in result and "message" in result["result"]:
                    content = result["result"]["message"]["content"]
                elif "message" in result:
                    content = result["message"]["content"]
                else:
                    print(f"❌ 예상하지 못한 HCX API 응답 구조: {result}")
                    return "응답 구조를 파싱할 수 없습니다."
                
                # RAGAS 파싱을 위한 응답 후처리
                content = self._post_process_response(content)
                if attempt == 0:  # 첫 번째 성공 시에만 로그
                    print(f"✅ HCX API 응답 받음")
                return content
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"❌ HCX API 네트워크 오류: {str(e)}")
                    print(f"   URL: {self.api_url}")
                    print(f"   API 키 형식: {self.api_key[:15]}...")
                    return "네트워크 오류로 인해 평가를 완료할 수 없습니다."
                else:
                    delay = base_delay * (1.5 ** attempt) + random.uniform(0.5, 1.0)
                    time.sleep(delay)
                    continue
            except (KeyError, json.JSONDecodeError):
                if attempt == max_retries - 1:
                    print(f"❌ HCX API 응답 파싱 실패")
                    return "응답 형식 오류"
                else:
                    time.sleep(base_delay)
                    continue

    def _post_process_response(self, content: str) -> str:
        """RAGAS 파싱을 위한 응답 후처리 (강화된 버전)"""
        import re
        import json

        content = content.strip()

        # 1. 가장 먼저, JSON 마크다운 블록 추출 시도
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                content = json_str

        # 2. 문자열 내에서 JSON 객체처럼 보이는 부분 추출
        start_index = content.find('{')
        end_index = content.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = content[start_index : end_index + 1]
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass

        # 3. 전체 문자열이 유효한 JSON인지 마지막으로 확인
        try:
            json.loads(content)
            return content
        except json.JSONDecodeError:
            pass

        # 4. 모든 JSON 추출 실패 시, 답변을 JSON으로 감싸기
        escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'{{"answer": "{escaped_content}"}}'

    def get_llm(self) -> Any:
        """
        Ragas 평가에 사용될 LangChain 호환 LLM 객체를 반환합니다.
        """
        return HcxLangChainCompat(adapter=self)


class HcxLangChainCompat(LLM):
    """HcxAdapter를 LangChain LLM처럼 사용하기 위한 래퍼 클래스"""
    
    def __init__(self, adapter: HcxAdapter, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'adapter', adapter)
        object.__setattr__(self, 'model', adapter.model_name)

    def generate(self, prompts: List[str | StringPromptValue], **kwargs: Any) -> LLMResult:
        """
        Ragas에서 단일 프롬프트를 리스트로 감싸지 않고 호출하는 경우에 대한 예외 처리
        """
        if not isinstance(prompts, list):
            prompts = [prompts]
        return super().generate(prompts=prompts, **kwargs)

    async def agenerate(self, prompts: List[str | StringPromptValue], **kwargs: Any) -> LLMResult:
        """
        Ragas에서 비동기 호출 시 단일 프롬프트를 리스트로 감싸지 않고 호출하는 경우에 대한 예외 처리
        """
        if not isinstance(prompts, list):
            prompts = [prompts]
        # 부모 클래스의 agenerate를 호출하여 비동기 파이프라인을 사용
        return await super().agenerate(prompts=prompts, **kwargs)

    @property
    def _llm_type(self) -> str:
        return "hcx"
    
    def set_run_config(self, run_config):
        """RAGAS RunConfig 설정 - HCX는 무시"""
        # HCX는 자체 설정을 사용하므로 RunConfig는 무시
        pass

    def _call(self, prompt, stop: List[str] | None = None, run_manager=None, **kwargs: Any) -> str:
        if hasattr(prompt, 'to_string'):
            prompt_str = prompt.to_string()
        else:
            prompt_str = str(prompt)
        
        result = self.adapter.generate_answer(question=prompt_str, contexts=[])
        return self.adapter._post_process_response(result)
        
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """모델 식별을 위한 파라미터 반환"""
        return {
            "model_name": self.adapter.model_name,
        } 