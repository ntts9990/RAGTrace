"""
LangChain 호환 Google GenerativeAI 직접 호출 래퍼
LangChain Google GenAI의 타임아웃 문제를 해결하기 위한 대안
"""

import time
from typing import List, Any, Dict, Optional

import google.generativeai as genai
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import Generation


class DirectGeminiWrapper(LLM):
    """Google GenerativeAI를 직접 사용하는 LangChain 호환 래퍼"""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        super().__init__(**kwargs)
        # LangChain의 필드 접근 제한 때문에 object.__setattr__ 사용
        object.__setattr__(self, 'api_key', api_key)
        object.__setattr__(self, 'model_name', model_name)
        object.__setattr__(self, 'timeout', 30)  # 30초 타임아웃으로 증가
        object.__setattr__(self, 'max_retries', 2)
        
        # Google AI 설정
        genai.configure(api_key=api_key)
        object.__setattr__(self, 'genai_model', genai.GenerativeModel(model_name))
        
        # LangChain 호환성을 위한 속성들
        object.__setattr__(self, 'model', model_name)
        object.__setattr__(self, 'temperature', 0.1)
        
        print(f"✅ DirectGeminiWrapper 초기화 완료: {model_name}")

    @property
    def _llm_type(self) -> str:
        return "direct_gemini"
    
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
        return self._generate_with_timeout(prompt)
        
    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs: Any) -> List[Generation]:
        """배치 프롬프트 처리"""
        generations = []
        for prompt in prompts:
            try:
                text = self._generate_with_timeout(prompt)
                generations.append(Generation(text=text))
            except Exception as e:
                print(f"⚠️ 프롬프트 생성 실패: {e}")
                # 실패한 경우 빈 텍스트로 처리
                generations.append(Generation(text=""))
        return generations

    def _generate_with_timeout(self, prompt: str) -> str:
        """타임아웃이 적용된 텍스트 생성 - 간단한 직접 호출"""
        try:
            # 간단한 직접 호출로 변경
            for attempt in range(self.max_retries):
                try:
                    response = self.genai_model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=1024,
                        )
                    )
                    
                    if response.text:
                        return response.text
                    else:
                        if attempt == self.max_retries - 1:
                            raise RuntimeError("응답이 비어있습니다")
                        time.sleep(1)
                        
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise RuntimeError(f"Google AI API 오류: {str(e)}")
                    time.sleep(1)  # 재시도 전 대기
                    
        except Exception as e:
            raise RuntimeError(f"Google AI API 호출 실패: {str(e)}")

    def invoke(self, prompt: str) -> Any:
        """ChatGoogleGenerativeAI 호환성을 위한 invoke 메서드"""
        class Response:
            def __init__(self, content: str):
                self.content = content
        
        result = self._call(prompt)
        return Response(result)