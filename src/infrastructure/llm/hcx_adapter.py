import requests
from typing import List, Any, Dict

from src.application.ports.llm import LlmPort
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk, Generation


class HcxAdapter(LlmPort):
    """Naver Cloud CLOVA Studio HCX 모델 연동을 위한 어댑터"""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        requests_per_minute: int,
    ):
        if not api_key:
            raise ValueError("CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
        self.api_key = api_key
        self.model_name = model_name
        self.model = model_name  # RagasEvalAdapter 호환성을 위해 추가
        self.requests_per_minute = requests_per_minute
        self.api_url = f"https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{self.model_name}"

    def generate_answer(self, question: str, contexts: List[str]) -> str:
        """
        HCX 모델을 사용하여 질문과 컨텍스트 기반의 답변을 생성합니다.
        """
        context_text = "\\n\\n".join(contexts)
        
        # HCX 모델에 맞는 프롬프트 구성
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Based on the following context, please answer the question. Respond in Korean."
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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "messages": messages,
            "maxTokens": 1024,
            "temperature": 0.5,
            "topP": 0.8,
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=body, timeout=60)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
            
            result = response.json()
            return result["result"]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HCX API 요청 중 오류 발생: {e}")
        except KeyError:
            raise RuntimeError(f"HCX API 응답 형식이 예상과 다릅니다: {response.text}")

    def get_llm(self) -> Any:
        """
        Ragas 평가에 사용될 LangChain 호환 LLM 객체를 반환합니다.
        """
        return HcxLangChainCompat(adapter=self)


class HcxLangChainCompat(LLM):
    """HcxAdapter를 LangChain LLM처럼 사용하기 위한 래퍼 클래스"""
    
    adapter: HcxAdapter

    @property
    def _llm_type(self) -> str:
        return "hcx"

    def _call(self, prompt: str, stop: List[str] | None = None, **kwargs: Any) -> str:
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