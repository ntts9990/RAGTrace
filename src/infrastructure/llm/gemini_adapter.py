from typing import List

from src.application.ports.llm import LlmPort
from src.infrastructure.llm.http_gemini_wrapper import HttpGeminiWrapper


class GeminiAdapter(LlmPort):
    """Gemini LLM 연동을 위한 구현체 (Adapter)"""

    def __init__(
        self,
        api_key: str,
        model_name: str,
    ):
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        self.api_key = api_key
        self.model_name = model_name
        self.model = model_name  # RagasEvalAdapter 호환성을 위해 추가
        print(f"✅ Gemini LLM 초기화 완료: {model_name}")

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

    def get_llm(self) -> HttpGeminiWrapper:
        """
        Gemini LLM 객체를 반환합니다.
        
        HttpGeminiWrapper를 사용하여 HTTP로 직접 API 호출합니다.
        """
        return HttpGeminiWrapper(
            api_key=self.api_key,
            model_name=self.model_name,
        )
