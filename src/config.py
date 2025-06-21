"""
애플리케이션 설정 관리

환경 변수와 설정 파일을 통해 애플리케이션 설정을 관리합니다.
RAGAS 프롬프트 커스터마이징 설정도 포함합니다.
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from src.domain.prompts import PromptType


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    # Gemini API 설정
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API 키")
    GEMINI_MODEL_NAME: str = Field(
        default="models/gemini-2.5-flash-preview-05-20", description="사용할 Gemini 모델명"
    )
    GEMINI_EMBEDDING_MODEL_NAME: str = Field(
        default="models/gemini-embedding-exp-03-07", description="임베딩용 Gemini 모델명"
    )


    # HCX API 설정
    CLOVA_STUDIO_API_KEY: Optional[str] = Field(default=None, description="Naver Cloud CLOVA Studio API 키")
    HCX_MODEL_NAME: str = Field(default="HCX-005", description="사용할 HCX 모델명")

    # LLM 선택 설정
    DEFAULT_LLM: str = Field(default="gemini", description="사용할 기본 LLM (gemini 또는 hcx)")

    # 프롬프트 커스터마이징 설정
    DEFAULT_PROMPT_TYPE: str = Field(
        default="default", 
        description="기본 사용할 프롬프트 타입 (default, korean_tech, multilingual_tech)"
    )
    
    # CLI에서 프롬프트 타입 오버라이드
    RAGAS_PROMPT_TYPE: Optional[str] = Field(
        default=None,
        description="CLI나 환경변수로 지정하는 프롬프트 타입"
    )

    # 데이터베이스 설정
    DATABASE_URL: str = Field(
        default="sqlite:///ragas_evaluation_history.db",
        description="평가 결과 저장용 데이터베이스 URL"
    )

    # 로그 설정
    LOG_LEVEL: str = Field(default="INFO", description="로그 레벨")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="로그 포맷"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 추가 필드 무시

    def get_prompt_type(self) -> PromptType:
        """설정된 프롬프트 타입을 PromptType enum으로 반환"""
        # CLI나 환경변수 설정이 우선
        prompt_type_str = self.RAGAS_PROMPT_TYPE or self.DEFAULT_PROMPT_TYPE
        
        try:
            return PromptType(prompt_type_str.lower())
        except ValueError:
            # 잘못된 값이면 기본값 사용
            return PromptType.DEFAULT

    def is_custom_prompt_enabled(self) -> bool:
        """커스텀 프롬프트 사용 여부 확인"""
        return self.get_prompt_type() != PromptType.DEFAULT


# 전역 설정 인스턴스
settings = Settings()


def get_prompt_type_from_env() -> PromptType:
    """환경변수에서 프롬프트 타입 가져오기"""
    return settings.get_prompt_type()


def set_prompt_type_for_session(prompt_type: PromptType):
    """세션용 프롬프트 타입 설정 (환경변수 오버라이드)"""
    os.environ["RAGAS_PROMPT_TYPE"] = prompt_type.value
    # settings 인스턴스 업데이트
    global settings
    settings = Settings()


def get_database_path() -> str:
    """데이터베이스 파일 경로 반환"""
    if settings.DATABASE_URL.startswith("sqlite:///"):
        return settings.DATABASE_URL[10:]  # "sqlite:///" 제거
    return "ragas_evaluation_history.db"  # 기본값


# 프롬프트 타입별 설명 (CLI 도움말용)
PROMPT_TYPE_HELP = {
    PromptType.DEFAULT: "기본 RAGAS 프롬프트 (영어, 범용)",
    PromptType.NUCLEAR_HYDRO_TECH: "원자력/수력 기술 문서 특화 프롬프트 (한영 혼용, 수식 포함)",
    PromptType.KOREAN_FORMAL: "한국어 공식 문서 프롬프트"
}


def validate_settings():
    """설정 유효성 검증"""
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY가 설정되지 않았습니다. .env 파일이나 환경변수를 확인하세요."
        )
    
    # HCX API 키는 선택 사항이므로, 사용할 경우에만 검증할 수 있도록 별도 함수나 로직 필요
    # if not settings.CLOVA_STUDIO_API_KEY:
    #     raise ValueError(
    #         "CLOVA_STUDIO_API_KEY가 설정되지 않았습니다. .env 파일이나 환경변수를 확인하세요."
    #     )

    # 프롬프트 타입 유효성 검증
    try:
        settings.get_prompt_type()
    except ValueError as e:
        raise ValueError(f"잘못된 프롬프트 타입 설정: {e}")
    
    return True