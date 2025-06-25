# RAGTrace Windows 완전 설치 가이드

## 🎯 개요

Windows 환경에서 RAGTrace를 설치하고 실행하기 위한 완전한 가이드입니다. 
일반 설치부터 폐쇄망 환경까지 모든 시나리오를 지원합니다.

## 🚀 빠른 시작 (권장)

### 일반 환경 (인터넷 연결 가능)

```bash
# 1. 의존성 설치
uv sync --all-extras

# 2. API 키 설정 (.env 파일)
copy .env.example .env
# .env 파일을 편집하여 API 키 입력

# 3. 즉시 평가 실행
uv run python cli.py quick-eval evaluation_data
```

## 📦 오프라인 설치 옵션

### 1. 🛡️ 완전 오프라인 패키지 (엔터프라이즈)

```powershell
# 패키지 생성 (인터넷 연결된 PC에서)
python scripts/offline-packaging/create-enterprise-offline.py --project-root . --output-dir ./enterprise-package

# 폐쇄망으로 패키지 이동 후 설치
# install.bat 실행
```

**특징:**
- ✅ **완전 폐쇄망 지원**: 인터넷 연결 없이 완전 설치
- ✅ **SHA-256 무결성 검증**: 모든 패키지 암호화 검증  
- ✅ **자동 복구 시스템**: 설치 실패 시 자동 롤백
- ✅ **종합 진단 도구**: 시스템 상태 자동 분석

### 2. 🔧 Windows 안전 패키지

```powershell
# 안전한 패키지 생성
.\\scripts\\offline-packaging\\create-windows-offline-safe.ps1

# 결과물: RAGTrace-Windows-Offline-Safe.zip
```

**특징:**
- ✅ **모든 오류 상황 사전 검사**
- ✅ **단계별 상세 피드백**
- ✅ **안전한 패키지 버전 고정**
- ✅ **강화된 설치 스크립트**

### 3. ⚡ 간단 설치 패키지

```bash
# 간단 패키지 생성
bash scripts/offline-packaging/create-simple-offline.sh
```

**특징:**
- ✅ **빠른 생성과 설치**
- ✅ **최소 용량** (10-50MB)
- ⚠️ **설치 시 인터넷 연결 필요**

## 🚨 문제 해결

### 자주 발생하는 오류들

#### 1. PowerShell 실행 정책 오류

**증상:**
```
스크립트를 로드할 수 없습니다... 실행 정책에서 허용되지 않음
```

**해결:**
```powershell
# 관리자 권한으로 PowerShell 실행 후
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 또는 일회성 실행
powershell -ExecutionPolicy Bypass -File script.ps1
```

#### 2. Python 설치 문제

**증상:**
```
'python'은(는) 내부 또는 외부 명령... 인식할 수 없습니다
```

**해결:**
1. Python 3.11 다운로드: https://www.python.org/downloads/release/python-3119/
2. 설치 시 **"Add Python to PATH" 체크 필수**
3. 명령 프롬프트 재시작

#### 3. 관리자 권한 문제

**증상:**
```
액세스가 거부되었습니다
```

**해결:**
```cmd
# PowerShell을 관리자 권한으로 실행
# 시작 메뉴 → PowerShell → 우클릭 → "관리자 권한으로 실행"

# 권한 확인
net session
```

#### 4. 패키지 다운로드 실패

**증상:**
```
pip install 시 timeout 또는 network error
```

**해결:**
```bash
# 타임아웃 증가
pip install --timeout 1000 --retries 10 package_name

# 프록시 환경인 경우
pip install --proxy http://proxy.company.com:8080 package_name

# 캐시 정리
pip cache purge
```

#### 5. UV 설치 문제

**증상:**
```
'uv'은(는) 내부 또는 외부 명령이 아닙니다
```

**해결:**
```powershell
# UV 설치 (Windows PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 설치 확인
uv --version
```

#### 6. 메모리 부족 문제

**증상:**
```
MemoryError 또는 시스템이 느려짐
```

**해결:**
```bash
# BGE-M3 GPU 메모리 최적화
set BGE_M3_DEVICE=cpu

# 배치 크기 조정  
uv run python cli.py evaluate data.json --batch-size 4
```

## 🔍 시스템 진단

### 자동 진단 도구

```bash
# 종합 시스템 진단
python enterprise-validator.py

# 진단 보고서 생성
python enterprise-validator.py --output diagnostic_report.json

# 간략한 결과만 출력
python enterprise-validator.py --quiet
```

### 수동 확인 사항

```powershell
# 1. Python 버전 확인
python --version
# 출력: Python 3.11.x

# 2. pip 확인
pip --version

# 3. UV 확인 
uv --version

# 4. 시스템 정보
systeminfo | findstr "Total Physical Memory"

# 5. 디스크 공간 확인
dir C:\ /-c
```

## 💡 권장 설치 순서

### 폐쇄망 환경

1. **인터넷 연결된 PC에서 패키지 생성**
   ```bash
   python scripts/offline-packaging/create-enterprise-offline.py
   ```

2. **시스템 검증 및 진단** 
   ```bash
   python enterprise-validator.py --output system_report.json
   ```

3. **폐쇄망으로 패키지 이동**

4. **설치 실행**
   ```bash
   # Windows: install.bat 실행
   # Linux/macOS: bash install.sh
   ```

### 일반 환경

1. **Python 3.11 설치** (https://www.python.org/downloads/)

2. **UV 설치**
   ```powershell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **RAGTrace 설치**
   ```bash
   uv sync --all-extras
   ```

4. **환경 설정**
   ```bash
   copy .env.example .env
   # .env 파일에 API 키 입력
   ```

5. **테스트 실행**
   ```bash
   uv run python cli.py quick-eval evaluation_data
   ```

## 📞 추가 지원

- **설치 문제**: 진단 도구 실행 (`python enterprise-validator.py`)
- **성능 문제**: 메모리 및 GPU 설정 확인
- **권한 문제**: 관리자 권한으로 PowerShell 실행

## 🔗 관련 문서

- [엔터프라이즈 패키지 시스템](../../ENTERPRISE_패키지_시스템.md)
- [UV 설정 가이드](../../UV_SETUP.md)
- [Docker 배포 가이드](Docker_Deployment_Guide.md)