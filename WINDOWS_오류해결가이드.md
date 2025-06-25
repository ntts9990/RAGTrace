# RAGTrace Windows 오프라인 패키지 오류 해결 가이드

## 🎯 개요

Windows PC에서 RAGTrace 오프라인 패키지 생성 및 설치 시 발생할 수 있는 오류들과 해결 방법을 정리한 가이드입니다.

## 📋 제공되는 안전한 스크립트들

### 1. 완전 오프라인 버전 (추천)
```powershell
.\create-windows-offline-safe.ps1
```
- **특징**: 모든 wheel 파일 사전 다운로드, 완전 오프라인 설치
- **용량**: 2-3GB
- **장점**: 폐쇄망에서 100% 오프라인 설치 가능
- **단점**: 초기 생성 시간이 오래 걸림

### 2. 간단 설치 버전
```bash
bash create-simple-offline.sh
```
- **특징**: 최소 패키지, 설치 시 인터넷 연결 필요
- **용량**: 10-50MB
- **장점**: 빠른 생성, 간단한 설치
- **단점**: 폐쇄망에서는 사용 불가

## 🚨 자주 발생하는 오류들

### 1. PowerShell 실행 정책 오류

**오류 메시지:**
```
이 시스템에서 스크립트를 실행할 수 없으므로 파일을 로드할 수 없습니다
```

**해결 방법:**
```powershell
# 관리자 권한으로 PowerShell 실행 후
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
# 또는
Set-ExecutionPolicy Bypass -Scope Process -Force
```

### 2. Python PATH 오류

**오류 메시지:**
```
'python'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.
```

**해결 방법:**
1. **Python 재설치** (권장)
   - https://www.python.org/downloads/release/python-3119/
   - 설치 시 **"Add Python to PATH"** 체크 필수
   
2. **수동 PATH 설정**
   ```cmd
   # 시스템 속성 → 고급 → 환경 변수
   # PATH에 다음 경로 추가:
   C:\Users\[사용자명]\AppData\Local\Programs\Python\Python311\
   C:\Users\[사용자명]\AppData\Local\Programs\Python\Python311\Scripts\
   ```

### 3. pip 다운로드 오류

**오류 메시지:**
```
WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None))
ERROR: Could not find a version that satisfies the requirement
```

**해결 방법:**
1. **네트워크 확인**
   ```cmd
   ping pypi.org
   ```

2. **pip 업그레이드**
   ```cmd
   python -m pip install --upgrade pip
   ```

3. **프록시 설정 (회사망)**
   ```cmd
   pip install --proxy http://proxy.company.com:8080 --trusted-host pypi.org --trusted-host pypi.python.org
   ```

4. **타임아웃 증가**
   ```cmd
   pip install --timeout 1000 --retries 10
   ```

### 4. 권한 관련 오류

**오류 메시지:**
```
Access is denied
관리자 권한이 필요합니다
```

**해결 방법:**
1. **PowerShell 관리자 실행**
   - 시작 메뉴 → PowerShell → 우클릭 → "관리자 권한으로 실행"

2. **UAC 설정 확인**
   - 제어판 → 사용자 계정 → 사용자 계정 컨트롤 설정 변경

### 5. 가상환경 생성 오류

**오류 메시지:**
```
Error: Unable to create virtual environment
```

**해결 방법:**
1. **venv 모듈 확인**
   ```cmd
   python -m venv --help
   ```

2. **수동 가상환경 생성**
   ```cmd
   python -m pip install virtualenv
   virtualenv .venv
   ```

3. **경로 문제 해결**
   ```cmd
   # 짧은 경로 사용
   mkdir C:\RAG
   cd C:\RAG
   ```

### 6. 패키지 설치 실패

**오류 메시지:**
```
ERROR: Failed building wheel for [package]
Microsoft Visual C++ 14.0 is required
```

