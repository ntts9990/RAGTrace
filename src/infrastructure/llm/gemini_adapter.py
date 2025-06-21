from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI

from src.application.ports.llm import LlmPort
from src.infrastructure.llm.rate_limiter import RateLimitedGeminiLLM


class GeminiAdapter(LlmPort):
    """Gemini LLM 연동을 위한 구현체 (Adapter)"""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        requests_per_minute: int,
    ):
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        self.api_key = api_key
        self.model_name = model_name
        self.requests_per_minute = requests_per_minute
        print(f"✅ Gemini LLM Rate Limiting 활성화: {requests_per_minute} requests/minute")

    def generate_answer(self, question: str, contexts: List[str]) -> str:
        """
        질문과 컨텍스트를 바탕으로 답변을 생성합니다.
        
        Args:
            question: 질문 텍스트
            contexts: 컨텍스트 목록
            
        Returns:
            str: 생성된 답변
        """
        llm = self.get_llm()
        
        # 컨텍스트를 하나의 문자열로 결합
        context_text = "\n\n".join(contexts)
        
        # 프롬프트 구성
        prompt = f"""다음 컨텍스트를 바탕으로 질문에 답변하세요.

컨텍스트:
{context_text}

질문: {question}

답변:"""
        
        try:
            response = llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            raise RuntimeError(f"답변 생성 중 오류 발생: {str(e)}") from e

    def get_llm(self) -> ChatGoogleGenerativeAI:
        """
        Rate limiting이 적용된 Gemini LLM 객체를 반환합니다.
        
        Note: 이 메서드는 하위 호환성을 위해 유지되지만,
        향후 generate_answer 메서드 사용을 권장합니다.
        """
        return RateLimitedGeminiLLM(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.1,
            timeout=60,  # 60초 타임아웃
            max_retries=2,  # 최대 2회 재시도
            requests_per_minute=self.requests_per_minute  # Rate limiting 적용
        )
