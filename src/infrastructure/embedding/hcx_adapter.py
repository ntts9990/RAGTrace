import time
from typing import List
import requests
from langchain_core.embeddings import Embeddings

# 초당 API 요청 수를 제어하기 위한 간단한 Rate Limiter
class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.request_interval = 60.0 / requests_per_minute if requests_per_minute > 0 else 0
        self.last_request_time = 0

    def wait(self):
        if self.request_interval == 0:
            return
            
        elapsed_time = time.monotonic() - self.last_request_time
        if elapsed_time < self.request_interval:
            time.sleep(self.request_interval - elapsed_time)
        self.last_request_time = time.monotonic()


class HcxEmbeddingAdapter(Embeddings):
    """
    CLOVA Studio Embedding v2 API를 위한 LangChain 호환 어댑터
    """
    def __init__(self, api_key: str, requests_per_minute: int = 30):
        if not api_key:
            raise ValueError("CLOVA_STUDIO_API_KEY가 HcxEmbeddingAdapter에 필요합니다.")
        
        self.api_key = api_key
        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/api-tools/embedding/v2"
        self.rate_limiter = RateLimiter(requests_per_minute)

    def _embed(self, text: str) -> List[float]:
        """단일 텍스트에 대한 임베딩을 수행하고 API 요청 속도를 제어합니다."""
        self.rate_limiter.wait()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {"text": text}

        try:
            response = requests.post(self.api_url, headers=headers, json=body, timeout=20)
            response.raise_for_status()
            result = response.json()
            return result["result"]["embedding"]
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HCX Embedding API 요청 실패: {e}")
        except KeyError:
            raise RuntimeError(f"HCX Embedding API의 응답 형식이 예상과 다릅니다: {response.text}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """여러 문서를 하나씩 임베딩합니다."""
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """단일 질문을 임베딩합니다."""
        return self._embed(text) 