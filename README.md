# 🔍 RAGTrace

**Multi-LLM RAG 시스템 성능 평가 및 분석 플랫폼**

RAGTrace는 RAG(Retrieval-Augmented Generation) 시스템의 핵심 품질 지표를 신뢰성 있게 평가하고 분석하기 위한 종합 플랫폼입니다. [RAGAS](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 하며, Clean Architecture와 완전한 의존성 주입을 통해 확장 가능하고 유지보수성이 높은 구조를 제공합니다.

- 📖 **[통합 개발 가이드](docs/Development_Guide.md)에서 더 자세한 내용을 확인하세요.**

## ✨ 주요 기능

### 🤖 **Multi-LLM & Multi-Embedding 지원**
- **Google Gemini 2.5 Flash**, **Naver HCX-005**, **BGE-M3 Local** 등 다양한 모델을 런타임에 선택
- **독립적 모델 조합**: LLM과 임베딩 모델을 자유롭게 조합 가능
- **HTTP 직접 호출**: LangChain 타임아웃 문제를 해결한 안정적인 API 호출

### 📊 **완전한 RAGAS 메트릭 지원**
- **Faithfulness**: 답변의 사실적 정확성 (문맥 일치도)
- **Answer Relevancy**: 질문과 답변의 연관성
- **Context Recall**: 관련 정보 검색 완성도
- **Context Precision**: 검색된 문맥의 정확성
- **Answer Correctness**: 정답(ground truth)과의 일치도

### 🚀 **로컬 환경 최적화**
- **BGE-M3 로컬 임베딩**: 완전한 오프라인 임베딩 처리 지원
- **GPU 자동 최적화**: CUDA, MPS(Apple Silicon), CPU 자동 감지 및 최적화
- **메모리 효율성**: 대용량 데이터셋 처리를 위한 배치 처리 및 메모리 관리

### 💾 **대용량 데이터셋 지원**
- **체크포인트 시스템**: 50개 이상 항목 시 자동 활성화
- **중단/재개 기능**: 평가 중단 시 정확한 지점에서 재개 가능
- **배치 처리**: 메모리 사용량 모니터링과 함께 안정적인 대용량 처리
- **진행률 추적**: 실시간 진행률 표시 및 예상 완료 시간

### 📤 **결과 분석 및 내보내기**
- **상세 CSV**: 개별 항목별 메트릭 점수
- **요약 통계**: 메트릭별 기초 통계 (평균, 중앙값, 표준편차 등)
- **분석 보고서**: 마크다운 형식의 상세 성능 분석 및 개선 권장사항
- **전체 패키지**: CSV, 요약, 보고서를 포함한 ZIP 파일

### 🌐 **인터랙티브 웹 대시보드**
- **실시간 모니터링**: 평가 과정을 실시간으로 추적
- **시각화**: Plotly 기반 레이더 차트, 바 차트, 트렌드 분석
- **히스토리 관리**: SQLite 기반 평가 이력 저장 및 비교
- **내보내기 기능**: 웹에서 직접 결과 다운로드

### 🏗️ **Clean Architecture & DI**
- **완전한 의존성 주입**: dependency-injector 프레임워크 사용
- **Port-Adapter 패턴**: 새로운 LLM, 임베딩 모델을 최소한의 코드로 추가
- **전략 패턴**: 다양한 평가 전략 지원 (표준, 커스텀, HCX 전용)
- **확장성**: 새로운 메트릭, 데이터 소스, UI 컴포넌트 쉽게 추가

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

### 사전 요구사항
- Python 3.11+
- [UV](https://docs.astral.sh/uv/) 패키지 매니저
- API 키 (`.env` 파일에 설정)

### 설치 및 설정

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/RAGTrace.git
cd RAGTrace

# 2. (선택) 자동 설정 스크립트 실행
# 이 스크립트는 가상 환경 생성, 의존성 설치, .env 파일 복사를 한번에 수행합니다.
chmod +x uv-setup.sh
./uv-setup.sh

# 3. (수동 설정 시) 의존성 설치
uv sync --all-extras

# 4. .env 파일 생성 및 API 키 입력
# cp .env.example .env # 예제 파일 복사
# nano .env
```

`.env` 파일에 `GEMINI_API_KEY` 등을 설정해야 합니다.

## 💻 사용법

### 🐳 Docker를 통한 배포 (가장 간단)

```bash
# Docker 이미지 실행 (1분 이내 시작)
docker run -d -p 8501:8501 \
  -e GEMINI_API_KEY="your-api-key" \
  ghcr.io/ntts9990/ragtrace:latest

# 브라우저에서 http://localhost:8501 접속
```

자세한 Docker 배포 방법은 [Docker 배포 가이드](docs/Docker_Deployment_Guide.md)를 참고하세요.

### 웹 대시보드 (로컬 실행)

```bash
# uv를 사용하여 대시보드 실행
uv run streamlit run src/presentation/web/main.py

# 또는 justfile을 사용 (Just 설치 시)
just dashboard
```
브라우저에서 `http://localhost:8501`에 접속하여 평가를 시작하세요.

### CLI 고급 평가

CLI를 통해 더 세밀한 제어와 대용량 데이터셋 처리가 가능합니다.

```bash
# 기본 평가 실행
uv run python cli.py evaluate evaluation_data --llm gemini --embedding bge_m3

# 다양한 모델 조합
uv run python cli.py evaluate evaluation_data --llm hcx --embedding bge_m3
uv run python cli.py evaluate evaluation_data --llm gemini --embedding gemini

# 결과를 파일로 저장하고 상세 로그 출력
uv run python cli.py evaluate evaluation_data --llm gemini --embedding bge_m3 --output result.json --verbose

# Excel/CSV 데이터 import 및 평가
uv run python cli.py import-data your_data.xlsx --validate --output converted_data.json
uv run python cli.py evaluate converted_data --llm gemini --embedding bge_m3

# 결과 내보내기 (CSV, 요약, 분석보고서)
uv run python cli.py export-results result.json --format all --output-dir analysis_results

# 대용량 데이터셋 체크포인트 관리
uv run python cli.py list-checkpoints
uv run python cli.py resume-evaluation [session_id]
uv run python cli.py cleanup-checkpoints --days 7

# 사용 가능한 옵션 확인
uv run python cli.py --help
```

#### 📊 **평가 결과 예시**
```
==================================================
📊 평가 결과 요약
==================================================
ragas_score      : 0.7820
answer_relevancy : 0.7276
faithfulness    : 0.8333
context_recall   : 1.0000
context_precision: 0.6667
answer_correctness: 0.6822
==================================================
```

#### 📊 Excel/CSV 데이터 형식

Excel 또는 CSV 파일은 다음 4개 컬럼을 포함해야 합니다:

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `question` | 평가할 질문 | "원자력 발전소의 주요 구성요소는?" |
| `contexts` | 참고 문맥들 | JSON 배열 또는 `;` 구분 |
| `answer` | 시스템 답변 | "원자로, 증기발생기, 터빈발전기..." |
| `ground_truth` | 정답 기준 | "원자로, 증기발생기, 터빈발전기" |

**contexts 작성 방법:**
- JSON 배열: `["첫 번째 문맥", "두 번째 문맥"]` (권장)
- 세미콜론 구분: `첫 번째 문맥;두 번째 문맥`
- 파이프 구분: `첫 번째 문맥|두 번째 문맥`
- 단일 문맥: `하나의 긴 문맥 내용`

## 📁 프로젝트 구조

```
RAGTrace/
├── 📂 src/                          # 소스 코드 (Clean Architecture)
│   ├── 📂 application/              # 애플리케이션 계층 (Use Cases, Ports)
│   │   ├── ports/
│   │   ├── services/
│   │   └── use_cases/
│   ├── 📂 container/                # 의존성 주입 (DI) 컨테이너
│   ├── 📂 domain/                   # 도메인 계층 (Entities, Value Objects)
│   │   ├── entities/
│   │   └── value_objects/
│   ├── 📂 infrastructure/           # 인프라 계층 (DB, API, Adapters)
│   │   ├── data_import/
│   │   ├── evaluation/
│   │   ├── llm/
│   │   └── repository/
│   ├── 📂 presentation/             # 프레젠테이션 계층 (CLI, Web UI)
│   │   └── web/
│   └── 📂 utils/                    # 공통 유틸리티
│
├── 📂 data/                         # 평가 데이터 및 DB
├── 📂 docs/                         # 핵심 문서
├── 📂 models/                       # (Git 추적 제외) 로컬 모델 저장소
├── 📂 tests/                        # 테스트 코드 (90%+ 커버리지)
│
├── cli.py                           # CLI 애플리케이션 진입점
├── run_dashboard.py                 # 웹 대시보드 실행 스크립트
├── pyproject.toml                   # 프로젝트 및 의존성 설정
└── README.md                        # 이 파일
```

## 🔧 기술 스택 및 특징

### **핵심 기술**
- **언어**: Python 3.11+
- **패키지 관리**: `uv` (고성능 Python 패키지 매니저)
- **아키텍처**: Clean Architecture + Dependency Injection
- **평가 프레임워크**: RAGAS (v0.1.0+)
- **웹 UI**: Streamlit + Plotly
- **데이터베이스**: SQLite (평가 히스토리)
- **로컬 AI**: BGE-M3 + sentence-transformers

### **품질 보증**
- **코드 품질**: `black`, `isort`, `ruff`, `mypy`
- **테스트**: `pytest`, `pytest-cov` (90%+ 커버리지)
- **CI/CD**: GitHub Actions
- **의존성 관리**: UV lockfile + 보안 스캔

### **성능 최적화**
- **GPU 가속**: CUDA, MPS(Apple Silicon) 자동 감지
- **메모리 관리**: 배치 처리 + 가비지 컬렉션
- **체크포인트**: 대용량 데이터셋 중단/재개
- **HTTP 최적화**: LangChain 우회한 직접 API 호출

### **최신 업데이트 (2024)**
- ✅ **Answer Correctness 메트릭**: 완전한 5개 RAGAS 메트릭 지원
- ✅ **HCX-005 SingleTurnSample 호환성**: Naver HCX 모델 완전 지원
- ✅ **체크포인트 시스템**: 대용량 데이터셋 안정적 처리
- ✅ **결과 내보내기**: CSV, 요약 통계, 분석 보고서 생성
- ✅ **HTTP 안정성**: LangChain 타임아웃 문제 해결

## 📚 **상세 사용법**

### **CLI 명령어 레퍼런스**

```bash
# 데이터셋 관리
uv run python cli.py list-datasets              # 사용 가능한 데이터셋 목록
uv run python cli.py list-prompts               # 지원 프롬프트 타입 목록

# 데이터 변환
uv run python cli.py import-data data.xlsx --validate --output converted.json

# 평가 실행
uv run python cli.py evaluate [dataset] --llm [model] --embedding [model] [options]

# 결과 관리
uv run python cli.py export-results result.json --format all --output-dir exports

# 체크포인트 관리 (대용량 데이터셋)
uv run python cli.py list-checkpoints           # 체크포인트 목록
uv run python cli.py resume-evaluation [id]     # 중단된 평가 재개
uv run python cli.py cleanup-checkpoints --days 7  # 오래된 체크포인트 정리
```

### **지원 모델**

| 카테고리 | 모델 | 식별자 | 요구사항 |
|----------|------|--------|----------|
| **LLM** | Google Gemini 2.5 Flash | `gemini` | `GEMINI_API_KEY` |
| | Naver HCX-005 | `hcx` | `CLOVA_STUDIO_API_KEY` |
| **Embedding** | Google Gemini | `gemini` | `GEMINI_API_KEY` |
| | Naver HCX | `hcx` | `CLOVA_STUDIO_API_KEY` |
| | BGE-M3 Local | `bge_m3` | 로컬 모델 (자동 다운로드) |

### **성능 벤치마크**

| 구성 | 처리 속도 | 메모리 사용량 | 특징 |
|------|-----------|---------------|------|
| Gemini + BGE-M3 (MPS) | ~15 items/min | ~2GB | 로컬 임베딩, GPU 가속 |
| HCX + BGE-M3 (MPS) | ~8 items/min | ~2GB | API 제한, 로컬 임베딩 |
| Gemini + Gemini | ~12 items/min | ~500MB | 완전 클라우드 |

### **체크포인트 시스템**

```bash
# 대용량 데이터셋 (50+ 항목) 자동 체크포인트
uv run python cli.py evaluate large_dataset --llm gemini --embedding bge_m3

# 진행률 추적
📊 대량 데이터셋 감지 (120개 항목)
💾 자동으로 체크포인트 기능을 활성화합니다.
🔄 배치 처리: 1-10/120
💾 체크포인트 업데이트: 10/120 (8.3%)

# 중단 후 재개
uv run python cli.py resume-evaluation dataset_20241224_143022_abc12345
```

## 🤝 기여하기

Pull Request는 언제나 환영합니다. 기여하기 전에 `docs/Development_Guide.md`를 참고해주세요.

### **개발 환경 설정**
```bash
# 개발 의존성 설치
uv sync --extra dev

# 코드 품질 검사
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/

# 테스트 실행
uv run pytest tests/ --cov=src --cov-report=html
```

## 📄 라이선스

이 프로젝트는 Apache License 2.0 하에 배포됩니다.