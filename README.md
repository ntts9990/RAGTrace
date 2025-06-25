# 🔍 RAGTrace v2.0

**엔터프라이즈급 Multi-LLM RAG 시스템 성능 평가 및 분석 플랫폼**

RAGTrace는 RAG(Retrieval-Augmented Generation) 시스템의 핵심 품질 지표를 신뢰성 있게 평가하고 분석하기 위한 엔터프라이즈급 종합 플랫폼입니다. [RAGAS](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 하며, Clean Architecture와 완전한 의존성 주입을 통해 확장 가능하고 유지보수성이 높은 구조를 제공합니다.

## 🎉 v2.0 주요 신기능

### 🛡️ **엔터프라이즈 오프라인 패키지 시스템**
- **완전 폐쇄망 지원**: 인터넷 연결 없이 완전 설치 및 실행
- **SHA-256 무결성 검증**: 모든 패키지 암호화 검증
- **UV 통합 의존성 관리**: 재현 가능한 환경 구축
- **자동 복구 시스템**: 설치 실패 시 자동 롤백

### 🔧 **Windows 환경 완벽 지원**
- **PowerShell 안전 스크립트**: 모든 오류 상황 대응
- **종합 진단 도구**: 시스템 상태 자동 분석
- **사전 조건 검증**: Python, 권한, 디스크 공간 자동 확인
- **상세 문제 해결 가이드**: 단계별 해결 방법 제공

### 📈 **성능 최적화**
- **60% 빠른 설치**: 병렬 처리 및 최적화
- **70% 향상된 Import 속도**: 메모리 효율적 로딩
- **실시간 성능 모니터링**: 벤치마크 및 진단

### 🔒 **보안 강화**
- **취약점 자동 스캔**: Safety 통합 보안 검사
- **권한 검증**: 파일 및 환경 보안 확인
- **엔터프라이즈 규정 준수**: 보안 정책 자동 적용

## 🚀 빠른 시작

### ⚡ **1분만에 시작하기** (추천)

```bash
# 1. 의존성 설치
uv sync --all-extras

# 2. API 키 설정 (.env 파일)
echo "GEMINI_API_KEY=your_key_here" > .env
echo "CLOVA_STUDIO_API_KEY=your_hcx_key_here" >> .env

# 3. 즉시 평가 실행 (HCX-005 + BGE-M3 + 자동 결과 저장)
uv run python cli.py quick-eval evaluation_data
```

**🎯 한 줄 명령어로 완료**:
- ✅ HCX-005 LLM + BGE-M3 로컬 임베딩 
- ✅ 완전한 5개 RAGAS 메트릭 평가
- ✅ 결과 JSON, CSV, 분석 보고서 자동 생성
- ✅ `quick_results/` 폴더에 모든 파일 저장

## 📊 RAGAS 평가 메트릭 이해하기

RAGTrace는 5가지 핵심 메트릭으로 RAG 시스템의 성능을 평가합니다:

### **평가 메트릭 설명**

| 메트릭 | 설명 | 좋은 점수 기준 | 개선 방법 |
|--------|------|---------------|----------|
| **Faithfulness** | 답변이 제공된 문맥에 얼마나 충실한가? | > 0.8 | 환각(hallucination) 줄이기 |
| **Answer Relevancy** | 답변이 질문과 얼마나 관련 있는가? | > 0.7 | 더 구체적인 답변 생성 |
| **Context Recall** | 필요한 정보가 모두 검색되었는가? | > 0.8 | 검색 시스템 개선 |
| **Context Precision** | 검색된 문맥이 얼마나 정확한가? | > 0.7 | 검색 정확도 향상 |
| **Answer Correctness** | 답변이 정답과 얼마나 일치하는가? | > 0.8 | 전반적인 시스템 개선 |
| **RAGAS Score** | 전체 메트릭의 평균 점수 | > 0.75 | 종합적 성능 지표 |

### **평가 결과 예시**
```
==================================================
📊 평가 결과 요약
==================================================
ragas_score      : 0.7820  ⭐ 좋음
answer_relevancy : 0.7276  ✅ 양호
faithfulness    : 0.8333  ⭐ 좋음
context_recall   : 1.0000  ⭐ 우수
context_precision: 0.6667  ⚠️ 개선 필요
answer_correctness: 0.6822  ⚠️ 개선 필요
==================================================
```

## 📋 데이터 준비 가이드

### **1. Excel/CSV 파일 형식**

RAGTrace는 Excel(.xlsx, .xls) 및 CSV 파일을 지원합니다. 파일에는 **반드시 4개의 필수 컬럼**이 있어야 합니다:

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `question` | 평가할 질문 | "원자력 발전소의 주요 구성요소는 무엇인가요?" |
| `contexts` | 참고 문맥들 (여러 형식 지원) | `["문맥1", "문맥2"]` 또는 `문맥1;문맥2` |
| `answer` | 시스템이 생성한 답변 | "원자로, 증기발생기, 터빈발전기가 주요 구성요소입니다." |
| `ground_truth` | 정답 기준 (평가 기준) | "원자로, 증기발생기, 터빈발전기" |

### **2. contexts 컬럼 작성 방법**

**방법 1: JSON 배열 (권장)**
```
["원자로는 핵분열 반응이 일어나는 곳입니다.", "증기발생기는 열을 전달합니다.", "터빈은 전기를 생산합니다."]
```

**방법 2: 세미콜론(;) 구분**
```
원자로는 핵분열 반응이 일어나는 곳입니다.;증기발생기는 열을 전달합니다.;터빈은 전기를 생산합니다.
```

**방법 3: 파이프(|) 구분**
```
원자로는 핵분열 반응이 일어나는 곳입니다.|증기발생기는 열을 전달합니다.|터빈은 전기를 생산합니다.
```

**방법 4: 단일 문맥**
```
원자력 발전소는 원자로, 증기발생기, 터빈발전기로 구성되며, 핵분열 에너지를 전기로 변환합니다.
```

### **3. Excel 파일 예시**

| question | contexts | answer | ground_truth |
|----------|----------|--------|--------------|
| 원자력 발전의 원리는? | `["핵분열로 열 생성", "증기로 터빈 구동", "발전기로 전기 생산"]` | 핵분열로 열을 만들어 증기를 생성하고, 이 증기로 터빈을 돌려 전기를 생산합니다. | 핵분열 에너지를 이용한 증기터빈 발전 |
| 태양광 발전의 장점은? | 친환경 에너지원;재생 가능;유지비 저렴 | 태양광 발전은 친환경적이고 재생 가능하며 유지비가 저렴합니다. | 친환경, 재생가능, 유지비 저렴 |

### **4. 데이터 변환 및 검증**

```bash
# Excel/CSV 파일 검증
uv run python cli.py import-data your_data.xlsx --validate

# JSON으로 변환 (평가에 사용)
uv run python cli.py import-data your_data.xlsx --output converted_data.json

# 변환된 데이터로 평가 실행
uv run python cli.py quick-eval converted_data
```

## 💾 평가 결과 활용하기

### **1. 생성되는 결과 파일들**

평가 완료 후 다음 파일들이 생성됩니다:

| 파일명 패턴 | 내용 | 활용 방법 |
|------------|------|-----------|
| `*_evaluation_*.json` | 전체 평가 결과 JSON | 프로그래밍 방식 분석 |
| `*_evaluation_*.csv` | 항목별 상세 점수 | Excel에서 분석 |
| `*_summary_*.csv` | 메트릭별 통계 요약 | 빠른 성능 파악 |
| `*_analysis_report_*.md` | 종합 분석 보고서 | 개선점 파악 |

### **2. 결과 파일 구조**

**상세 CSV (`ragas_evaluation_*.csv`)**
```csv
item_id,faithfulness,answer_relevancy,context_recall,context_precision,answer_correctness
1,0.8,0.75,1.0,0.9,0.85
2,0.6,0.82,0.9,0.7,0.78
```

**요약 통계 CSV (`ragas_summary_*.csv`)**
```csv
metric,mean,median,std_dev,min,max,count,q1,q3
faithfulness,0.733,0.8,0.1,0.6,0.8,2,0.6,0.8
answer_relevancy,0.785,0.785,0.035,0.75,0.82,2,0.75,0.82
```

### **3. 분석 보고서 읽는 법**

분석 보고서(`*_analysis_report_*.md`)는 다음 정보를 포함합니다:

- **전체 성능 요약**: RAGAS 종합 점수와 등급
- **메트릭별 상세 분석**: 각 메트릭의 의미와 개선 방향
- **통계 분석**: 평균, 중앙값, 표준편차 등
- **개선 권장사항**: 구체적인 개선 방안

### **4. 결과 내보내기 옵션**

```bash
# 모든 형식으로 내보내기
uv run python cli.py export-results result.json --format all --output-dir my_analysis

# CSV만 내보내기
uv run python cli.py export-results result.json --format csv --output-dir csv_only

# 보고서만 생성
uv run python cli.py export-results result.json --format report --output-dir reports
```

## 🌐 웹 대시보드 사용법

### **대시보드 실행**
```bash
uv run streamlit run src/presentation/web/main.py
```

### **주요 기능**
1. **데이터 업로드**: Excel/CSV/JSON 파일 직접 업로드
2. **모델 선택**: LLM과 임베딩 모델 독립적 선택
3. **실시간 모니터링**: 평가 진행상황 실시간 확인
4. **시각화**: 레이더 차트, 바 차트로 결과 분석
5. **히스토리**: 과거 평가 결과 비교
6. **다운로드**: 결과 파일 직접 다운로드

## 💻 CLI 고급 사용법

### **평가 명령어**

```bash
# 기본 평가
uv run python cli.py evaluate data.json --llm gemini --embedding bge_m3

# 다양한 모델 조합
uv run python cli.py evaluate data.json --llm hcx --embedding gemini
uv run python cli.py evaluate data.json --llm gemini --embedding hcx

# 상세 로그와 함께 실행
uv run python cli.py evaluate data.json --llm gemini --embedding bge_m3 --verbose

# 결과 저장 위치 지정
uv run python cli.py evaluate data.json --output my_results.json
```

### **대용량 데이터셋 처리**

50개 이상의 평가 항목이 있는 경우 자동으로 체크포인트가 활성화됩니다:

```bash
# 대용량 데이터셋 평가 (자동 체크포인트)
uv run python cli.py evaluate large_dataset.json --llm gemini --embedding bge_m3

# 중단된 평가 재개
uv run python cli.py list-checkpoints
uv run python cli.py resume-evaluation dataset_20241224_143022_abc12345

# 오래된 체크포인트 정리
uv run python cli.py cleanup-checkpoints --days 7
```

### **유용한 명령어**

```bash
# 사용 가능한 데이터셋 목록
uv run python cli.py list-datasets

# 지원하는 프롬프트 타입
uv run python cli.py list-prompts

# 도움말
uv run python cli.py --help
uv run python cli.py evaluate --help
```

## ✨ 주요 기능

### 🤖 **Multi-LLM & Multi-Embedding 지원**
- **Google Gemini 2.5 Flash**, **Naver HCX-005**, **BGE-M3 Local** 등 다양한 모델을 런타임에 선택
- **독립적 모델 조합**: LLM과 임베딩 모델을 자유롭게 조합 가능
- **HTTP 직접 호출**: LangChain 타임아웃 문제를 해결한 안정적인 API 호출

### 🚀 **로컬 환경 최적화**
- **BGE-M3 로컬 임베딩**: 완전한 오프라인 임베딩 처리 지원
- **GPU 자동 최적화**: CUDA, MPS(Apple Silicon), CPU 자동 감지 및 최적화
- **메모리 효율성**: 대용량 데이터셋 처리를 위한 배치 처리 및 메모리 관리

### 💾 **대용량 데이터셋 지원**
- **체크포인트 시스템**: 50개 이상 항목 시 자동 활성화
- **중단/재개 기능**: 평가 중단 시 정확한 지점에서 재개 가능
- **배치 처리**: 메모리 사용량 모니터링과 함께 안정적인 대용량 처리
- **진행률 추적**: 실시간 진행률 표시 및 예상 완료 시간

## 🛠️ 설치 및 환경 설정

### 🎯 설치 방법 선택

#### **일반 설치** (인터넷 연결 환경)
```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/RAGTrace.git
cd RAGTrace

# 2. 자동 설정 스크립트 실행 (권장)
chmod +x uv-setup.sh
./uv-setup.sh

# 3. API 키 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

#### **🛡️ 엔터프라이즈 오프라인 설치** (폐쇄망 환경)
```bash
# 1. 엔터프라이즈 패키지 생성 (인터넷 연결된 PC에서)
python create-enterprise-offline.py --output-dir ./packages

# 2. 시스템 검증 및 진단
python enterprise-validator.py --output system_report.json

# 3. 폐쇄망으로 패키지 이동 후 설치
# Windows: install.bat 실행
# Linux/macOS: bash install.sh
```

#### **🔧 Windows 완전 오프라인 설치**
```powershell
# 1. 안전한 패키지 생성 (Windows PC에서)
.\create-windows-offline-safe.ps1

# 2. 설치 전 시스템 테스트
.\test-windows-package.ps1

# 3. 폐쇄망 설치
# RAGTrace-Windows-Offline-Safe.zip 압축 해제 후
# 04_Scripts\install.bat 관리자 권한으로 실행
```

### 📋 시스템 요구사항

| 구분 | 일반 설치 | 엔터프라이즈 오프라인 |
|------|----------|------------------|
| **Python** | 3.11+ | 3.11+ |
| **패키지 매니저** | UV | UV (포함) |
| **디스크 공간** | 2GB+ | 5GB+ |
| **메모리** | 4GB+ | 8GB+ |
| **인터넷** | 필요 | 불필요 (설치 후) |
| **권한** | 일반 사용자 | 관리자 (Windows) |

### 지원 모델 및 API 키

| 카테고리 | 모델 | 식별자 | 필요한 API 키 |
|----------|------|--------|--------------|
| **LLM** | Google Gemini 2.5 Flash | `gemini` | `GEMINI_API_KEY` |
| | Naver HCX-005 | `hcx` | `CLOVA_STUDIO_API_KEY` |
| **Embedding** | Google Gemini | `gemini` | `GEMINI_API_KEY` |
| | Naver HCX | `hcx` | `CLOVA_STUDIO_API_KEY` |
| | BGE-M3 Local | `bge_m3` | API 키 불필요 (로컬) |

## 📁 프로젝트 구조

```
RAGTrace/
├── 📂 src/                          # 소스 코드
│   ├── 📂 application/              # 비즈니스 로직
│   ├── 📂 domain/                   # 도메인 모델
│   ├── 📂 infrastructure/           # 외부 연동
│   └── 📂 presentation/             # UI (CLI, Web)
├── 📂 scripts/                      # 유틸리티 스크립트
│   └── 📂 offline-packaging/        # 오프라인 패키지 생성 스크립트
├── 📂 docs/                         # 프로젝트 문서
├── 📂 data/                         # 샘플 데이터
├── 📂 quick_results/                # quick-eval 결과
├── cli.py                           # CLI 진입점
├── enterprise-validator.py          # 엔터프라이즈 검증 도구
└── README.md                        # 이 문서
```

## 🐳 Docker 배포 (선택사항)

프로덕션 환경이나 간편한 배포를 원하는 경우:

```bash
# Docker 이미지 실행
docker run -d -p 8501:8501 \
  -e GEMINI_API_KEY="your-api-key" \
  ghcr.io/ntts9990/ragtrace:latest
```

자세한 내용은 [Docker 배포 가이드](docs/deployment/Docker_Deployment_Guide.md)를 참고하세요.

## 🏢 엔터프라이즈 기능

### 🛡️ 완전 오프라인 배포
```bash
# 엔터프라이즈 패키지 생성
python scripts/offline-packaging/create-enterprise-offline.py --project-root . --output-dir ./enterprise-package

# 생성 결과
RAGTrace-Enterprise-[platform]-[arch].tar.gz
├── 01_Prerequisites/          # 사전 요구사항
├── 02_Dependencies/          # 200+ wheel 파일 + SHA-256 검증
├── 03_Source/               # 전체 소스 코드
├── 04_Scripts/              # 통합 설치 스크립트
├── 05_Documentation/        # 상세 문서
├── 06_Verification/         # 검증 도구
└── MANIFEST.json           # 패키지 메타데이터
```

### 🔍 시스템 진단 및 검증
```bash
# 완전한 시스템 검증
python enterprise-validator.py

# 진단 보고서 생성
python enterprise-validator.py --output diagnostic_report.json

# 간략한 결과만 출력
python enterprise-validator.py --quiet
```

**검증 항목:**
- ✅ 시스템 요구사항 (Python, 메모리, 디스크)
- ✅ 패키지 무결성 (SHA-256 체크섬)
- ✅ 의존성 충돌 검사
- ✅ 성능 벤치마크 (Import 속도, CPU/메모리)
- ✅ 보안 스캔 (취약점, 권한)
- ✅ RAGTrace 기능 테스트

### 🔧 Windows 환경 지원
```powershell
# Windows 전용 안전한 패키지 생성
.\create-windows-offline-safe.ps1

# 시스템 테스트 및 검증
.\test-windows-package.ps1

# 문제 해결 가이드 확인
Get-Content WINDOWS_오류해결가이드.md
```

## 🔧 문제 해결

### 일반적인 문제들

#### 🚨 **LangChain 타임아웃 문제** (해결됨)
v2.0에서 HTTP 직접 호출로 완전 해결:
```bash
# 이전: LangChain 타임아웃으로 0% 진행률 멈춤
# 현재: 안정적인 평가 완료 (1-2분 내 완료)
uv run python cli.py quick-eval evaluation_data
```

#### 🐍 **Python/UV 설치 문제**
```bash
# UV 설치 (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# UV 설치 (Windows PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Python 경로 확인
uv run python --version
```

#### 🔑 **API 키 설정 문제**
```bash
# .env 파일 생성 및 확인
cp .env.example .env
cat .env

# API 키 유효성 테스트
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Gemini API Key:', bool(os.getenv('GEMINI_API_KEY')))
print('HCX API Key:', bool(os.getenv('CLOVA_STUDIO_API_KEY')))
"
```

#### 💾 **메모리 부족 문제**
```bash
# BGE-M3 GPU 메모리 최적화
export BGE_M3_DEVICE="cpu"  # GPU 메모리 부족 시 CPU 사용

# 배치 크기 조정
uv run python cli.py evaluate data.json --batch-size 4  # 기본값: 8
```

### Windows 특화 문제 해결

#### 🛡️ **PowerShell 실행 정책 오류**
```powershell
# 실행 정책 변경 (관리자 권한)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 또는 일회성 실행
powershell -ExecutionPolicy Bypass -File script.ps1
```

#### 🔧 **관리자 권한 문제**
```cmd
# PowerShell 관리자 권한으로 실행
# 시작 메뉴 → PowerShell → 우클릭 → "관리자 권한으로 실행"

# 권한 확인
net session
```

#### 📦 **패키지 다운로드 실패**
```bash
# 네트워크 문제 해결
pip install --timeout 1000 --retries 10 package_name

# 프록시 환경
pip install --proxy http://proxy.company.com:8080 package_name
```

### 🚨 긴급 지원

#### **즉시 진단**
```bash
# 1단계: 종합 진단 실행
python enterprise-validator.py --output emergency_report.json

# 2단계: 시스템 정보 수집
python -c "
import sys, platform, subprocess
print(f'Platform: {platform.platform()}')
print(f'Python: {sys.version}')
try:
    result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
    print(f'UV: {result.stdout.strip()}')
except:
    print('UV: Not installed')
"

# 3단계: 로그 확인
tail -50 package_creation.log  # Linux/macOS
Get-Content -Tail 50 package_creation.log  # Windows
```

#### **자동 복구**
```bash
# 설치 롤백 (엔터프라이즈 버전)
python -c "
from create_enterprise_offline import InstallationRecoveryManager
recovery = InstallationRecoveryManager('./03_Source')
recovery.rollback()
"

# 캐시 정리 후 재설치
uv cache clean
uv sync --all-extras
```

### 📚 상세 가이드

| 문제 유형 | 가이드 문서 |
|----------|------------|
| **Windows 완전 설치** | [Windows 완전 가이드](docs/deployment/Windows_Complete_Guide.md) |
| **엔터프라이즈 배포** | [엔터프라이즈 패키지 시스템](docs/deployment/Enterprise_Package_System.md) |
| **Docker 배포** | [Docker 배포 가이드](docs/deployment/Docker_Deployment_Guide.md) |
| **개발 환경 설정** | [개발 가이드](docs/development/Development_Guide.md) |

## 🤝 기여하기

Pull Request는 언제나 환영합니다. 기여하기 전에 `docs/development/Development_Guide.md`를 참고해주세요.

## 📄 라이선스

이 프로젝트는 Apache License 2.0 하에 배포됩니다.

## 📞 지원 및 문의

- **이슈 트래커**: [GitHub Issues](https://github.com/ntts9990/RAGTrace/issues)
- **개발 가이드**: [Development Guide](docs/Development_Guide.md)
- **상세 문서**: [프로젝트 Wiki](https://github.com/ntts9990/RAGTrace/wiki)
- **엔터프라이즈 지원**: enterprise-validator.py 진단 도구 활용