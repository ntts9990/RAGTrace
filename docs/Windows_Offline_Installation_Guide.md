# RAGTrace Windows 폐쇄망 설치 완전 가이드

## 📋 개요

이 가이드는 인터넷이 차단된 폐쇄망 환경의 Windows PC에서 RAGTrace를 설치하고 실행하는 완전한 과정을 안내합니다.

## 🔍 전체 프로세스

1. **준비 단계** (인터넷 연결된 PC에서)
2. **패키지 생성** (인터넷 연결된 PC에서)
3. **파일 이동** (폐쇄망으로)
4. **설치 단계** (폐쇄망 PC에서)
5. **검증 및 실행** (폐쇄망 PC에서)

---

## 1️⃣ 준비 단계 (인터넷 연결된 PC)

### 시스템 요구사항
- Windows 10/11 64비트
- Python 3.11 설치
- PowerShell 5.1 이상
- 관리자 권한
- 10GB 이상 디스크 공간

### 필수 소프트웨어 다운로드

#### 1. Python 3.11.9 설치파일
```
다운로드 URL: https://www.python.org/downloads/release/python-3119/
파일명: python-3.11.9-amd64.exe
크기: 약 30MB
```

#### 2. Visual C++ 재배포 가능 패키지
```
다운로드 URL: https://aka.ms/vs/17/release/vc_redist.x64.exe
파일명: vc_redist.x64.exe
크기: 약 14MB
```

#### 3. Git (소스코드 다운로드용)
```
다운로드 URL: https://git-scm.com/download/win
```

### RAGTrace 소스코드 준비
```bash
# GitHub에서 클론
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# 최신 업데이트 받기
git pull origin main
```

### UV 패키지 매니저 설치
```powershell
# PowerShell 관리자 권한으로 실행
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 설치 확인
uv --version
```

---

## 2️⃣ 패키지 생성 (인터넷 연결된 PC)

### 오프라인 패키지 생성
```powershell
# PowerShell을 관리자 권한으로 실행

# RAGTrace 디렉토리로 이동
cd C:\Users\[사용자명]\RAGTrace

# Python 버전 확인
python --version  # Python 3.11.x 확인

# 오프라인 패키지 생성 스크립트 실행
.\create-windows-offline-safe.ps1

# 소요 시간: 15-45분 (인터넷 속도에 따라 다름)
```

### 생성된 패키지 구조
```
RAGTrace-Windows-Offline/
├── 01_Prerequisites/          # Python, VC++ 설치파일 (수동 추가 필요)
│   ├── README.txt            # 설치파일 안내
│   ├── python-3.11.9-amd64.exe  # Python 설치파일 (수동 추가)
│   └── vc_redist.x64.exe        # VC++ 재배포 패키지 (수동 추가)
├── 02_Dependencies/           # Python 패키지들
│   ├── wheels/               # 200개 이상의 .whl 파일
│   ├── requirements.txt      # 의존성 목록
│   └── checksums.txt        # 무결성 검증 파일
├── 03_Source/                # RAGTrace 전체 소스코드
│   ├── src/                  # 메인 소스코드
│   ├── data/                 # 샘플 데이터셋
│   ├── docs/                 # 문서
│   ├── cli.py               # CLI 진입점
│   ├── run_dashboard.py     # 대시보드 진입점
│   └── .env.example         # 환경설정 템플릿
├── 04_Scripts/               # 설치 및 실행 스크립트
│   ├── install.bat          # 오프라인 설치 스크립트
│   ├── run-web.bat          # 웹 대시보드 실행
│   ├── run-cli.bat          # CLI 모드 실행
│   ├── verify.bat           # 설치 검증 실행
│   └── verify.py            # 설치 검증 스크립트
└── README-안전설치가이드.txt    # 한글 설치 가이드
```

### 패키지 압축
```powershell
# 생성된 패키지가 RAGTrace-Windows-Offline.zip으로 자동 압축됨
# 크기: 약 2-3GB (BGE-M3 모델 제외)
```

### 필수 파일 추가
```powershell
# 01_Prerequisites 폴더에 다운로드한 파일 복사
copy python-3.11.9-amd64.exe RAGTrace-Windows-Offline\01_Prerequisites\
copy vc_redist.x64.exe RAGTrace-Windows-Offline\01_Prerequisites\
```

---

