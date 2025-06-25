"""
Configuration Container

애플리케이션 설정 관리를 담당하는 컨테이너입니다.
"""

from src.config import settings


class ConfigurationContainer:
    """설정 관리를 위한 컨테이너"""
    
    def __init__(self):
        self.config = settings
    
    def get_llm_config(self, llm_type: str) -> dict:
        """LLM 설정 반환"""
        if llm_type == "gemini":
            return {
                "api_key": self.config.GEMINI_API_KEY,
                "model_name": self.config.GEMINI_MODEL_NAME,
            }
        elif llm_type == "hcx":
            return {
                "api_key": self.config.CLOVA_STUDIO_API_KEY,
                "model_name": self.config.HCX_MODEL_NAME,
            }
        else:
            raise ValueError(f"지원하지 않는 LLM 타입: {llm_type}")
    
    def get_embedding_config(self, embedding_type: str) -> dict:
        """임베딩 모델 설정 반환"""
        if embedding_type == "gemini":
            return {
                "api_key": self.config.GEMINI_API_KEY,
                "model_name": self.config.GEMINI_EMBEDDING_MODEL_NAME,
            }
        elif embedding_type == "hcx":
            return {
                "api_key": self.config.CLOVA_STUDIO_API_KEY,
            }
        elif embedding_type == "bge_m3":
            return {
                "model_path": self.config.BGE_M3_MODEL_PATH,
                "device": self.config.BGE_M3_DEVICE,
            }
        else:
            raise ValueError(f"지원하지 않는 임베딩 타입: {embedding_type}")
    
    def validate_llm_config(self, llm_type: str) -> bool:
        """LLM 설정 유효성 검증"""
        try:
            config = self.get_llm_config(llm_type)
            if llm_type == "gemini":
                return bool(config["api_key"])
            elif llm_type == "hcx":
                return bool(config["api_key"])
            return True
        except Exception:
            return False
    
    def validate_embedding_config(self, embedding_type: str) -> bool:
        """임베딩 모델 설정 유효성 검증"""
        try:
            config = self.get_embedding_config(embedding_type)
            if embedding_type in ["gemini", "hcx"]:
                return bool(config["api_key"])
            elif embedding_type == "bge_m3":
                # BGE-M3는 model_path가 None이어도 기본값으로 자동 다운로드됨
                return True
            return True
        except Exception:
            return False