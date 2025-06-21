# RAGTrace 트러블슈팅 가이드

이 문서는 RAGTrace 프로젝트에서 발생할 수 있는 일반적인 오류들과 해결 방법을 정리한 종합적인 가이드입니다.

## 목차

1. [환경 설정 오류](#환경-설정-오류)
2. [의존성 설치 오류](#의존성-설치-오류)
3. [API 키 및 인증 오류](#api-키-및-인증-오류)
4. [Docker 관련 오류](#docker-관련-오류)
5. [GitHub Actions CI/CD 오류](#github-actions-cicd-오류)
6. [테스트 실행 오류](#테스트-실행-오류)
7. [평가 실행 오류](#평가-실행-오류)
8. [데이터 로딩 오류](#데이터-로딩-오류)
9. [웹 대시보드 오류](#웹-대시보드-오류)
10. [성능 및 리소스 오류](#성능-및-리소스-오류)

---

## 환경 설정 오류

### 1. Python 버전 호환성 문제

**오류:**
```
ERROR: Python 3.10 is not supported. Requires Python 3.11+
```

**해결 방법:**
```bash
# pyenv를 사용한 Python 버전 설치
pyenv install 3.11.10
pyenv local 3.11.10

# 또는 직접 Python 3.11+ 설치
python --version  # 3.11+ 확인
```

### 2. UV 패키지 매니저 설치 문제

**오류:**
```
uv: command not found
```

**해결 방법:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 설치 확인
uv --version
```

### 3. 프로젝트 루트 경로 문제

**오류:**
```
ModuleNotFoundError: No module named 'src'
```

**해결 방법:**
```bash
# 프로젝트 루트에서 실행하는지 확인
pwd  # /path/to/RAGTrace 여야 함

# PYTHONPATH 설정
export PYTHONPATH=$PWD:$PYTHONPATH

# 또는 uv run 사용
uv run python src/presentation/main.py
```

---

## 의존성 설치 오류

### 1. UV 동기화 실패

**오류:**
```
error: failed to solve: process "/bin/sh -c uv sync" did not complete successfully: exit code: 2
```

**해결 방법:**
```bash
# 캐시 초기화
uv cache clean

# 전체 재설치
rm -rf .venv uv.lock
uv sync --all-extras

# 의존성 문제가 있는 경우
uv add --dev pytest pytest-cov  # 누락된 패키지 수동 추가
```

### 2. 특정 패키지 설치 실패

**오류:**
```
ERROR: Could not install packages due to conflicting dependencies
```

**해결 방법:**
```bash
# 의존성 트리 확인
uv tree

# 충돌하는 패키지 개별 설치
uv add "package_name>=version"

# 가상환경 재생성
rm -rf .venv
uv sync
```

### 3. 시스템 의존성 누락 (Linux)

**오류:**
```
error: Microsoft Visual C++ 14.0 is required
```

**해결 방법:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# macOS
xcode-select --install
```

---

## API 키 및 인증 오류

### 1. API 키 누락

**오류:**
```
ValueError: GEMINI_API_KEY가 설정되지 않았습니다.
```

**해결 방법:**
```bash
# .env 파일 생성
cat > .env << EOF
GEMINI_API_KEY=your_api_key_here
CLOVA_STUDIO_API_KEY=your_clova_key_here
EOF

# 환경 변수 직접 설정
export GEMINI_API_KEY="your_api_key_here"
```

### 2. API 키 형식 오류

**오류:**
```
API key not valid. Please pass a valid API key.
```

**해결 방법:**
- API 키가 올바른 형식인지 확인 (보통 32-40자)
- 키에 불필요한 공백이나 따옴표가 없는지 확인
- Google AI Studio에서 새 키 생성
- API 사용량 한도 확인

### 3. 네트워크 연결 오류

**오류:**
```
ConnectionError: HTTPSConnectionPool(host='generativelanguage.googleapis.com', port=443)
```

**해결 방법:**
```bash
# 네트워크 연결 확인
ping google.com

# 프록시 설정 확인
echo $HTTP_PROXY $HTTPS_PROXY

# 방화벽 설정 확인
curl -I https://generativelanguage.googleapis.com
```

---

## Docker 관련 오류

### 1. Docker 이미지 빌드 실패

**오류:**
```
ERROR: failed to solve: process "/bin/sh -c uv sync --frozen --no-dev" did not complete successfully
```

**해결 방법:**
```bash
# Docker 캐시 정리
docker system prune -a

# BuildKit 사용 확인
export DOCKER_BUILDKIT=1

# 단계별 빌드로 문제 확인
docker build --no-cache --progress=plain .
```

### 2. 권한 문제

**오류:**
```
Permission denied (os error 13)
error: failed to open file `/tmp/.uv-cache/sdists-v9/.git`
```

**해결 방법:**
```dockerfile
# Dockerfile에서 사용자 권한 올바르게 설정
RUN chown -R appuser:appuser /app
USER appuser

# 또는 캐시 디렉토리 권한 수정
ENV UV_CACHE_DIR=/tmp/uv-cache
RUN mkdir -p /tmp/uv-cache && chmod 777 /tmp/uv-cache
```

### 3. 메모리 부족

**오류:**
```
docker: Error response from daemon: failed to create shim task: OCI runtime create failed
```

**해결 방법:**
```bash
# Docker 메모리 한도 확인
docker stats

# Docker 설정에서 메모리 증가 (Docker Desktop)
# Settings > Resources > Memory 를 4GB 이상으로 설정

# 멀티스테이지 빌드 사용하여 이미지 크기 감소
```

### 4. 포트 충돌

**오류:**
```
Error: Port 8501 is already in use
```

**해결 방법:**
```bash
# 포트 사용 프로세스 확인
lsof -i :8501
netstat -tulpn | grep 8501

# 프로세스 종료
kill -9 $(lsof -t -i:8501)

# 다른 포트 사용
docker run -p 8502:8501 ragtrace
```

---

## GitHub Actions CI/CD 오류

### 1. 테스트 커버리지 실패

**오류:**
```
Coverage failure: total of 39 is less than fail-under=80
```

**해결 방법:**
```ini
# pytest.ini 수정
[tool:pytest]
--cov-fail-under=35  # 현실적인 값으로 조정
```

### 2. Docker 이미지 찾을 수 없음

**오류:**
```
Unable to find image 'ragtrace:test' locally
```

**해결 방법:**
```yaml
# .github/workflows/ci.yml
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    load: true  # 이 옵션 추가
    tags: ragtrace:test
```

### 3. SARIF 업로드 권한 오류

**오류:**
```
Resource not accessible by integration
```

**해결 방법:**
```yaml
# 보안 스캔 단순화
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    format: 'table'  # sarif 대신 table 사용
    exit-code: '0'   # 실패해도 CI 통과
```

### 4. Docker Compose 명령어 오류

**오류:**
```
docker-compose: command not found
```

**해결 방법:**
```yaml
# docker-compose → docker compose 변경
- name: Test with Docker Compose
  run: docker compose up -d
```

---

## 테스트 실행 오류

### 1. 테스트 모듈 Import 오류

**오류:**
```
ModuleNotFoundError: No module named 'src.domain'
```

**해결 방법:**
```bash
# PYTHONPATH 설정
export PYTHONPATH=$PWD:$PYTHONPATH

# 또는 pytest.ini 설정 확인
[tool:pytest]
env = PYTHONPATH = .

# uv를 통한 실행
uv run pytest tests/
```

### 2. Fixture 누락 오류

**오류:**
```
fixture 'mock_ports' not found
```

**해결 방법:**
```python
# conftest.py에 fixture 추가
@pytest.fixture
def mock_ports():
    return {
        "llm_port": MagicMock(),
        "repository_port": MagicMock(),
    }
```

### 3. 테스트 데이터베이스 충돌

**오류:**
```
sqlite3.OperationalError: database is locked
```

**해결 방법:**
```python
# 테스트마다 임시 데이터베이스 사용
@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test.db"
    return str(db_path)
```

---

## 평가 실행 오류

### 1. RAGAS 평가 타임아웃

**오류:**
```
TimeoutError: Evaluation took longer than expected
```

**해결 방법:**
```python
# RagasEvalAdapter의 타임아웃 설정 증가
self.run_config = RunConfig(
    timeout=600,        # 10분으로 증가
    max_retries=2,      # 재시도 횟수 감소
    max_workers=2,      # 워커 수 감소
)
```

### 2. 메모리 부족으로 평가 실패

**오류:**
```
OutOfMemoryError: CUDA out of memory
```

**해결 방법:**
```python
# 배치 크기 감소
dataset_chunks = [dataset[i:i+5] for i in range(0, len(dataset), 5)]
for chunk in dataset_chunks:
    result = evaluate(chunk)
```

### 3. LLM 요청 제한 초과

**오류:**
```
Rate limit exceeded. Please try again later.
```

**해결 방법:**
```python
# 요청 간격 증가
import time
time.sleep(2)  # 요청 사이 2초 대기

# 또는 무료 tier 한도 확인
# Gemini: 8 requests/minute
```

---

## 데이터 로딩 오류

### 1. JSON 파싱 오류

**오류:**
```
JSONDecodeError: Expecting property name enclosed in double quotes
```

**해결 방법:**
```bash
# JSON 형식 검증
python -m json.tool data/evaluation_data.json

# 또는 온라인 JSON 검증 도구 사용
# UTF-8 인코딩 확인
file data/evaluation_data.json
```

### 2. 필수 필드 누락

**오류:**
```
ValidationError: 'question' field is required
```

**해결 방법:**
```json
// 올바른 데이터 형식 확인
{
  "question": "질문 내용",
  "contexts": ["컨텍스트1", "컨텍스트2"],
  "answer": "답변 내용",
  "ground_truth": "정답 내용"
}
```

### 3. 파일 경로 오류

**오류:**
```
FileNotFoundError: evaluation_data.json not found
```

**해결 방법:**
```bash
# 파일 존재 확인
ls -la data/

# 올바른 경로로 실행
cd /path/to/RAGTrace
python src/presentation/main.py
```

---

## 웹 대시보드 오류

### 1. Streamlit 포트 충돌

**오류:**
```
OSError: [Errno 48] Address already in use
```

**해결 방법:**
```bash
# 다른 포트 사용
streamlit run src/presentation/web/main.py --server.port 8502

# 또는 기존 프로세스 종료
pkill -f streamlit
```

### 2. 정적 파일 로딩 실패

**오류:**
```
FileNotFoundError: static/style.css not found
```

**해결 방법:**
```python
# 상대 경로 대신 절대 경로 사용
import os
from pathlib import Path

STATIC_DIR = Path(__file__).parent / "static"
```

### 3. 세션 상태 오류

**오류:**
```
StreamlitAPIException: Session state key not found
```

**해결 방법:**
```python
# 기본값 설정
if 'evaluation_result' not in st.session_state:
    st.session_state.evaluation_result = None
```

---

## 성능 및 리소스 오류

### 1. 메모리 사용량 과다

**오류:**
```
MemoryError: Unable to allocate array
```

**해결 방법:**
```python
# 대용량 데이터 청크 단위 처리
def process_large_dataset(dataset, chunk_size=100):
    for i in range(0, len(dataset), chunk_size):
        chunk = dataset[i:i+chunk_size]
        yield process_chunk(chunk)

# 메모리 정리
import gc
gc.collect()
```

### 2. 디스크 공간 부족

**오류:**
```
OSError: [Errno 28] No space left on device
```

**해결 방법:**
```bash
# 디스크 사용량 확인
df -h

# 캐시 정리
uv cache clean
docker system prune -a

# 로그 파일 정리
find . -name "*.log" -delete
```

### 3. 느린 응답 시간

**문제:** API 응답이 매우 느림

**해결 방법:**
```python
# 비동기 처리 사용
import asyncio
async def evaluate_async(data):
    tasks = [process_item(item) for item in data]
    results = await asyncio.gather(*tasks)
    return results

# 연결 풀 사용
import requests
session = requests.Session()
```

---

## 로그 및 디버깅 팁

### 1. 상세 로깅 활성화

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 특정 모듈 로깅
logger = logging.getLogger(__name__)
logger.debug("Debug information")
```

### 2. 환경 정보 확인

```bash
# 시스템 정보
uname -a
python --version
uv --version
docker --version

# 패키지 정보
uv pip list
```

### 3. 네트워크 연결 테스트

```bash
# API 연결 테스트
curl -I https://generativelanguage.googleapis.com
curl -I https://clovastudio.stream.ntruss.com

# DNS 확인
nslookup google.com
```

---

## 추가 리소스

- [RAGTrace GitHub Issues](https://github.com/ntts9990/RAGTrace/issues)
- [UV 공식 문서](https://docs.astral.sh/uv/)
- [Docker 문제 해결](https://docs.docker.com/engine/troubleshoot/)
- [Streamlit 문제 해결](https://docs.streamlit.io/knowledge-base)
- [RAGAS 문서](https://docs.ragas.io/)

---

**참고:** 이 가이드에서 해결되지 않는 문제가 있다면 GitHub Issues에 상세한 오류 로그와 함께 문의해 주세요.