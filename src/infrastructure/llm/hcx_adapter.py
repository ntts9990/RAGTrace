import requests
from typing import List, Any, Dict
import threading
import time

from src.application.ports.llm import LlmPort
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk, Generation, LLMResult


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
            "maxTokens": 1024,
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
        """RAGAS 파싱을 위한 응답 후처리"""
        if not content:
            return content
            
        # 일반적인 정리
        content = content.strip()
        
        # JSON 형식 검사 및 수정
        import re
        import json
        
        # RAGAS가 기대하는 JSON 형식 확인
        if content.startswith('{') and content.endswith('}'):
            try:
                # JSON 파싱 시도
                parsed = json.loads(content)
                return content  # 이미 올바른 JSON
            except json.JSONDecodeError:
                # JSON 형식이지만 파싱 실패 - 수정 시도
                pass
        
        # JSON 블록 추출 시도 (```json ... ``` 형식)
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_block_match:
            try:
                json_content = json_block_match.group(1)
                parsed = json.loads(json_content)
                return json_content
            except:
                pass
        
        # 중괄호로 둘러싸인 JSON 찾기
        json_match = re.search(r'(\{[^{}]*\})', content, re.DOTALL)
        if json_match:
            try:
                json_content = json_match.group(1)
                parsed = json.loads(json_content)
                return json_content
            except:
                pass
        
        # RAGAS가 기대하는 특정 형식들 처리
        # 1. Yes/No 질문에 대한 응답을 JSON으로 변환
        content_lower = content.lower()
        if any(word in content_lower for word in ['yes', '예', '맞습니다', '그렇습니다']):
            if not any(word in content_lower for word in ['no', '아니', '아닙니다', '그렇지 않습니다']):
                return '{"answer": "Yes"}'
        elif any(word in content_lower for word in ['no', '아니', '아닙니다', '그렇지 않습니다']):
            return '{"answer": "No"}'
        
        # 2. 숫자/점수 응답을 JSON으로 변환
        number_match = re.search(r'\b(\d+(?:\.\d+)?)\b', content)
        if number_match and len(content.split()) <= 5:
            score = number_match.group(1)
            return f'{{"score": {score}}}'
        
        # 3. 리스트 형태 응답을 JSON 배열로 변환
        if content.startswith('- ') or content.startswith('1. '):
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            items = []
            for line in lines:
                # 번호나 대시 제거
                cleaned = re.sub(r'^[-*•]?\s*\d*\.?\s*', '', line).strip()
                if cleaned:
                    items.append(cleaned)
            if items:
                return json.dumps({"items": items}, ensure_ascii=False)
        
        # 4. 일반 텍스트를 JSON으로 감싸기
        # 특수문자 이스케이프 처리
        escaped_content = content.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
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

    @property
    def _llm_type(self) -> str:
        return "hcx"

    def _call(self, prompt: str, stop: List[str] | None = None, run_manager=None, **kwargs: Any) -> str:
        # Ragas는 주로 (question, contexts) 쌍으로 평가하지만,
        # 일부 메트릭은 단일 프롬프트(텍스트)를 사용하므로, 이를 question으로 간주합니다.
        return self.adapter.generate_answer(question=prompt, contexts=[])
        
    def _generate(
        self, prompts: List[str], stop: List[str] | None = None, **kwargs: Any
    ) -> List[Generation]:
        generations = []
        for prompt in prompts:
            text = self._call(prompt, stop, **kwargs)
            generations.append(Generation(text=text))
        return generations

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """모델 식별을 위한 파라미터 반환"""
        return {
            "model_name": self.adapter.model_name,
        } 