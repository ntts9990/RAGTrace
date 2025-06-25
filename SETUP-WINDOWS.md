# Windows 설치 가이드

RAGTrace를 Windows에서 사용하기 위한 완전한 설치 가이드입니다.

## 📋 두 가지 설치 시나리오

### 🌐 시나리오 1: 인터넷 연결된 PC (오프라인 패키지 생성용)

폐쇄망에서 사용할 완전한 오프라인 패키지를 생성하는 PC입니다.

#### 1단계: 저장소 클론
```bash
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace
```

#### 2단계: 오프라인 패키지 생성 (관리자 권한 PowerShell)
```powershell
# 권장: 완전 자동 설치 (Python + UV 자동 설치)
.\create-complete-offline.ps1 -Verbose

# 또는 PowerShell 호환성 문제 시
.\create-offline-simple.bat
```

**자동으로 수행되는 작업:**
- ✅ Python 3.11.9 자동 다운로드 및 설치
- ✅ UV 패키지 매니저 자동 설치
- ✅ 모든 Python 패키지 다운로드 (200+ 개)
- ✅ RAGTrace 소스코드 패키징
- ✅ BGE-M3 모델 다운로드 (선택사항)
- ✅ 완전한 오프라인 설치 패키지 생성

#### 3단계: 생성된 패키지 확인
```
📁 RAGTrace-Complete-Offline/
├── 01_Dependencies/     # Python 패키지들
├── 02_Source/          # RAGTrace 소스코드
├── 03_Models/          # BGE-M3 모델 (선택)
├── 04_Scripts/         # 설치 스크립트들
├── 05_Installers/      # Python, VC++ 설치파일
└── README-설치가이드.txt
```

---

### 🔒 시나리오 2: 폐쇄망 PC (실제 사용 환경)

인터넷이 차단된 환경에서 RAGTrace를 실행하는 PC입니다.

#### 1단계: 오프라인 패키지 복사
인터넷 PC에서 생성한 `RAGTrace-Complete-Offline` 폴더를 폐쇄망 PC로 복사합니다.

#### 2단계: 자동 설치 실행 (관리자 권한)
```cmd
cd RAGTrace-Complete-Offline\04_Scripts
00-install-all.bat
```

**자동 설치 순서:**
1. Python 3.11.9 설치
2. Visual C++ 재배포 패키지 설치
3. RAGTrace 패키지들 설치
4. 환경 설정 완료

#### 3단계: RAGTrace 실행
```cmd
# 웹 대시보드 실행
05-run-dashboard.bat

# 또는 CLI 사용
python cli.py --help
```

---

## 🛠️ 수동 설치 방법 (고급 사용자)

자동 설치가 실패하거나 커스터마이징이 필요한 경우:

### 인터넷 연결된 PC에서

1. **Python 3.11+ 설치**
   ```
   https://www.python.org/downloads/release/python-3119/
   ✅ "Add Python to PATH" 체크
   ✅ "Install for all users" 권장
   ```

2. **UV 설치**
   ```powershell
   pip install uv
   ```

3. **RAGTrace 클론 및 패키지 생성**
   ```powershell
   git clone https://github.com/ntts9990/RAGTrace.git
   cd RAGTrace
   .\create-complete-offline.ps1 -Verbose
   ```

### 폐쇄망 PC에서

1. **오프라인 패키지의 Python 설치**
   ```cmd
   05_Installers\python-3.11.9-amd64.exe
   ```

2. **Visual C++ 재배포 패키지 설치**
   ```cmd
   05_Installers\VC_redist.x64.exe
   ```

3. **RAGTrace 패키지 설치**
   ```cmd
   cd 01_Dependencies
   pip install --no-index --find-links . -r requirements.txt
   ```

---

## 🚨 문제 해결

### PowerShell 호환성 문제
```
오류: "from 키워드는 이 언어 버전에서 지원되지 않습니다"
```

**해결 방법:**
1. PowerShell 7+ 설치: https://github.com/PowerShell/PowerShell/releases
2. 또는 배치 스크립트 사용: `create-offline-simple.bat`

### Python 설치 문제
```
오류: Python이 PATH에 없습니다
```

**해결 방법:**
1. Python 재설치 시 "Add Python to PATH" 체크
2. 또는 환경변수 수동 설정:
   ```
   C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311
   C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\Scripts
   ```

### 관리자 권한 문제
```
오류: 관리자 권한이 필요합니다
```

**해결 방법:**
1. PowerShell을 우클릭 → "관리자 권한으로 실행"
2. 또는 CMD를 관리자 권한으로 실행

### 방화벽/보안 문제
```
오류: 실행 정책에 의해 차단됨
```

**해결 방법:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📞 지원 및 문의

- **GitHub Issues**: https://github.com/ntts9990/RAGTrace/issues
- **문서**: `docs/` 폴더 참조
- **예제**: `data/` 폴더의 샘플 데이터

---

## 🎯 요약

### 🌐 인터넷 연결된 PC
```powershell
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace
.\create-complete-offline.ps1 -Verbose
```

### 🔒 폐쇄망 PC
```cmd
# 오프라인 패키지 복사 후
cd RAGTrace-Complete-Offline\04_Scripts
00-install-all.bat

# 실행
05-run-dashboard.bat
```

모든 과정이 자동화되어 있어 최소한의 수동 작업으로 RAGTrace를 사용할 수 있습니다! 🚀