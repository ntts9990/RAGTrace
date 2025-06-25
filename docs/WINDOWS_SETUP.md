# 🪟 Windows 설치 가이드

## 🎯 개요

RAGTrace Windows 설치는 두 가지 주요 시나리오를 지원합니다:
1. **인터넷 연결된 PC**: 오프라인 패키지 생성
2. **폐쇄망 PC**: 오프라인 패키지로 설치

## 📋 설치 방법 선택

| 상황 | 권장 방법 | 특징 |
|------|-----------|------|
| **인터넷 연결 + 일반 사용** | [자동 설치](#-자동-설치-인터넷-연결) | Python까지 자동 설치 |
| **PowerShell 문제** | [배치 스크립트](#-배치-스크립트-설치) | CMD 기반 백업 방법 |
| **폐쇄망 환경** | [오프라인 설치](#-오프라인-설치-폐쇄망) | 완전 자체 포함 패키지 |

---

## 🌐 자동 설치 (인터넷 연결)

깨끗한 Windows PC에서도 Python부터 자동으로 설치하는 완전 자동화 방법입니다.

### 사전 요구사항
- Windows 10/11
- 관리자 권한
- Git (선택사항, 없으면 ZIP 다운로드)

### 1단계: 저장소 받기

#### Git 사용 (권장)
```powershell
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace
```

#### ZIP 다운로드 (Git 없는 경우)
1. https://github.com/ntts9990/RAGTrace/archive/main.zip 다운로드
2. 압축 해제 후 폴더로 이동

### 2단계: 자동 설치 실행

#### PowerShell 방법 (권장)
```powershell
# 관리자 권한 PowerShell에서 실행
.\create-complete-offline.ps1 -Verbose
```

#### 실행 정책 문제 시
```powershell
# PowerShell 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 다시 실행
.\create-complete-offline.ps1 -Verbose
```

### 자동 설치 과정

스크립트는 다음을 자동으로 수행합니다:

1. **🔍 시스템 확인**
   - PowerShell 버전 호환성 확인
   - 관리자 권한 확인
   - 인터넷 연결 확인

2. **🐍 Python 자동 설치**
   - Python 3.11.9 자동 다운로드
   - 무인 설치 (PATH 자동 추가)
   - 설치 확인 및 검증

3. **⚡ UV 설치**
   - pip 업그레이드
   - UV 패키지 매니저 설치
   - 환경 변수 설정

4. **📦 패키지 생성**
   - 모든 Python 패키지 다운로드 (200+ 개)
   - RAGTrace 소스코드 패키징
   - BGE-M3 모델 다운로드 (선택)
   - 완전한 오프라인 패키지 생성

### 생성 결과

```
📁 RAGTrace-Complete-Offline/
├── 01_Dependencies/     # Python 패키지들 (.whl 파일)
├── 02_Source/          # RAGTrace 소스코드
├── 03_Models/          # BGE-M3 모델 (선택)
├── 04_Scripts/         # 설치 스크립트들
├── 05_Installers/      # Python, VC++ 설치파일
└── README-설치가이드.txt
```

---

## 💾 배치 스크립트 설치

PowerShell 호환성 문제가 있을 때 사용하는 백업 방법입니다.

### 실행 방법
```cmd
# 관리자 권한 CMD에서 실행
create-offline-simple.bat
```

### 수행 작업
- Python 3.11.9 자동 다운로드 및 설치
- UV 패키지 매니저 설치
- 기본 패키지들 다운로드
- 간단한 오프라인 패키지 생성

---

## 🔒 오프라인 설치 (폐쇄망)

인터넷이 차단된 환경에서 미리 생성된 패키지로 설치합니다.

### 사전 준비
1. 인터넷 PC에서 `RAGTrace-Complete-Offline` 패키지 생성
2. 폐쇄망 PC로 패키지 복사

### 설치 과정

#### 1단계: 패키지 배치
```cmd
# C:\에 복사 (권장)
C:\RAGTrace-Complete-Offline\
```

#### 2단계: 자동 설치 실행
```cmd
cd C:\RAGTrace-Complete-Offline\04_Scripts
00-install-all.bat
```

#### 3단계: 설치 순서 확인
자동 설치 스크립트는 다음 순서로 실행됩니다:

1. **01-install-python.bat** - Python 3.11.9 설치
2. **02-install-vcredist.bat** - Visual C++ 재배포 설치
3. **03-install-packages.bat** - RAGTrace 패키지 설치
4. **04-verify-installation.bat** - 설치 확인 및 테스트

#### 4단계: 실행
```cmd
# 웹 대시보드 실행
05-run-dashboard.bat

# CLI 테스트
06-test-cli.bat
```

---

## 🔧 환경 설정

### API 키 설정

RAGTrace 실행을 위해 API 키를 설정합니다:

#### 방법 1: .env 파일 (권장)
```cmd
cd 02_Source
copy .env.example .env
notepad .env
```

`.env` 파일 내용:
```bash
# 필수: Google Gemini API 키
GEMINI_API_KEY=your_gemini_api_key_here

# 선택: Naver HCX API 키
CLOVA_STUDIO_API_KEY=your_hcx_api_key_here

# 기본 설정 (선택사항)
DEFAULT_LLM=gemini
DEFAULT_EMBEDDING=bge_m3
```

#### 방법 2: 환경 변수
```cmd
# 시스템 환경 변수에 추가
setx GEMINI_API_KEY "your_key_here"
setx CLOVA_STUDIO_API_KEY "your_hcx_key_here"
```

### BGE-M3 로컬 모델 설정

#### 자동 설정 (오프라인 패키지 포함 시)
BGE-M3 모델이 패키지에 포함된 경우 자동으로 설정됩니다.

#### 수동 설정
```cmd
# models 폴더 생성
mkdir 02_Source\models\bge-m3

# 모델 파일 복사 (별도 다운로드한 경우)
xcopy /E /I bge-m3-files 02_Source\models\bge-m3\
```

---

## ⚡ 실행 방법

### 웹 대시보드 (권장)
```cmd
# 1. 스크립트 실행
05-run-dashboard.bat

# 2. 브라우저에서 접속
# http://localhost:8501
```

### CLI 사용
```cmd
# 기본 명령
cd 02_Source
python cli.py --help

# 평가 실행
python cli.py evaluate evaluation_data --llm gemini

# 데이터셋 목록
python cli.py list-datasets
```

### UV 사용 (설치된 경우)
```cmd
cd 02_Source

# 웹 대시보드
uv run streamlit run src/presentation/web/main.py

# CLI 평가
uv run python cli.py evaluate evaluation_data
```

---

## 🚨 문제 해결

### PowerShell 실행 정책 문제

**문제**: `execution policy` 오류
```powershell
# 해결: 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python PATH 문제

**문제**: `python is not recognized`
```cmd
# 해결: 수동 PATH 추가
set PATH=%PATH%;C:\Python311;C:\Python311\Scripts

# 영구 설정
setx PATH "%PATH%;C:\Python311;C:\Python311\Scripts"
```

### 관리자 권한 문제

**문제**: `Access is denied`
**해결**: 
1. PowerShell/CMD를 우클릭
2. "관리자 권한으로 실행" 선택

### 방화벽 문제

**문제**: 웹 대시보드 접속 불가
```cmd
# 해결: Windows 방화벽에서 Python 허용
# 또는 방화벽 규칙 추가
netsh advfirewall firewall add rule name="RAGTrace" dir=in action=allow protocol=TCP localport=8501
```

### 디스크 공간 부족

**문제**: 설치 중 공간 부족
**해결**:
- 최소 5GB 이상 확보
- 임시 파일 정리: `disk cleanup`
- BGE-M3 모델 제외 옵션 사용

### 네트워크 문제 (인터넷 PC)

**문제**: 패키지 다운로드 실패
```powershell
# 해결: 프록시 설정 확인
netsh winhttp show proxy

# pip 프록시 설정 (필요 시)
pip config set global.proxy http://proxy.company.com:8080
```

---

## 🔍 설치 확인

### 기본 확인
```cmd
cd 02_Source

# Python 버전 확인
python --version

# RAGTrace 버전 확인
python cli.py --version

# 패키지 확인
python -c "import streamlit; print('Streamlit OK')"
python -c "import torch; print('PyTorch OK')"
```

### 기능 테스트
```cmd
# 환경 테스트
python hello.py

# 간단한 평가 테스트
python cli.py evaluate evaluation_data_variant1 --llm gemini

# 웹 대시보드 테스트
python -m streamlit run src/presentation/web/main.py
```

---

## 📋 고급 설정

### 성능 최적화
```cmd
# BGE-M3 GPU 사용 (NVIDIA GPU 있는 경우)
set BGE_M3_DEVICE=cuda

# CPU 코어 수 설정
set UV_CONCURRENT_INSTALLS=4

# 메모리 사용량 제한
set PYTHONHASHSEED=0
```

### 보안 설정
```cmd
# 실행 정책 엄격하게 설정 (설치 후)
Set-ExecutionPolicy -ExecutionPolicy Restricted -Scope CurrentUser

# 불필요한 서비스 중지
net stop "Diagnostic Policy Service"
```

### 엔터프라이즈 배포
```cmd
# 무인 설치 모드
00-install-all.bat /quiet

# 로그 파일 생성
00-install-all.bat > install.log 2>&1

# 배치 배포 스크립트 생성
echo @echo off > deploy.bat
echo xcopy /E /I RAGTrace-Complete-Offline C:\RAGTrace\ >> deploy.bat
echo cd C:\RAGTrace\04_Scripts >> deploy.bat
echo call 00-install-all.bat >> deploy.bat
```

---

## 📞 지원 및 문의

### 일반적인 지원
- **GitHub Issues**: https://github.com/ntts9990/RAGTrace/issues
- **문서**: `docs/` 폴더의 추가 가이드들

### Windows 특화 지원
- **[문제 해결 가이드](TROUBLESHOOTING.md)**: 일반적인 문제 해결
- **[데이터 가이드](Data_Import_Guide.md)**: Excel/CSV 데이터 처리

### 진단 정보 수집
문제 신고 시 다음 정보를 포함해주세요:

```cmd
# 시스템 정보
systeminfo | findstr /B "OS Name OS Version"
python --version
uv --version

# 에러 로그
python hello.py > diagnostic.log 2>&1
```

---

## 🎯 다음 단계

Windows 설치가 완료되면:

1. **기본 사용법 익히기**
   - 웹 대시보드 탐색
   - 샘플 데이터로 평가 실행

2. **데이터 준비**
   - Excel/CSV 데이터 가져오기
   - 평가 데이터셋 구성

3. **평가 실행**
   - 다양한 LLM 모델 테스트
   - 결과 분석 및 보고서 생성

4. **고급 기능 활용**
   - 커스텀 프롬프트 설정
   - 배치 평가 실행
   - 결과 내보내기

Windows에서 RAGTrace를 성공적으로 활용하세요! 🚀