import time

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import Field

from src.application.ports.llm import LlmPort


class RateLimitedGeminiLLM(ChatGoogleGenerativeAI):
    """Rate limiting이 적용된 Gemini LLM 래퍼"""

    requests_per_minute: int | None = Field(default=10, exclude=True)
    min_request_interval: float | None = Field(default=6.0, exclude=True)
    last_request_time: float | None = Field(default=0.0, exclude=True)

    def __init__(self, *args, requests_per_minute: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests_per_minute = requests_per_minute
        self.min_request_interval = 60.0 / requests_per_minute
        self.last_request_time = 0

    def _rate_limit(self):
        """요청 간 최소 시간 간격을 보장"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            print(f"Rate limiting: 대기 중... {sleep_time:.2f}초")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def invoke(self, *args, **kwargs):
        """동기 호출 시 rate limiting 적용"""
        self._rate_limit()
        return super().invoke(*args, **kwargs)

    async def ainvoke(self, *args, **kwargs):
        """비동기 호출 시 rate limiting 적용"""
        self._rate_limit()
        return await super().ainvoke(*args, **kwargs)


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

    def get_llm(self) -> RateLimitedGeminiLLM:
        """
        Rate limiting이 적용된 Gemini LLM 객체를 반환합니다.
        """
        return RateLimitedGeminiLLM(
            model=self.model_name,
            google_api_key=self.api_key,
            # temperature는 RAGAS에서 내부적으로 1e-08로 강제 설정됨 (평가 일관성을 위해)
            requests_per_minute=self.requests_per_minute,
        )
