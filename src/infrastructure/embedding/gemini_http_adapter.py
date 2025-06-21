"""
HTTP를 통한 직접 Google Gemini Embedding API 호출 어댑터
langchain-google-genai의 타임아웃 문제를 해결하기 위한 대안
"""

import json
import time
from typing import List, Optional

import requests
from langchain_core.embeddings import Embeddings


class GeminiHttpEmbeddingAdapter(Embeddings):
    """HTTP를 통해 Google Gemini Embedding API를 직접 호출하는 어댑터"""
    
    def __init__(self, api_key: str, model_name: str = "models/text-embedding-004"):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = 20  # 20초 타임아웃
        self.max_retries = 2
        
        # 모델명 정리 (models/ 프리픽스 제거)
        clean_model_name = model_name.replace("models/", "")
        if "embedding" not in clean_model_name:
            clean_model_name = "text-embedding-004"  # 기본 임베딩 모델
        
        # API URL 구성
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:embedContent?key={api_key}"
        
        print(f"✅ GeminiHttpEmbeddingAdapter 초기화 완료: {clean_model_name}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 임베딩합니다."""
        embeddings = []
        for text in texts:
            try:
                embedding = self._embed_single_text(text)
                embeddings.append(embedding)
            except Exception as e:
                print(f"⚠️ 임베딩 실패 ({text[:50]}...): {e}")
                # 실패한 경우 빈 벡터로 처리 (768차원)
                embeddings.append([0.0] * 768)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """단일 쿼리를 임베딩합니다."""
        try:
            return self._embed_single_text(text)
        except Exception as e:
            print(f"⚠️ 쿼리 임베딩 실패: {e}")
            # 실패한 경우 빈 벡터로 처리 (768차원)
            return [0.0] * 768

    def _embed_single_text(self, text: str) -> List[float]:
        """단일 텍스트를 HTTP API로 임베딩합니다."""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result["embedding"]["values"]
                    return embedding
                else:
                    if attempt == self.max_retries - 1:
                        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
                    time.sleep(1)
                    
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"HTTP 요청 실패: {str(e)}")
                time.sleep(1)
                
        raise RuntimeError("모든 재시도 실패")

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """비동기 문서 임베딩 (동기 버전으로 폴백)"""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """비동기 쿼리 임베딩 (동기 버전으로 폴백)"""
        return self.embed_query(text)