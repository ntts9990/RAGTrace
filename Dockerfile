FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# pyproject.toml과 소스 코드 복사
COPY pyproject.toml .
COPY src/ ./src/
COPY data/ ./data/
COPY run_dashboard.py .
COPY README.md .

# uv 설치 (더 빠른 패키지 관리)
RUN pip install uv

# 의존성 설치
RUN uv pip install --system -e .

# 포트 노출
EXPOSE 8501

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 비루트 사용자 생성 및 권한 설정
RUN useradd -m -u 1000 ragtrace && \
    chown -R ragtrace:ragtrace /app
USER ragtrace

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Streamlit 직접 실행
CMD ["streamlit", "run", "src/presentation/web/main.py", "--server.port=8501", "--server.address=0.0.0.0"]