**해결 방법:**
1. **Visual C++ 재배포 가능 패키지 설치**
   - https://aka.ms/vs/17/release/vc_redist.x64.exe

2. **Visual Studio Build Tools 설치**
   - https://visualstudio.microsoft.com/visual-cpp-build-tools/

3. **사전 컴파일된 wheel 사용**
   ```cmd
   pip install --only-binary=all package_name
   ```

### 7. 메모리 부족 오류

**오류 메시지:**
```
MemoryError
Killed
```

**해결 방법:**
1. **가상 메모리 증가**
   - 시스템 속성 → 고급 → 성능 설정 → 고급 → 가상 메모리

2. **배치 크기 줄이기**
   ```cmd
   pip install --no-cache-dir package_name
   ```

## 🔧 단계별 트러블슈팅

### 단계 1: 환경 검증
```cmd
# Python 버전 확인
python --version

# pip 버전 확인  
pip --version

# 관리자 권한 확인
net session

# 인터넷 연결 확인
ping google.com
```

### 단계 2: 스크립트 실행 전 준비
```powershell
# PowerShell 실행 정책 설정
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 작업 디렉토리 확인
Get-Location
Test-Path ".\cli.py"
Test-Path ".\src"
```

### 단계 3: 오류 발생 시 진단
```cmd
# 자세한 오류 출력
pip install package_name --verbose

# 로그 파일 확인
type pip.log

# 시스템 정보 확인
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
```

## 🛠️ 권장 해결 순서

### 1단계: 기본 환경 점검
- [ ] Python 3.11 설치 확인
- [ ] PATH 환경변수 설정 확인
- [ ] 관리자 권한 확인
- [ ] 인터넷 연결 확인

### 2단계: 스크립트 선택
- **폐쇄망 환경**: `create-windows-offline-safe.ps1` 사용
- **인터넷 연결 가능**: `create-simple-offline.sh` 사용

### 3단계: 오류 발생 시
1. 오류 메시지 전체 복사
2. 위 가이드에서 해당 오류 검색
3. 제시된 해결 방법 순서대로 시도
4. 여전히 실패 시 로그 파일 확인

### 4단계: 대안 방법
- 다른 Windows PC에서 시도
- 가상머신 환경에서 테스트
- Docker 환경 활용

## 📞 추가 지원

### 로그 수집 방법
```cmd
# 상세 로그와 함께 실행
create-windows-offline-safe.ps1 -Verbose > install_log.txt 2>&1
```

### 시스템 정보 수집
```cmd
# 시스템 정보 저장
systeminfo > system_info.txt
python --version > python_info.txt
pip list > pip_packages.txt
```

### 환경 변수 확인
```cmd
echo %PATH% > path_info.txt
echo %PYTHONPATH% > python_path.txt
```

## 🎯 성공 확인 방법

### 패키지 생성 확인
```cmd
# 생성된 파일 확인
dir RAGTrace-Windows-Offline-Safe.zip
dir RAGTrace-Simple-Offline.tar.gz
```

### 설치 후 검증
```cmd
cd 03_Source
.venv\Scripts\activate
python ..\04_Scripts\verify.py
```

### 웹 UI 실행 테스트
```cmd
cd 04_Scripts
run-web.bat
# 브라우저에서 http://localhost:8501 접속 확인
```

## 💡 예방 조치

### 1. 사전 환경 준비
- Windows 10 64비트 이상
- 최소 10GB 여유 공간
- 안정적인 인터넷 연결
- 관리자 계정 사용

### 2. 권장 설정
- Windows Defender 예외 설정
- 바이러스 백신 임시 비활성화
- 자동 업데이트 일시 중지

### 3. 백업 방안
- 중요 데이터 백업
- 시스템 복원 지점 생성
- 가상머신 환경 활용

---

이 가이드로 해결되지 않는 문제가 있다면, 오류 메시지와 시스템 정보를 함께 제공해 주세요.