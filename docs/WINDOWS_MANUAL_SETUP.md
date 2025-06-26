# 🪟 Windows 수동 설치 가이드

PowerShell 자동 스크립트에서 문제가 발생할 때 사용하는 **완전 수동 설치 가이드**입니다.  
모든 단계를 하나씩 직접 실행하면서 진행할 수 있습니다.

## 🎯 이 가이드를 사용하는 경우

- ✅ PowerShell 스크립트 실행 시 오류 발생
- ✅ 자동 설치보다 단계별 제어가 필요한 경우
- ✅ 엔터프라이즈 환경에서 보안 정책상 스크립트 실행 불가
- ✅ 설치 과정을 완전히 이해하고 싶은 경우

---

## 📋 설치 과정 개요

### 🌐 인터넷 연결된 PC (패키지 생성용)
1. [사전 준비](#1-사전-준비)
2. [Git 설치](#2-git-설치)
3. [Python 수동 설치](#3-python-수동-설치)
4. [UV 설치](#4-uv-설치)
5. [RAGTrace 다운로드](#5-ragtrace-다운로드)
6. [오프라인 패키지 수동 생성](#6-오프라인-패키지-수동-생성)

### 🔒 폐쇄망 PC (실제 사용 환경)
1. [오프라인 패키지 복사](#폐쇄망-pc-설치)
2. [Python 설치](#폐쇄망-python-설치)
3. [가상환경 생성 및 활성화](#폐쇄망-가상환경-설정)
4. [RAGTrace 패키지 설치](#폐쇄망-ragtrace-설치)
5. [실행 및 확인](#폐쇄망-실행-확인)

---

## 🌐 인터넷 연결된 PC - 패키지 생성

### 1. 사전 준비

#### 1-1. 관리자 권한 확인
```cmd
# 1. Windows 키 + R 누르기
# 2. "cmd" 입력 후 Ctrl + Shift + Enter (관리자 권한)
# 3. 다음 명령으로 확인
whoami /groups | find "Administrator"
```

**결과가 나오면 관리자 권한 ✅**  
**결과가 없으면 일반 사용자 ❌ → 관리자로 재실행 필요**

#### 1-2. 작업 폴더 생성
```cmd
# C:\에 작업 폴더 생성
cd C:\
mkdir RAGTrace-Setup
cd RAGTrace-Setup
echo 현재 위치: %CD%
```

**예상 결과:**
```
현재 위치: C:\RAGTrace-Setup
```

### 2. Git 설치

#### 2-1. Git 설치 여부 확인
```cmd
git --version
```

**Git이 설치된 경우:** `git version 2.x.x` 메시지 → [3단계로 이동](#3-python-수동-설치)  
**Git이 없는 경우:** `'git'은(는) 내부 또는 외부 명령...` 오류 → 아래 계속

#### 2-2. Git 다운로드 및 설치
1. **웹브라우저**에서 https://git-scm.com/download/win 접속
2. **"64-bit Git for Windows Setup"** 클릭하여 다운로드
3. **다운로드된 파일** 실행 (보통 `Git-2.x.x-64-bit.exe`)
4. **설치 과정:**
   - "Select Components" → 모든 기본값 유지
   - "Choose the default editor" → 기본값 유지
   - "Adjusting your PATH environment" → **"Git from the command line and also from 3rd-party software"** 선택
   - 나머지 모든 옵션 → 기본값 유지

#### 2-3. Git 설치 확인
```cmd
# 새 CMD 창 열기 (PATH 갱신을 위해)
# Windows 키 + R → "cmd" → Ctrl + Shift + Enter

git --version
```

**예상 결과:**
```
git version 2.43.0.windows.1
```

### 3. Python 수동 설치

#### 3-1. Python 설치 여부 확인
```cmd
python --version
```

**Python이 있는 경우:**
```
Python 3.11.x
```
→ [4단계 UV 설치](#4-uv-설치)로 이동

**Python이 없는 경우:**
```
'python'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.
```
→ 아래 계속

#### 3-2. Python 다운로드
1. **웹브라우저**에서 https://www.python.org/downloads/release/python-3119/ 접속
2. 페이지 하단 **"Files"** 섹션에서 **"Windows installer (64-bit)"** 클릭
3. `python-3.11.9-amd64.exe` 다운로드

#### 3-3. Python 설치
1. **다운로드된 파일** 실행
2. **매우 중요:** 첫 화면에서 **"Add Python 3.11 to PATH"** 체크박스 ✅ 선택
3. **"Install Now"** 클릭
4. 설치 완료까지 대기 (약 2-3분)
5. **"Setup was successful"** 메시지 확인

#### 3-4. Python 설치 확인
```cmd
# 새 CMD 창 열기 (PATH 갱신을 위해)
python --version
pip --version
```

**예상 결과:**
```
Python 3.11.9
pip 23.x.x from ...
```

### 4. UV 설치

#### 4-1. pip 업그레이드
```cmd
python -m pip install --upgrade pip
```

**예상 결과:**
```
Successfully installed pip-23.x.x
```

#### 4-2. UV 설치
```cmd
pip install uv
```

**예상 결과:**
```
Successfully installed uv-x.x.x
```

#### 4-3. UV 설치 확인
```cmd
uv --version
```

**예상 결과:**
```
uv 0.x.x
```

### 5. RAGTrace 다운로드

#### 5-1. 소스코드 클론
```cmd
cd C:\RAGTrace-Setup
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace
```

#### 5-2. 다운로드 확인
```cmd
dir
```

**예상 결과:** `src`, `data`, `cli.py`, `README.md` 등의 파일/폴더가 보여야 함

### 6. 오프라인 패키지 수동 생성

#### 6-1. 작업 디렉토리 생성
```cmd
mkdir RAGTrace-Complete-Offline
mkdir RAGTrace-Complete-Offline\01_Dependencies
mkdir RAGTrace-Complete-Offline\02_Source
mkdir RAGTrace-Complete-Offline\03_Models
mkdir RAGTrace-Complete-Offline\04_Scripts
mkdir RAGTrace-Complete-Offline\05_Installers
```

#### 6-2. BGE-M3 모델 다운로드 (필수)
```cmd
cd RAGTrace-Complete-Offline\03_Models

# Python으로 BGE-M3 모델 다운로드
python -c "
print('BGE-M3 모델 다운로드 시작...')
from sentence_transformers import SentenceTransformer
import os

# 모델 다운로드 및 저장
model = SentenceTransformer('BAAI/bge-m3')
model.save('./bge-m3')
print('✅ BGE-M3 모델 다운로드 완료')
print('📁 저장 위치: ./bge-m3')

# 모델 파일 확인
model_files = []
for root, dirs, files in os.walk('./bge-m3'):
    for file in files:
        file_path = os.path.join(root, file)
        size = os.path.getsize(file_path)
        model_files.append((file_path, size))

total_size = sum(size for _, size in model_files)
print(f'💾 모델 총 크기: {total_size / (1024*1024):.1f}MB')
print(f'📄 모델 파일 개수: {len(model_files)}개')
"
```

**예상 출력:**
```
BGE-M3 모델 다운로드 시작...
✅ BGE-M3 모델 다운로드 완료
📁 저장 위치: ./bge-m3
💾 모델 총 크기: 2048.5MB
📄 모델 파일 개수: 15개
```

**⚠️ 중요사항:**
- 이 단계는 **약 2GB 다운로드**가 필요하므로 시간이 오래 걸립니다.
- BGE-M3 모델이 없으면 폐쇄망에서 임베딩 관련 메트릭 평가가 실패합니다.
- **Context Recall**, **Context Precision** 메트릭은 임베딩이 필요하므로 반드시 포함해야 합니다.

#### 6-2. Requirements 파일 생성
```cmd
# RAGTrace-Complete-Offline\01_Dependencies 폴더로 이동
cd RAGTrace-Complete-Offline\01_Dependencies

# requirements.txt 파일 생성 (메모장으로)
notepad requirements.txt
```

**메모장에 다음 내용 입력:**
```txt
dependency-injector
ragas
google-generativeai
langchain-core
python-dotenv
pydantic
pydantic-settings
pandas
numpy
openpyxl
xlrd
datasets
scipy
scikit-learn
streamlit
plotly
sentence-transformers
transformers
requests
psutil
chardet
pytest
black
torch           # CPU 전용 휠은 별도로 다운로드 가능
uv
# CSV/Excel 지원을 위한 추가 패키지들
charset-normalizer
python-dateutil
pytz
et-xmlfile      # openpyxl 의존성
defusedxml      # xlrd 의존성
```

**저장:** Ctrl + S, 파일명 확인 후 저장

#### 6-3. Python 패키지 다운로드
```cmd
# 현재 위치 확인
echo %CD%
# 결과: C:\RAGTrace-Setup\RAGTrace\RAGTrace-Complete-Offline\01_Dependencies

# 패키지 다운로드 (시간이 오래 걸림 - 약 10-15분)
pip download -r requirements.txt -d ./packages
```

**진행 과정:** 여러 `.whl` 파일들이 다운로드됨

#### 6-4. 소스코드 복사
```cmd
cd ..\..\
echo %CD%
# 결과: C:\RAGTrace-Setup\RAGTrace

# 소스코드 복사
xcopy src RAGTrace-Complete-Offline\02_Source\src\ /E /I /Y
xcopy data RAGTrace-Complete-Offline\02_Source\data\ /E /I /Y
copy cli.py RAGTrace-Complete-Offline\02_Source\
copy run_dashboard.py RAGTrace-Complete-Offline\02_Source\
copy hello.py RAGTrace-Complete-Offline\02_Source\
copy pyproject.toml RAGTrace-Complete-Offline\02_Source\
copy .env.example RAGTrace-Complete-Offline\02_Source\

# CSV/Excel 지원을 위한 추가 파일들 (중요!)
copy quick_eval.py RAGTrace-Complete-Offline\02_Source\ 2>nul || echo quick_eval.py not found - OK
copy justfile RAGTrace-Complete-Offline\02_Source\ 2>nul || echo justfile not found - OK
copy uv.toml RAGTrace-Complete-Offline\02_Source\ 2>nul || echo uv.toml not found - OK
copy .python-version RAGTrace-Complete-Offline\02_Source\ 2>nul || echo .python-version not found - OK

# 복사 완료 확인
echo 📁 소스코드 복사 완료, 파일 목록 확인:
dir RAGTrace-Complete-Offline\02_Source
```

**필수 확인사항:**
- `src\` 폴더: RAGTrace 메인 소스코드 (CSV/Excel 변환 로직 포함)
- `cli.py`: CSV/Excel 변환 기능 포함된 CLI 도구
- `data\` 폴더: 샘플 평가 데이터
- 기타 설정 파일들

**⚠️ CSV/Excel 지원 필수 요소:**
- `src\utils\paths.py`: 파일 형식 감지 및 변환 로직
- `src\utils\data_converter.py`: CSV/Excel → JSON 변환 엔진
- `openpyxl`, `xlrd`, `chardet` 패키지: Excel/CSV 파싱용

#### 6-5. Python 설치파일 복사
```cmd
# 다운로드한 Python 설치파일을 05_Installers로 복사
# (다운로드 폴더에서 찾아서 복사)
copy "%USERPROFILE%\Downloads\python-3.11.9-amd64.exe" RAGTrace-Complete-Offline\05_Installers\
```

#### 6-6. 설치 스크립트 생성

**00-install-all.bat 생성:**
```cmd
cd RAGTrace-Complete-Offline\04_Scripts
notepad 00-install-all.bat
```

**내용 입력:**
```batch
@echo off
echo [RAGTrace] 완전 설치 시작...

:: 1. Python 설치
echo 1/4: Python 설치 중...
cd ..\05_Installers
python-3.11.9-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

echo Python 설치 대기 중...
:waitloop
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    timeout /t 2 >nul
    goto waitloop
)

:: 2. PATH 확인
echo 2/4: PATH 확인 및 환경 준비...
where python
if %ERRORLEVEL% NEQ 0 (
    echo [경고] PATH가 반영되지 않았을 수 있습니다. CMD 창을 재시작해 주세요.
)

:: 3. 패키지 설치
echo 3/4: RAGTrace 패키지 설치 중...
cd ..\01_Dependencies
python -m pip install --upgrade pip
python -m pip install --no-index --find-links . -r requirements.txt || (
    echo [ERROR] 패키지 설치 실패!
    pause
    exit /b 1
)

:: 4. 설치 완료
echo 4/4: 설치 완료!
cd ..\02_Source
echo.
echo ✅ API 키를 .env 파일에 설정하세요.
echo ▶ 실행: python run_dashboard.py
pause
```

**05-run-dashboard.bat 생성:**
```cmd
notepad 05-run-dashboard.bat
```

**내용 입력:**
```batch
@echo off
cd ..\02_Source
echo RAGTrace 웹 대시보드 실행 중...
python run_dashboard.py
pause
```

#### 6-7. 최종 패키지 확인
```cmd
cd ..
dir /s
```

**확인할 구조:**
```
RAGTrace-Complete-Offline\
├── 01_Dependencies\    (requirements.txt + .whl 파일들)
├── 02_Source\         (RAGTrace 소스코드)
├── 03_Models\         (BGE-M3 모델 파일들 - 필수!)
│   └── bge-m3\        (약 2GB, 15개 파일)
├── 04_Scripts\        (설치/실행 스크립트들)
└── 05_Installers\     (python-3.11.9-amd64.exe)
```

**⚠️ 폐쇄망 배포 전 필수 확인:**
```cmd
# BGE-M3 모델 파일 존재 확인
dir RAGTrace-Complete-Offline\03_Models\bge-m3
```

**예상 결과:** 15개 이상의 파일이 보여야 함 (config.json, pytorch_model.bin, tokenizer.json 등)

---

## 🔒 폐쇄망 PC 설치

### 폐쇄망 사전 준비

1. **오프라인 패키지 복사**
   - 인터넷 PC에서 생성한 `RAGTrace-Complete-Offline` 폴더 전체를 USB나 네트워크를 통해 폐쇄망 PC로 복사
   - 권장 위치: `C:\RAGTrace-Complete-Offline\`

### 폐쇄망 Python 설치

#### 1. 관리자 권한 확인
```cmd
# 관리자 권한 CMD 열기
whoami /groups | find "Administrator"
```

#### 2. Python 설치
```cmd
cd C:\RAGTrace-Complete-Offline\05_Installers
python-3.11.9-amd64.exe
```

**수동 설치 과정:**
1. **"Add Python 3.11 to PATH"** 체크 ✅
2. **"Install Now"** 클릭
3. 설치 완료 대기

#### 3. 설치 확인
```cmd
# 새 CMD 창 열기
python --version
pip --version
```

#### 4. UV 오프라인 설치
```cmd
cd C:\RAGTrace-Complete-Offline\01_Dependencies
python -m pip install --no-index --find-links . uv
```

### 폐쇄망 가상환경 설정

#### 1. UV 기반 가상환경 생성 & 활성화
```cmd
cd C:\RAGTrace-Complete-Offline
where python
:: Python이 설치된 경로 복사
:: 예: C:\Users\<user>\AppData\Local\Programs\Python\Python311\python.exe
:: 위 경로를 지정해서 가상환경 생성
uv venv .venv --python "C:\Users\<user>\AppData\Local\Programs\Python\Python311\python.exe"
.venv\Scripts\activate
python --version   :: Python 3.11.9  ← 반드시 확인
```

### 폐쇄망 BGE-M3 모델 설정

#### 1. BGE-M3 모델 복사
```cmd
# BGE-M3 모델 디렉토리 생성
cd C:\RAGTrace-Complete-Offline\02_Source
mkdir models

# BGE-M3 모델 파일 복사
xcopy ..\03_Models\bge-m3 models\bge-m3\ /E /I /Y

# 모델 파일 확인
dir models\bge-m3
```

**예상 결과:** 15개 이상의 파일이 복사되어야 함

#### 2. 환경 변수 설정 (선택사항)
```cmd
# .env 파일에 BGE-M3 모델 경로 추가
echo BGE_M3_MODEL_PATH=./models/bge-m3 >> .env
```

### 폐쇄망 RAGTrace 설치

#### 1. 패키지 설치
```cmd
cd C:\RAGTrace-Complete-Offline\01_Dependencies
:: pip를 인터넷 없이 로컬 파일로 업그레이드
uv pip install --no-index --find-links .\packages pip
:: requirements.txt에 있는 패키지들을 로컬 파일로 설치
uv pip install --no-index --find-links .\packages -r requirements.txt
```

#### 2. API 키 설정
```cmd
cd ..\02_Source
copy .env.example .env
notepad .env
```

**.env 파일에 API 키 입력:**
```
GEMINI_API_KEY=your_gemini_api_key_here
CLOVA_STUDIO_API_KEY=your_hcx_key_here
```

### 폐쇄망 실행 확인

#### 1. 기본 테스트
```cmd
cd C:\RAGTrace-Complete-Offline\02_Source
python hello.py
```

**예상 결과:** 시스템 상태 정보 출력

#### 2. CLI 테스트
```cmd
python cli.py --help
```

**예상 결과:** 도움말 메시지 출력

#### 3. 웹 대시보드 실행
```cmd
python run_dashboard.py
```

**예상 결과:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

4. **웹브라우저**에서 http://localhost:8501 접속

---

## 🚨 문제 해결

### Python PATH 문제

**문제:** `'python'은(는) 내부 또는 외부 명령...`

**해결:**
```cmd
# Python 설치 위치 확인
dir "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311"

# PATH 수동 추가
setx PATH "%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\Scripts"

# CMD 재시작 후 확인
python --version
```

### 관리자 권한 문제

**문제:** `액세스가 거부되었습니다`

**해결:**
1. **Windows 키 + X**
2. **"Windows PowerShell(관리자)"** 또는 **"명령 프롬프트(관리자)"** 선택
3. **"예"** 클릭하여 권한 승인

### 패키지 설치 실패

**문제:** `pip install` 실패

**해결:**
```cmd
# pip 캐시 정리
python -m pip cache purge

# 개별 패키지 설치 시도
python -m pip install --no-index --find-links . streamlit
python -m pip install --no-index --find-links . pandas

# 모든 .whl 파일 강제 설치
for %f in (*.whl) do python -m pip install "%f" --force-reinstall
```

### 웹 대시보드 접속 불가

**문제:** 브라우저에서 접속 안됨

**해결:**
```cmd
# 방화벽 규칙 추가
netsh advfirewall firewall add rule name="RAGTrace" dir=in action=allow protocol=TCP localport=8501

# 다른 포트로 실행
python -m streamlit run src/presentation/web/main.py --server.port 8502
```

### BGE-M3 모델 문제

**문제:** 평가 중 임베딩 오류 발생

**원인:** BGE-M3 모델 파일이 누락되거나 손상됨

**해결:**
```cmd
# 모델 파일 존재 확인
dir C:\RAGTrace-Complete-Offline\02_Source\models\bge-m3

# 모델 파일이 없는 경우 다시 복사
cd C:\RAGTrace-Complete-Offline\02_Source
xcopy ..\03_Models\bge-m3 models\bge-m3\ /E /I /Y

# BGE-M3 모델 테스트
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('./models/bge-m3')
print('✅ BGE-M3 모델 로딩 성공')
"
```

**문제:** 임베딩 관련 메트릭 실패 (Context Recall, Context Precision)

**원인:** BGE-M3 모델이 없어서 임베딩 생성 실패

**해결:** 위의 BGE-M3 모델 설치 단계 다시 실행

---

## 📝 설치 체크리스트

### 인터넷 PC (패키지 생성)
- [ ] 관리자 권한 확인
- [ ] Git 설치 및 확인
- [ ] Python 3.11 설치 (PATH 포함)
- [ ] UV 설치 및 확인
- [ ] RAGTrace 소스코드 다운로드
- [ ] 패키지 디렉토리 구조 생성
- [ ] **BGE-M3 모델 다운로드 (약 2GB, 필수!)**
- [ ] requirements.txt 생성
- [ ] Python 패키지 다운로드 (200+ 개)
- [ ] 소스코드 복사
- [ ] 설치파일 복사 (Python)
- [ ] 설치/실행 스크립트 생성
- [ ] 최종 패키지 구조 확인 (BGE-M3 모델 포함)

### 폐쇄망 PC (설치 및 실행)
- [ ] 오프라인 패키지 복사
- [ ] 관리자 권한 확인
- [ ] Python 설치 (PATH 포함)
- [ ] Python 설치 확인
- [ ] **BGE-M3 모델 복사 및 확인 (models/bge-m3/)**
- [ ] RAGTrace 패키지 설치
- [ ] API 키 설정 (.env 파일)
- [ ] 기본 테스트 (hello.py)
- [ ] CLI 테스트
- [ ] **BGE-M3 모델 로딩 테스트**
- [ ] 웹 대시보드 실행
- [ ] 브라우저 접속 확인
- [ ] **전체 RAGAS 메트릭 평가 테스트 (임베딩 포함)**

---

## 🎯 다음 단계

설치가 완료되면:

1. **API 키 설정** - Gemini API 키는 필수
2. **샘플 데이터 테스트** - evaluation_data로 첫 평가 실행
3. **실제 데이터 준비** - Excel/CSV 데이터 가져오기
4. **결과 분석** - 평가 보고서 및 시각화 활용

이 가이드를 통해 어떤 환경에서도 RAGTrace를 성공적으로 설치할 수 있습니다! 🚀