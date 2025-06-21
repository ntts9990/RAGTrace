"""
HTTP를 통한 직접 Google Gemini API 호출 래퍼
google-generativeai 라이브러리의 타임아웃 문제를 해결하기 위한 대안
"""

import json
import time
from typing import List, Any, Dict, Optional

import requests
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import Generation


class HttpGeminiWrapper(LLM):
    """HTTP를 통해 Google Gemini API를 직접 호출하는 LangChain 호환 래퍼"""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        super().__init__(**kwargs)
        # LangChain의 필드 접근 제한 때문에 object.__setattr__ 사용
        object.__setattr__(self, 'api_key', api_key)
        object.__setattr__(self, 'model_name', model_name)
        object.__setattr__(self, 'timeout', 20)  # 20초 타임아웃
        object.__setattr__(self, 'max_retries', 2)
        
        # 모델명 정리 (models/ 프리픽스 제거하고 표준 이름 사용)
        clean_model_name = model_name.replace("models/", "")
        if "gemini-2.5-flash" in clean_model_name:
            clean_model_name = "gemini-1.5-flash"  # 안정적인 모델로 변경
        
        # API URL 구성
        object.__setattr__(self, 'api_url', 
            f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent?key={api_key}")
        
        # LangChain 호환성을 위한 속성들
        object.__setattr__(self, 'model', model_name)
        object.__setattr__(self, '_temperature', 0.1)
        
        print(f"✅ HttpGeminiWrapper 초기화 완료: {model_name}")

    @property
    def _llm_type(self) -> str:
        return "http_gemini"
    
    # LangChain에서 접근하는 필드들을 명시적으로 허용
    @property
    def temperature(self) -> float:
        return getattr(self, '_temperature', 0.1)
    
    @temperature.setter
    def temperature(self, value: float):
        object.__setattr__(self, '_temperature', value)
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """모델 식별 파라미터"""
        return {
            "model_name": self.model_name,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager=None, **kwargs: Any) -> str:
        """단일 프롬프트 처리"""
        return self._generate_with_http(prompt)
        
    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs: Any) -> List[Generation]:
        """배치 프롬프트 처리"""
        generations = []
        for prompt in prompts:
            try:
                text = self._generate_with_http(prompt)
                generations.append(Generation(text=text))
            except Exception as e:
                print(f"⚠️ 프롬프트 생성 실패: {e}")
                # 실패한 경우 빈 텍스트로 처리
                generations.append(Generation(text=""))
        return generations

    def _generate_with_http(self, prompt: str) -> str:
        """HTTP를 통한 직접 API 호출"""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 1024,
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
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return content
                else:
                    if attempt == self.max_retries - 1:
                        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
                    time.sleep(1)
                    
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"HTTP 요청 실패: {str(e)}")
                time.sleep(1)
                
        raise RuntimeError("모든 재시도 실패")

    def invoke(self, prompt: str) -> Any:
        """ChatGoogleGenerativeAI 호환성을 위한 invoke 메서드"""
        class Response:
            def __init__(self, content: str):
                self.content = content
        
        result = self._call(prompt)
        return Response(result)