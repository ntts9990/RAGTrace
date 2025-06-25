# RAGTrace Windows PC 완전 오프라인 패키지 생성 가이드

## 🎯 목표
폐쇄망 환경에서 사용할 RAGTrace 완전 오프라인 패키지를 Windows PC에서 생성

## 📋 Windows PC에서 수행할 단계

### 1. 사전 준비
```powershell
# 1.1 Git 설치 확인
git --version

# 1.2 Python 3.11 설치 확인  
python --version

# 1.3 UV 설치 (PowerShell 관리자 권한)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 프로젝트 클론
```bash
# 2.1 저장소 클론
git clone https://github.com/ntts9990/RAGTrace.git
cd RAGTrace

# 2.2 브랜치 변경
git checkout refactor/architecture-improvement

# 2.3 최신 상태 확인
git pull origin refactor/architecture-improvement
```

### 3. 개발 환경 설정
```bash
# 3.1 가상환경 생성 및 의존성 설치
uv sync --all-extras

# 3.2 환경 확인
uv pip list | head -20
```

### 4. 완전 오프라인 패키지 생성
```powershell
# 4.1 PowerShell 스크립트 실행
.\create-windows-offline.ps1

# 또는 bash 스크립트 실행
bash create-complete-offline.sh
```

## 📄 생성할 파일들

### create-windows-offline.ps1 (PowerShell 버전)
- Windows 네이티브 스크립트
- 플랫폼별 wheel 다운로드 최적화
- 완전 오프라인 패키지 생성

### create-complete-offline.sh (Bash 버전) 
- 크로스 플랫폼 호환
- 상세한 로깅
- 자동 검증 기능

## 🎯 최종 결과물
```
RAGTrace-Windows-Offline.zip
├── 01_Prerequisites/
│   ├── python-3.11.9-amd64.exe (사용자가 추가)
│   ├── vc_redist.x64.exe (사용자가 추가)  
│   └── README.txt
├── 02_Dependencies/
│   ├── wheels/ (200+ .whl 파일)
│   ├── requirements.txt
│   └── checksums.txt
├── 03_Source/
│   └── (전체 RAGTrace 소스)
├── 04_Scripts/
│   ├── install.bat
│   ├── run-web.bat
│   ├── run-cli.bat
│   └── verify.py
└── README-설치가이드.txt
```

## ⚡ 예상 결과
- **패키지 크기**: 약 2-3GB
- **wheel 파일**: 200+ 개
- **설치 시간**: 10-20분 (폐쇄망)
- **실행**: 완전 오프라인 가능