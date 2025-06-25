# 🔧 RAGTrace Windows 완전 설치 가이드

**엔터프라이즈급 Windows 환경을 위한 종합 설치 안내서**

이 가이드는 Windows 환경에서 RAGTrace를 설치하고 실행하는 모든 방법을 다룹니다. 인터넷 연결 환경부터 완전 폐쇄망 환경까지 모든 시나리오를 지원합니다.

## 📋 목차

1. [빠른 설치 (인터넷 연결 환경)](#1-빠른-설치-인터넷-연결-환경)
2. [완전 오프라인 설치 (폐쇄망 환경)](#2-완전-오프라인-설치-폐쇄망-환경)
3. [Git 클론 후 프로젝트 내부 설치](#3-git-클론-후-프로젝트-내부-설치)
4. [BGE-M3 로컬 모델 설정](#4-bge-m3-로컬-모델-설정)
5. [문제 해결 및 검증](#5-문제-해결-및-검증)

---

## 1. 빠른 설치 (인터넷 연결 환경)

### 🎯 1분만에 시작하기

**시스템 요구사항:**
- Windows 10/11 64비트
- Python 3.11+ 
- 10GB 디스크 공간
- 8GB RAM

**설치 과정:**

```powershell
# 1. 프로젝트 클론
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# 2. UV 패키지 매니저 설치
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 3. 의존성 설치
uv sync --all-extras

# 4. API 키 설정
copy .env.example .env
# 메모장으로 .env 편집하여 API 키 입력

# 5. BGE-M3 모델 자동 다운로드 및 준비
uv run python hello.py --prepare-models

# 6. 즉시 실행
uv run streamlit run src/presentation/web/main.py
```

**브라우저에서 http://localhost:8501 접속**

---

## 2. 완전 오프라인 설치 (폐쇄망 환경)

### 📦 사전 준비 (인터넷 연결된 PC에서)

#### Step 1: 필수 소프트웨어 다운로드

1. **Python 3.11.9 설치파일**
   ```
   다운로드: https://www.python.org/downloads/release/python-3119/
   파일명: python-3.11.9-amd64.exe
   크기: 약 30MB
   ```

2. **Visual C++ 재배포 가능 패키지**
   ```
   다운로드: https://aka.ms/vs/17/release/vc_redist.x64.exe
   파일명: vc_redist.x64.exe
   크기: 약 14MB
   ```

3. **RAGTrace 소스코드**
   ```powershell
   git clone https://github.com/ntts9990/RAGTrace.git
   cd RAGTrace
   ```

#### Step 2: 오프라인 패키지 생성

```powershell
# PowerShell을 관리자 권한으로 실행
cd RAGTrace

# 안전한 오프라인 패키지 생성
.\create-windows-offline-safe.ps1

# 생성 완료 후 다음 파일들이 생성됨:
# - RAGTrace-Windows-Offline.zip (약 2-3GB)
# - 패키지 구조가 자동으로 생성됨
```

#### Step 3: 필수 파일 추가

패키지 생성 후 다음 파일들을 수동으로 추가:

```powershell
# 압축 해제 후
Expand-Archive RAGTrace-Windows-Offline.zip -DestinationPath .

# 01_Prerequisites 폴더에 다운로드한 파일 복사
copy python-3.11.9-amd64.exe RAGTrace-Windows-Offline\01_Prerequisites\
copy vc_redist.x64.exe RAGTrace-Windows-Offline\01_Prerequisites\

# 필수 파일 확인
dir RAGTrace-Windows-Offline\01_Prerequisites\
# python-3.11.9-amd64.exe와 vc_redist.x64.exe가 있어야 함

# 최종 패키지 재압축 (선택사항)
Compress-Archive -Path RAGTrace-Windows-Offline -DestinationPath RAGTrace-Windows-Complete.zip
```

### 🔧 폐쇄망 설치 과정

#### Step 1: 패키지 이동 및 압축 해제

```powershell
# 폐쇄망 PC에서
mkdir C:\RAGTrace-Install
cd C:\RAGTrace-Install

# RAGTrace-Windows-Offline.zip (또는 Complete.zip)을 이 위치에 압축 해제
Expand-Archive RAGTrace-Windows-Offline.zip -DestinationPath .

# 압축 해제 후 폴더 구조 확인
dir RAGTrace-Windows-Offline
# 01_Prerequisites, 02_Dependencies, 03_Source, 04_Scripts 폴더가 있어야 함
```

#### Step 2: Python 3.11 설치

```powershell
# 01_Prerequisites 폴더로 이동
cd RAGTrace-Windows-Offline\01_Prerequisites

# Python 설치 실행
.\python-3.11.9-amd64.exe
```

**⚠️ 중요 설치 옵션:**
- ✅ **"Add Python 3.11 to PATH"** - 반드시 체크
- ✅ **"Install for all users"** - 권장
- 설치 완료 후 PC 재부팅

**설치 확인:**
```powershell
# 새 PowerShell 창에서 확인
python --version
# 출력: Python 3.11.9
```

#### Step 3: Visual C++ 재배포 패키지 설치

```powershell
# 같은 폴더에서
.\vc_redist.x64.exe
# 기본 설정으로 설치 진행
```

#### Step 4: RAGTrace 오프라인 설치

```powershell
# PowerShell을 관리자 권한으로 실행
cd C:\RAGTrace-Install\RAGTrace-Windows-Offline

# 안전한 설치 스크립트 실행
.\04_Scripts\install.bat
```

**설치 과정 상세:**
1. 관리자 권한 자동 확인
2. Python 3.11 버전 검증
3. 가상환경 생성 (`.venv`)
4. 오프라인 패키지 설치 (10-30분 소요)
5. 설치 완료 확인

#### Step 5: 환경 설정

```powershell
# 03_Source 폴더로 이동
cd 03_Source

# .env 파일 생성
copy .env.example .env

# 메모장으로 .env 편집
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

#### Step 6: 설치 검증

```powershell
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

✅ 설치 검증 통과! RAGTrace 사용 가능
```

#### Step 7: 실행

**웹 대시보드 (권장):**
```powershell
.\04_Scripts\run-web.bat
# 브라우저에서 http://localhost:8501 접속
```

**CLI 모드:**
```powershell
.\04_Scripts\run-cli.bat
# CLI 명령어 사용 가능
```

---

## 3. Git 클론 후 프로젝트 내부 설치

### 🚀 Git 클론 후 완전 오프라인 설치

이 방법은 Git으로 소스코드를 받은 후, 프로젝트 내부 스크립트만으로 완전 설치하는 방법입니다.

#### Step 1: 소스코드 클론

```powershell
# Git으로 소스코드 클론
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace
```

#### Step 2: Windows 오프라인 패키지 생성

```powershell
# PowerShell 관리자 권한으로 실행
.\create-windows-offline-safe.ps1

# 자동으로 다음이 수행됨:
# - 시스템 요구사항 검증
# - Python 패키지 다운로드
# - 설치 스크립트 생성
# - 완전 오프라인 패키지 생성
```

#### Step 3: 생성된 패키지 구조

```
RAGTrace-Windows-Offline/
├── 01_Prerequisites/          # Python, VC++ 설치파일 (수동 추가 필요)
│   ├── README.txt            # 설치파일 안내
│   ├── python-3.11.9-amd64.exe  # Python 설치파일 (수동 추가)
│   └── vc_redist.x64.exe        # VC++ 재배포 패키지 (수동 추가)
├── 02_Dependencies/           # Python 패키지들 (자동 생성)
│   ├── wheels/               # 200개 이상의 .whl 파일
│   ├── requirements.txt      # 의존성 목록
│   └── checksums.txt        # 무결성 검증 파일
├── 03_Source/                # RAGTrace 전체 소스코드 (자동 복사)
│   ├── src/                  # 메인 소스코드
│   ├── data/                 # 샘플 데이터셋
│   ├── docs/                 # 문서
│   ├── cli.py               # CLI 진입점
│   ├── run_dashboard.py     # 대시보드 진입점
│   └── .env.example         # 환경설정 템플릿
├── 04_Scripts/               # 설치 및 실행 스크립트 (자동 생성)
│   ├── install.bat          # 오프라인 설치 스크립트
│   ├── run-web.bat          # 웹 대시보드 실행
│   ├── run-cli.bat          # CLI 모드 실행
│   ├── verify.bat           # 설치 검증 실행
│   └── verify.py            # 설치 검증 스크립트
└── README-안전설치가이드.txt    # 한글 설치 가이드
```

#### Step 4: 필수 파일 추가

**인터넷 연결된 PC에서 다운로드:**

1. **Python 3.11.9**: https://www.python.org/downloads/release/python-3119/
2. **VC++ 재배포 패키지**: https://aka.ms/vs/17/release/vc_redist.x64.exe

```powershell
# 다운로드한 파일을 01_Prerequisites 폴더에 복사
copy python-3.11.9-amd64.exe RAGTrace-Windows-Offline\01_Prerequisites\
copy vc_redist.x64.exe RAGTrace-Windows-Offline\01_Prerequisites\
```

#### Step 5: 완전 설치 실행

**폐쇄망 환경에서:**

```powershell
# 전체 패키지를 폐쇄망으로 이동 후
cd RAGTrace-Windows-Offline

# 1. Python 설치
01_Prerequisites\python-3.11.9-amd64.exe
# ⚠️ "Add Python to PATH" 반드시 체크

# 2. VC++ 설치
01_Prerequisites\vc_redist.x64.exe

# 3. PC 재부팅 (권장)

# 4. RAGTrace 설치 (관리자 권한 PowerShell)
04_Scripts\install.bat

# 5. 환경 설정
cd 03_Source
copy .env.example .env
notepad .env  # API 키 입력

# 6. 설치 검증
..\04_Scripts\verify.bat

# 7. 실행
..\04_Scripts\run-web.bat
```

### 🎯 완전 자동화된 설치 과정

프로젝트 내부 스크립트는 다음을 자동으로 처리합니다:

1. **시스템 검증**
   - 관리자 권한 확인
   - Python 3.11 버전 확인
   - 디스크 공간 및 메모리 확인

2. **가상환경 설정**
   - `.venv` 가상환경 생성
   - 가상환경 자동 활성화

3. **패키지 설치**
   - 오프라인 wheel 파일에서 설치
   - 의존성 자동 해결
   - 설치 진행률 표시

4. **검증 및 테스트**
   - 핵심 패키지 설치 확인
   - PyTorch CPU 버전 확인
   - RAGTrace 기능 테스트

---

## 4. BGE-M3 로컬 모델 설정

### 📥 BGE-M3 모델 준비

BGE-M3는 완전 오프라인 임베딩 처리를 위한 로컬 모델입니다.

#### 방법 1: 자동 다운로드 (인터넷 연결 시)

```powershell
# RAGTrace 프로젝트 루트에서
uv run python hello.py --prepare-models

# 자동으로 다음이 수행됨:
# - models/bge-m3/ 폴더 생성
# - Hugging Face에서 BGE-M3 모델 다운로드 (약 2GB)
# - GPU/CPU 자동 감지 및 최적화
# - .env 파일 자동 업데이트
```

#### 방법 2: 오프라인 설치 (폐쇄망 환경)

**인터넷 연결된 PC에서:**
```bash
# BGE-M3 모델 다운로드
git lfs clone https://huggingface.co/BAAI/bge-m3

# 또는 Python으로
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')
model.save('./bge-m3-download')
"
```

**폐쇄망 PC에서:**
```powershell
# RAGTrace 설치 디렉토리에서
cd 03_Source  # 또는 RAGTrace 루트
mkdir models
xcopy /E /I D:\bge-m3-download models\bge-m3

# 모델 파일 확인
dir models\bge-m3
# config.json, pytorch_model.bin 등이 있어야 함
```

#### BGE-M3 설정 확인

```powershell
# .env 파일에서 BGE-M3 경로 설정
echo BGE_M3_MODEL_PATH="./models/bge-m3" >> .env
echo DEFAULT_EMBEDDING="bge_m3" >> .env

# BGE-M3 모델 테스트
cd 03_Source
.venv\Scripts\activate
python -c "
from pathlib import Path
bge_path = Path('./models/bge-m3')
print(f'BGE-M3 모델 존재: {bge_path.exists()}')
if bge_path.exists():
    print('모델 파일들:')
    for f in bge_path.glob('*'):
        print(f'  {f.name}')
"
```

### 🚀 BGE-M3 성능 최적화

```powershell
# GPU 사용 (CUDA 가능 시)
echo BGE_M3_DEVICE="cuda" >> .env

# Apple Silicon MPS 사용 (macOS)
echo BGE_M3_DEVICE="mps" >> .env

# CPU 전용 (안전한 설정)
echo BGE_M3_DEVICE="cpu" >> .env

# 자동 감지 (권장)
echo BGE_M3_DEVICE="auto" >> .env
```

**성능 벤치마크:**
- **CUDA GPU**: ~60 docs/sec
- **MPS (Apple Silicon)**: ~15 docs/sec  
- **CPU (멀티코어)**: ~40 docs/sec

---

## 5. 문제 해결 및 검증

### 🔍 설치 상태 확인

#### 종합 시스템 검증

```powershell
# 모든 구성 요소 확인
.\04_Scripts\verify.bat

# 또는 수동 확인
cd 03_Source
.venv\Scripts\activate
python cli.py --help
```

#### 개별 구성 요소 테스트

```powershell
# Python 버전 확인
python --version

# 가상환경 확인
.venv\Scripts\activate
pip list | findstr streamlit

# BGE-M3 모델 확인
python -c "
import torch
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('./models/bge-m3')
print('BGE-M3 로드 성공!')
"

# 웹 대시보드 테스트
python -c "
import streamlit as st
print('Streamlit 정상 로드')
"
```

### 🚨 일반적인 문제 해결

#### 1. Python PATH 문제

```powershell
# Python이 인식되지 않는 경우
where python
# 출력이 없으면 PATH 설정 필요

# 환경 변수 수동 추가
$env:PATH += ";C:\Program Files\Python311;C:\Program Files\Python311\Scripts"

# 영구적 설정 (시스템 환경 변수 편집)
# 제어판 → 시스템 → 고급 시스템 설정 → 환경 변수
```

#### 2. PowerShell 실행 정책 오류

```powershell
# 실행 정책 변경 (관리자 권한)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 또는 일회성 실행
powershell -ExecutionPolicy Bypass -File install.bat
```

#### 3. 가상환경 활성화 실패

```powershell
# 수동 활성화
cd 03_Source
.venv\Scripts\activate.bat

# 가상환경 재생성
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate
```

#### 4. 패키지 설치 실패

```powershell
# 가상환경에서 개별 설치
.venv\Scripts\activate
pip install --no-index --find-links ..\02_Dependencies\wheels streamlit

# 전체 재설치
pip install --no-index --find-links ..\02_Dependencies\wheels -r ..\02_Dependencies\requirements.txt --force-reinstall
```

#### 5. 웹 대시보드 접속 불가

```powershell
# 포트 사용 확인
netstat -an | findstr 8501

# 방화벽 허용 설정
# Windows 방화벽에서 Python 허용

# 수동 브라우저 접속
start http://localhost:8501
```

#### 6. BGE-M3 메모리 부족

```ini
# .env 파일에서 CPU 모드 강제
BGE_M3_DEVICE="cpu"

# 배치 크기 감소
BGE_M3_BATCH_SIZE=4
```

### 📞 긴급 지원

#### 자동 진단

```powershell
# 종합 진단 실행
python -c "
import sys, platform, subprocess
print(f'Platform: {platform.platform()}')
print(f'Python: {sys.version}')
try:
    result = subprocess.run(['python', '-m', 'pip', 'list'], capture_output=True, text=True)
    print(f'설치된 패키지: {len(result.stdout.splitlines())}개')
except Exception as e:
    print(f'패키지 확인 실패: {e}')
"

# 로그 확인
Get-Content -Tail 50 ..\02_Dependencies\download.log  # 있는 경우
```

#### 자동 복구

```powershell
# 설치 초기화 및 재설치
rmdir /s /q 03_Source\.venv
.\04_Scripts\install.bat

# 캐시 정리 (UV 사용 시)
uv cache clean
uv sync --all-extras
```

### 📚 추가 지원 리소스

| 문제 유형 | 해결 방법 |
|----------|-----------|
| **설치 실패** | `.\04_Scripts\install.bat` 재실행 |
| **실행 오류** | `.\04_Scripts\verify.bat` 실행 후 로그 확인 |
| **성능 문제** | BGE-M3 CPU 모드 설정 |
| **네트워크 오류** | 완전 오프라인 모드 확인 |
| **권한 문제** | 관리자 권한으로 PowerShell 실행 |

---

## 🎯 설치 성공 확인

모든 설치가 완료되면 다음을 확인하세요:

### ✅ 최종 체크리스트

1. **Python 설치 확인**
   ```powershell
   python --version
   # Python 3.11.x 출력
   ```

2. **가상환경 활성화 확인**
   ```powershell
   .venv\Scripts\activate
   # 프롬프트에 (.venv) 표시
   ```

3. **RAGTrace 패키지 확인**
   ```powershell
   python cli.py --help
   # CLI 도움말 출력
   ```

4. **웹 대시보드 실행 확인**
   ```powershell
   .\04_Scripts\run-web.bat
   # http://localhost:8501 접속 가능
   ```

5. **BGE-M3 모델 확인** (선택사항)
   ```powershell
   python -c "from pathlib import Path; print(Path('./models/bge-m3').exists())"
   # True 출력
   ```

6. **API 키 설정 확인**
   ```powershell
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print('Gemini API Key:', bool(os.getenv('GEMINI_API_KEY')))
   "
   # True 출력
   ```

### 🚀 설치 완료 후 첫 실행

```powershell
# 웹 대시보드 실행
.\04_Scripts\run-web.bat

# 브라우저에서 http://localhost:8501 접속

# 첫 평가 실행
# 1. 웹 UI에서 데이터 업로드
# 2. LLM 및 임베딩 모델 선택
# 3. 평가 실행 버튼 클릭
# 4. 결과 확인 및 분석
```

---

**🎉 축하합니다! RAGTrace Windows 설치가 완료되었습니다.**

이제 엔터프라이즈급 RAG 시스템 평가를 시작할 수 있습니다. 웹 대시보드에서 직관적인 UI로 평가를 수행하거나, CLI에서 자동화된 평가를 실행할 수 있습니다.

**지원 및 문의:**
- **GitHub Issues**: https://github.com/ntts9990/RAGTrace/issues
- **설치 검증**: `.\04_Scripts\verify.bat` 실행
- **상세 문서**: `docs/` 폴더의 추가 가이드 참조