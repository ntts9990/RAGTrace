# RAGTrace 설치 가이드

## 🎯 개요

RAGTrace는 다양한 환경에서 설치할 수 있도록 여러 가지 설치 방법을 제공합니다. 환경에 따라 최적의 설치 방법을 선택하세요.

## 📋 설치 방법 선택 가이드

| 환경 | 권장 방법 | 특징 |
|------|-----------|------|
| **일반 개발환경** | [UV 설치](#-uv-설치-권장) | 빠르고 안정적 |
| **Windows PC** | [Windows 자동설치](#-windows-자동-설치) | Python까지 자동 설치 |
| **Docker 환경** | [Docker 설치](#-docker-설치) | 컨테이너 기반 |
| **폐쇄망 환경** | [오프라인 설치](#-오프라인-설치) | 인터넷 불필요 |

---

## ⚡ UV 설치 (권장)

### 사전 요구사항
- Python 3.11+
- Git

### 1단계: UV 설치
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell  
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# pip 사용 (모든 OS)
pip install uv

# Homebrew (macOS)
brew install uv
```

### 2단계: RAGTrace 설치
```bash
# 저장소 클론
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# 자동 환경 설정
chmod +x uv-setup.sh
./uv-setup.sh

# 또는 수동 설치
uv sync --all-extras
```

### 3단계: 환경 설정
```bash
# API 키 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 입력

# BGE-M3 모델 자동 다운로드 (최초 한 번, 약 2GB)
uv run python hello.py --prepare-models
```

### 4단계: 실행
```bash
# 웹 대시보드 실행
uv run streamlit run src/presentation/web/main.py

# CLI 사용
uv run python cli.py evaluate evaluation_data
```

---

## 🪟 Windows 자동 설치

Windows에서는 Python부터 RAGTrace까지 모든 것을 자동으로 설치할 수 있습니다.

### 인터넷 연결된 PC

#### 자동 설치 (권장)
```powershell
# 1. 저장소 클론 (Git 필요)
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# 2. 관리자 권한 PowerShell에서 실행
.\create-complete-offline.ps1 -Verbose
```

**자동으로 수행되는 작업:**
- ✅ PowerShell 호환성 확인
- ✅ Python 3.11.9 자동 다운로드 및 설치
- ✅ UV 패키지 매니저 자동 설치
- ✅ 모든 의존성 패키지 설치
- ✅ BGE-M3 모델 다운로드 (선택)

#### 간단한 설치 (PowerShell 문제 시)
```cmd
# 관리자 권한 CMD에서 실행
create-offline-simple.bat
```

### 폐쇄망 PC

1. **오프라인 패키지 복사**
   - 인터넷 PC에서 생성된 `RAGTrace-Complete-Offline` 폴더 복사

2. **자동 설치 실행**
   ```cmd
   cd RAGTrace-Complete-Offline\04_Scripts
   00-install-all.bat
   ```

3. **실행**
   ```cmd
   05-run-dashboard.bat
   ```

---

## 🐳 Docker 설치

### Docker Compose (권장)
```bash
# 저장소 클론
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# 환경 설정
cp .env.example .env
# .env 파일 편집

# 실행
docker-compose up -d

# 접속
open http://localhost:8501
```

### 직접 Docker 실행
```bash
# 이미지 빌드
docker build -t ragtrace .

# 컨테이너 실행
docker run -p 8501:8501 --env-file .env ragtrace
```

---

## 🔒 오프라인 설치 (엔터프라이즈)

폐쇄망 환경에서 사용할 완전한 오프라인 패키지를 생성합니다.

### 인터넷 PC에서 패키지 생성

#### Linux/macOS
```bash
# 저장소 클론
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# 오프라인 패키지 생성
./scripts/create-offline-package.sh

# BGE-M3 포함 (대용량)
./scripts/create-offline-package.sh --include-bge
```

#### Windows
```powershell
# PowerShell 관리자 권한
.\create-complete-offline.ps1 -IncludeBGE -Verbose
```

### 폐쇄망에서 설치

1. **패키지 복사**
   ```bash
   # 생성된 패키지를 폐쇄망으로 복사
   scp RAGTrace-Offline-*.tar.gz target-machine:/tmp/
   ```

2. **설치 실행**
   ```bash
   # 압축 해제
   tar -xzf RAGTrace-Offline-*.tar.gz
   cd RAGTrace-Offline

   # 자동 설치
   ./install.sh

   # 실행
   ./run.sh
   ```

---

## 📋 환경별 상세 설정

### API 키 설정

RAGTrace는 다음 API 키들을 지원합니다:

```bash
# .env 파일에 추가
GEMINI_API_KEY=your_gemini_api_key_here
CLOVA_STUDIO_API_KEY=your_hcx_api_key_here  # 선택사항

# 기본 모델 설정 (선택사항)
DEFAULT_LLM=gemini  # 또는 hcx
DEFAULT_EMBEDDING=bge_m3  # 또는 gemini, hcx
```

### BGE-M3 로컬 모델 설정

```bash
# 자동 다운로드 (권장)
uv run python hello.py --prepare-models

# 수동 설정
mkdir -p models
# models/ 폴더에 BGE-M3 모델 파일 복사

# 환경 변수 설정 (선택사항)
BGE_M3_MODEL_PATH="./models/bge-m3"
```

### UV 설정 최적화

```bash
# UV 캐시 설정
export UV_CACHE_DIR="$HOME/.cache/uv"

# 병렬 설치 최적화
export UV_CONCURRENT_INSTALLS=10

# 오프라인 모드 (폐쇄망)
export UV_OFFLINE=1
```

---

## 🔧 설치 확인 및 테스트

### 기본 확인
```bash
# 환경 테스트
uv run python hello.py

# 컨테이너 설정 확인
uv run python -c "from src.container import container; print('✅ Container OK')"

# 데이터셋 확인
uv run python cli.py list-datasets
```

### 평가 테스트
```bash
# 간단한 평가 실행
uv run python cli.py evaluate evaluation_data_variant1 --llm gemini

# 웹 대시보드 테스트
uv run streamlit run src/presentation/web/main.py
```

---

## 🚨 문제 해결

일반적인 설치 문제는 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)를 참조하세요.

### 빠른 해결책

```bash
# UV 캐시 정리
uv cache clean

# 의존성 재설치
uv sync --all-extras --reinstall

# Python 환경 재생성
uv python install 3.11
```

### Windows 특화 문제

```powershell
# PowerShell 실행 정책 설정
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Python PATH 수동 추가
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Python311;C:\Python311\Scripts", "User")
```

---

## 📞 지원

- **GitHub Issues**: https://github.com/ntts9990/RAGTrace/issues  
- **문서**: `docs/` 폴더의 상세 가이드들
- **예제**: `data/` 폴더의 샘플 데이터

---

## 🎯 다음 단계

설치가 완료되면:

1. **[사용자 가이드](README.md)** - 기본 사용법
2. **[메트릭 가이드](RAGTRACE_METRICS.md)** - 평가 지표 이해
3. **[데이터 가이드](Data_Import_Guide.md)** - 데이터 준비 방법
4. **[아키텍처 가이드](ARCHITECTURE_AND_DEVELOPMENT.md)** - 개발 및 확장

RAGTrace로 효과적인 RAG 시스템 평가를 시작하세요! 🚀