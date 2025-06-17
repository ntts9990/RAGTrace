"""
Rate limiting 기능을 제공하는 범용 유틸리티 모듈

이 모듈은 다양한 API 호출에 대해 rate limiting을 적용할 수 있는
재사용 가능한 컴포넌트들을 제공합니다.
"""

import time
from typing import Any, Callable

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import Field


class RateLimiter:
    """범용 Rate Limiter 유틸리티"""
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.min_request_interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0
    
    def wait_if_needed(self) -> None:
        """요청 간 최소 시간 간격을 보장"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            print(f"Rate limiting: 대기 중... {sleep_time:.2f}초")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def apply_rate_limit(self, func: Callable) -> Callable:
        """함수에 rate limiting을 적용하는 데코레이터"""
        def wrapper(*args, **kwargs):
            self.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper


class RateLimitedGeminiLLM(ChatGoogleGenerativeAI):
    """Rate limiting이 적용된 Gemini LLM 래퍼"""

    requests_per_minute: int | None = Field(default=10, exclude=True)
    _rate_limiter: RateLimiter | None = Field(default=None, exclude=True)

    def __init__(self, *args, requests_per_minute: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests_per_minute = requests_per_minute
        self._rate_limiter = RateLimiter(requests_per_minute)

    def invoke(self, *args, **kwargs):
        """동기 호출 시 rate limiting 적용"""
        self._rate_limiter.wait_if_needed()
        return super().invoke(*args, **kwargs)

    async def ainvoke(self, *args, **kwargs):
        """비동기 호출 시 rate limiting 적용"""
        self._rate_limiter.wait_if_needed()
        return await super().ainvoke(*args, **kwargs)


class RateLimitedGeminiEmbeddings(GoogleGenerativeAIEmbeddings):
    """Rate limiting이 적용된 Gemini 임베딩 래퍼"""

    requests_per_minute: int | None = Field(default=10, exclude=True)
    _rate_limiter: RateLimiter | None = Field(default=None, exclude=True)

    def __init__(self, *args, requests_per_minute: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests_per_minute = requests_per_minute
        self._rate_limiter = RateLimiter(requests_per_minute)

    def embed_documents(self, texts):
        """문서 임베딩 시 rate limiting 적용"""
        self._rate_limiter.wait_if_needed()
        return super().embed_documents(texts)

    def embed_query(self, text):
        """쿼리 임베딩 시 rate limiting 적용"""
        self._rate_limiter.wait_if_needed()
        return super().embed_query(text)