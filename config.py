import os
from dotenv import load_dotenv
from src.utils.paths import ENV_FILE_PATH, DATABASE_PATH as DB_PATH

# 명시적으로 프로젝트 루트의 .env 파일 로드
load_dotenv(dotenv_path=ENV_FILE_PATH)

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini 모델 설정
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-preview-05-20")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL",
                                   "models/gemini-embedding-exp-03-07")

# Rate Limiting 설정
GEMINI_REQUESTS_PER_MINUTE = int(os.getenv("GEMINI_REQUESTS_PER_MINUTE", "8"))
EMBEDDING_REQUESTS_PER_MINUTE = int(os.getenv("EMBEDDING_REQUESTS_PER_MINUTE", "10"))

# 데이터베이스 설정 (중앙 경로 관리 모듈 사용)
# 환경 변수로 오버라이드 가능하지만 기본값은 중앙 경로 사용
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DB_PATH))

# 향후 HCX-005 등 다른 모델을 위한 설정 추가 가능
# HCX_API_ENDPOINT = os.getenv("HCX_API_ENDPOINT")
