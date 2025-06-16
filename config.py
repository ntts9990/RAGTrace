import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini 모델 설정
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-preview-05-20")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL",
                                   "models/gemini-embedding-exp-03-07")

# Rate Limiting 설정
GEMINI_REQUESTS_PER_MINUTE = int(os.getenv("GEMINI_REQUESTS_PER_MINUTE", "8"))
EMBEDDING_REQUESTS_PER_MINUTE = int(os.getenv("EMBEDDING_REQUESTS_PER_MINUTE", "10"))

# 데이터베이스 설정
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/db/evaluations.db")

# 향후 HCX-005 등 다른 모델을 위한 설정 추가 가능
# HCX_API_ENDPOINT = os.getenv("HCX_API_ENDPOINT")
