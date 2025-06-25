from typing import List
import requests
import threading
import time
from langchain_core.embeddings import Embeddings

# HCX 임베딩 API 요청 제한
_hcx_embedding_semaphore = threading.Semaphore(1)
_last_hcx_embedding_request_time = 0
_min_embedding_request_interval = 1.0  # 임베딩은 1초 간격


class HcxEmbeddingAdapter(Embeddings):
    """
    CLOVA Studio Embedding v2 API를 위한 LangChain 호환 어댑터
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("CLOVA_STUDIO_API_KEY가 HcxEmbeddingAdapter에 필요합니다.")
        
        self.api_key = api_key
        # 작동하는 엔드포인트 사용
        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/api-tools/embedding/v2"
        self.model_name = "HCX-Embedding"
        
        print(f"✅ HCX 임베딩 어댑터 초기화 완료: {self.model_name}")

    def _embed(self, text: str) -> List[float]:
        """단일 텍스트에 대한 임베딩을 수행합니다."""
        global _last_hcx_embedding_request_time
        
        # 글로벌 세마포어로 동시 요청 제한
        with _hcx_embedding_semaphore:
            # 최소 간격 보장
            current_time = time.time()
            elapsed = current_time - _last_hcx_embedding_request_time
            if elapsed < _min_embedding_request_interval:
                sleep_time = _min_embedding_request_interval - elapsed
                print(f"⏱️ HCX 임베딩 API 요청 간격 조절: {sleep_time:.1f}초 대기")
                time.sleep(sleep_time)
            
            _last_hcx_embedding_request_time = time.time()
            return self._make_embedding_request(text)
    
    def _make_embedding_request(self, text: str) -> List[float]:
        """실제 임베딩 API 요청 수행"""
        import uuid
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        }
        body = {"text": text}

        import time
        import random
        
        max_retries = 6   # 재시도 횟수 증가
        base_delay = 3    # 기본 지연 시간 증가
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, json=body, timeout=20)
                
                if response.status_code == 429:  # Too Many Requests
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2 ** attempt) + random.uniform(1.0, 3.0), 60)  # 최대 1분
                        print(f"⚠️ HCX 임베딩 API 요청 한도 초과 (429). {delay:.1f}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(f"HCX 임베딩 API 요청 한도 초과: 최대 재시도 횟수 초과")
                
                response.raise_for_status()
                result = response.json()
                return result["result"]["embedding"]
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️ HCX 임베딩 API 요청 실패: {e}. {delay}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise RuntimeError(f"HCX Embedding API 요청 실패: {e}")
            except KeyError:
                raise RuntimeError(f"HCX Embedding API의 응답 형식이 예상과 다릅니다: {response.text}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """여러 문서를 하나씩 임베딩합니다."""
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """단일 질문을 임베딩합니다."""
        return self._embed(text) 