## 3️⃣ 파일 이동 (폐쇄망으로)

### 이동해야 할 파일 목록
1. **RAGTrace-Windows-Offline.zip** - 생성된 오프라인 패키지 (약 2-3GB)
2. **python-3.11.9-amd64.exe** - Python 3.11 설치파일 (약 30MB)
3. **vc_redist.x64.exe** - Visual C++ 재배포 패키지 (약 14MB)
4. **BGE-M3 모델 폴더** - 로컬 임베딩용 (선택사항, 약 2GB)

### 폐쇄망 PC에서 준비
```powershell
# 작업 디렉토리 생성
mkdir C:\RAGTrace-Install
cd C:\RAGTrace-Install

# 패키지 압축 해제
# RAGTrace-Windows-Offline.zip을 이 위치에 압축 해제

# Prerequisites 폴더 확인
dir RAGTrace-Windows-Offline\01_Prerequisites
# python-3.11.9-amd64.exe와 vc_redist.x64.exe가 있어야 함
```

---

## 4️⃣ 설치 단계 (폐쇄망 PC)

### Step 1: Python 3.11 설치
```powershell
# 01_Prerequisites 폴더로 이동
cd C:\RAGTrace-Install\RAGTrace-Windows-Offline\01_Prerequisites

# Python 설치 실행
.\python-3.11.9-amd64.exe
```

**설치 옵션:**
- ✅ **"Add Python 3.11 to PATH"** - 반드시 체크
- ✅ **"Install for all users"** - 권장
- 설치 경로: 기본값 사용 권장
- 설치 완료 후 PC 재부팅 권장

**설치 확인:**
```powershell
# 새 PowerShell 창 열고 확인
python --version
# 출력: Python 3.11.9
```

### Step 2: Visual C++ 재배포 패키지 설치
```powershell
# 같은 폴더에서
.\vc_redist.x64.exe

# 기본 설정으로 설치 진행
```

### Step 3: RAGTrace 설치
```powershell
# PowerShell을 관리자 권한으로 실행

# RAGTrace 패키지 폴더로 이동
cd C:\RAGTrace-Install\RAGTrace-Windows-Offline

# 설치 스크립트 실행
.\04_Scripts\install.bat
```

**설치 과정:**
1. 관리자 권한 확인
2. Python 3.11 버전 확인
3. 작업 디렉토리 설정
4. Python 가상환경 생성
5. 오프라인 패키지 설치 (10-30분 소요)
6. 설치 완료 메시지

### Step 4: BGE-M3 모델 설정 (선택사항)
BGE-M3 로컬 임베딩을 사용하려면:

```powershell
# 모델 디렉토리 생성
cd C:\RAGTrace-Install\RAGTrace-Windows-Offline\03_Source
mkdir models

# BGE-M3 모델 복사 (별도 반입한 파일에서)
xcopy /E /I D:\BGE-M3모델폴더 models\bge-m3

# 복사 확인
dir models\bge-m3
# config.json, pytorch_model.bin 등의 파일이 보여야 함
```

### Step 5: 환경 설정
```powershell
# 03_Source 폴더로 이동
cd C:\RAGTrace-Install\RAGTrace-Windows-Offline\03_Source

# .env 파일 생성
copy .env.example .env

# 메모장으로 편집
notepad .env
```

**.env 파일 설정 예시:**
```ini
# Google Gemini API Key (필수)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Naver HCX API Key (선택사항)
CLOVA_STUDIO_API_KEY=your_hcx_api_key_here

# BGE-M3 로컬 모델 경로 (BGE-M3 사용시)
BGE_M3_MODEL_PATH="./models/bge-m3"

# 기본 설정
DEFAULT_LLM="gemini"
DEFAULT_EMBEDDING="bge_m3"  # 또는 "gemini" (온라인 임베딩)
```

---

## 5️⃣ 검증 및 실행

### 설치 검증
```powershell
# RAGTrace 패키지 폴더에서
cd C:\RAGTrace-Install\RAGTrace-Windows-Offline

# 검증 스크립트 실행
.\04_Scripts\verify.bat
```

