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
- **BGE-M3 모델 자동 포함** (약 2GB)

### create-complete-offline.sh (Bash 버전) 
- 크로스 플랫폼 호환
- 상세한 로깅
- 자동 검증 기능
- **BGE-M3 모델 자동 다운로드 및 포함**

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
├── 05_Models/
│   └── bge-m3/ (BGE-M3 로컬 임베딩 모델, 약 2GB)
│       ├── config.json
│       ├── pytorch_model.bin
│       ├── tokenizer.json
│       └── (기타 모델 파일들)
└── README-설치가이드.txt
```

## ⚡ 예상 결과
- **패키지 크기**: 약 4-5GB (**BGE-M3 모델 포함**)
- **wheel 파일**: 200+ 개
- **BGE-M3 모델**: 약 2GB (완전 오프라인 임베딩)
- **설치 시간**: 15-25분 (폐쇄망)
- **실행**: 완전 오프라인 가능 (인터넷 연결 불필요)

## 🤖 BGE-M3 로컬 임베딩 지원

### 📁 모델 파일 구조
```
05_Models/bge-m3/
├── config.json              # 모델 설정
├── pytorch_model.bin        # 모델 가중치
├── tokenizer.json          # 토크나이저
├── tokenizer_config.json   # 토크나이저 설정
├── special_tokens_map.json # 특수 토큰
└── vocab.txt              # 어휘 사전
```

### ⚙️ 폐쇄망 환경 설정
폐쇄망에서 설치 시 BGE-M3 모델이 자동으로 `models/bge-m3/` 경로에 복사됩니다:

```bash
# 설치 후 .env 파일 자동 구성
BGE_M3_MODEL_PATH="./models/bge-m3"
DEFAULT_EMBEDDING="bge_m3"
```

### 🔧 디바이스 자동 최적화
- **CUDA**: GPU 가속 임베딩 (가장 빠름)
- **MPS**: Apple Silicon 최적화
- **CPU**: 멀티코어 처리 (폐쇄망 환경에서도 안정적)

### 📊 성능 벤치마크
- **CUDA**: ~60 docs/sec
- **MPS**: ~15 docs/sec  
- **CPU**: ~40 docs/sec
- **메모리**: 약 2GB 사용