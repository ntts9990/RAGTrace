"""애플리케이션 설정 관리 모듈

이 모듈은 Pydantic-Settings를 사용하여 .env 파일과 환경 변수에서
설정을 로드하고, 타입 검증 및 기본값을 관리합니다.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.paths import ENV_FILE_PATH


class Settings(BaseSettings):
    """애플리케이션 설정을 정의하는 클래스"""

    # .env 파일을 읽도록 설정
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, env_file_encoding="utf-8", extra="ignore"
    )

    # LLM 관련 설정
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash-latest"
    GEMINI_REQUESTS_PER_MINUTE: int = 1000

    # Embedding 관련 설정
    GEMINI_EMBEDDING_MODEL_NAME: str = "models/embedding-001"
    EMBEDDING_REQUESTS_PER_MINUTE: int = 1000

    # 여기에 다른 필요한 설정들을 추가할 수 있습니다.
    # 예: DATABASE_ECHO: bool = False


# 설정 객체 인스턴스를 생성하여 다른 모듈에서 import하여 사용
settings = Settings()