**예상 출력:**
```
============================================================
  RAGTrace 오프라인 설치 검증 (안전 버전)
============================================================

🐍 Python: 3.11.9 ...
✅ Python 버전 OK
🔧 가상환경: ✅ 활성화됨

📦 핵심 패키지 확인:
   ✅ streamlit: 1.39.0
   ✅ pandas: 2.2.2
   ✅ numpy: 1.26.4
   ✅ torch: 2.5.1+cpu
   ✅ sentence_transformers: 3.3.1
   ✅ ragas: 0.2.15
   ✅ dependency_injector: 4.48.1
   ...

✅ 설치 검증 통과! RAGTrace 사용 가능
```

### BGE-M3 모델 테스트
```powershell
# Python에서 직접 테스트
cd 03_Source
.venv\Scripts\activate
python

>>> from pathlib import Path
>>> bge_path = Path("./models/bge-m3")
>>> print(f"BGE-M3 모델 존재: {bge_path.exists()}")
BGE-M3 모델 존재: True
>>> exit()
```

### RAGTrace 실행

#### 웹 대시보드 (권장)
```powershell
# 04_Scripts 폴더에서
.\run-web.bat
```

**웹 브라우저에서 접속:**
- URL: http://localhost:8501
- 자동으로 브라우저가 열리지 않으면 수동으로 접속

#### CLI 모드
```powershell
# 04_Scripts 폴더에서
.\run-cli.bat

# CLI 명령어 예시
python cli.py --help
python cli.py list-datasets
python cli.py evaluate evaluation_data --llm gemini --embedding bge_m3
```

---

## 🚨 문제 해결

### Python PATH 문제
```powershell
# Python이 인식되지 않는 경우
# 시스템 환경 변수에 수동 추가
set PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts

# 영구적으로 추가하려면 시스템 설정에서 환경 변수 편집
```

### 가상환경 활성화 실패
```powershell
# PowerShell 실행 정책 변경
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 수동으로 가상환경 활성화
cd 03_Source
.venv\Scripts\activate.bat
```

### BGE-M3 모델 경로 문제
```powershell
# 상대 경로가 작동하지 않으면 절대 경로 사용
# .env 파일에서:
BGE_M3_MODEL_PATH="C:\RAGTrace-Install\RAGTrace-Windows-Offline\03_Source\models\bge-m3"
```

### 패키지 설치 실패
```powershell
# 가상환경 활성화 후 개별 패키지 설치
cd 03_Source
.venv\Scripts\activate
pip install --no-index --find-links ..\02_Dependencies\wheels streamlit

# 전체 재설치
pip install --no-index --find-links ..\02_Dependencies\wheels -r ..\02_Dependencies\requirements.txt --force-reinstall
```

### 웹 대시보드 접속 불가
- Windows 방화벽에서 Python 허용 확인
- 다른 프로그램이 8501 포트 사용 중인지 확인
- `netstat -an | findstr 8501` 명령으로 포트 확인

### API 키 오류
- .env 파일의 API 키가 올바른지 확인
- 큰따옴표로 감싸져 있는지 확인
- 특수문자가 포함된 경우 이스케이프 처리

---

## 📌 추가 정보

### 디렉토리 구조
```
C:\RAGTrace-Install\
└── RAGTrace-Windows-Offline\
    ├── 01_Prerequisites\      # 설치 프로그램
    ├── 02_Dependencies\       # Python 패키지
    ├── 03_Source\            # RAGTrace 소스
    │   ├── .venv\           # 가상환경
    │   ├── models\          # BGE-M3 모델
    │   │   └── bge-m3\
    │   ├── data\            # 평가 데이터
    │   └── .env             # 환경 설정
    └── 04_Scripts\           # 실행 스크립트
```

### 로그 파일 위치
- 실행 로그: `03_Source\ragtrace.log`
- 에러 로그: Windows 이벤트 뷰어에서 확인

### 업데이트 방법
1. 새 버전의 오프라인 패키지 생성 (인터넷 PC에서)
2. 기존 설치 백업
3. 새 패키지로 덮어쓰기
4. .env 파일과 models 폴더는 보존

---

## 🆘 지원

문제가 지속되면:
1. `04_Scripts\verify.bat` 실행 결과 확인
2. 에러 메시지와 로그 파일 수집
3. GitHub Issues에 문제 보고: https://github.com/ntts9990/RAGTrace/issues

## 📄 관련 문서
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - 전체 설치 가이드
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 일반적인 문제 해결
- [BGE_M3_GPU_Guide.md](archive/BGE_M3_GPU_Guide.md) - BGE-M3 GPU 최적화