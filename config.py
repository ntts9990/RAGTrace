import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 향후 HCX-005 등 다른 모델을 위한 설정 추가 가능
# HCX_API_ENDPOINT = os.getenv("HCX_API_ENDPOINT") 