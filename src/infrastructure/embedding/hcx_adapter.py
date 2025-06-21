from typing import List
import requests
from langchain_core.embeddings import Embeddings


class HcxEmbeddingAdapter(Embeddings):
    """
    CLOVA Studio Embedding v2 API를 위한 LangChain 호환 어댑터
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("CLOVA_STUDIO_API_KEY가 HcxEmbeddingAdapter에 필요합니다.")
        
        self.api_key = api_key
        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/api-tools/embedding/v2"

    def _embed(self, text: str) -> List[float]:
        """단일 텍스트에 대한 임베딩을 수행합니다."""

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