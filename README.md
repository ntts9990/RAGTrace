# 🔍 RAGTrace

**Multi-LLM RAG 시스템 성능 평가 및 분석 플랫폼**

RAGTrace는 RAG(Retrieval-Augmented Generation) 시스템의 핵심 품질 지표를 신뢰성 있게 평가하고 분석하기 위한 종합 플랫폼입니다. [RAGAS](https://github.com/explodinggradients/ragas) 프레임워크를 기반으로 하며, Clean Architecture와 완전한 의존성 주입을 통해 확장 가능하고 유지보수성이 높은 구조를 제공합니다.

## ✨ 주요 기능

### 🤖 Multi-LLM & Multi-Embedding 지원
- **Google Gemini 2.5 Flash**: 빠르고 효율적인 범용 LLM
- **Naver HCX-005**: 한국어에 특화된 고성능 LLM
- **Google Gemini Embedding**: 다국어 임베딩 모델
- **Naver HCX Embedding**: 한국어 특화 임베딩 모델
- **런타임 모델 선택**: CLI와 웹 UI에서 동적 LLM/임베딩 모델 전환
- **최적화된 성능**: Rate limiting 제거로 빠른 평가 처리

### 📊 포괄적인 평가 지표
- **Faithfulness (충실성)**: 답변이 주어진 컨텍스트에 얼마나 충실한가
- **Answer Relevancy (답변 관련성)**: 답변이 질문에 얼마나 직접적으로 연관되는가
- **Context Recall (컨텍스트 재현율)**: 정답에 필요한 모든 정보가 검색되었는가
- **Context Precision (컨텍스트 정확성)**: 검색된 컨텍스트가 질문과 얼마나 관련이 있는가
- **RAGAS Score**: 종합 평가 점수

### 🌐 인터랙티브 웹 대시보드
- **실시간 평가**: 진행 상황과 메트릭을 실시간으로 확인
- **LLM 선택 UI**: 웹 인터페이스에서 간편한 모델 선택
- **히스토리 관리**: SQLite 기반 평가 결과 이력 추적
- **시각화**: Plotly를 활용한 직관적인 차트와 그래프
- **상세 분석**: 개별 QA 쌍에 대한 심층 분석

### 🏗️ 견고한 아키텍처
- **Clean Architecture**: 도메인, 애플리케이션, 인프라 계층 완전 분리
- **Dependency Injection**: dependency-injector를 통한 완전한 DI
- **Port-Adapter 패턴**: 모든 외부 의존성 추상화
- **Error Recovery**: 포괄적인 오류 처리 및 복구 메커니즘

### 🛡️ 안정성 및 품질
- **데이터 사전 검증**: 평가 전 데이터 품질 자동 검사
- **HTTP 직접 호출**: LangChain 타임아웃 문제 해결을 위한 HTTP API 직접 연동
- **네트워크 안정성**: DNS 해결 및 API 연결 실패 방지
- **부분 성공 허용**: API 실패 시에도 가능한 결과 제공
- **타입 안전성**: 전체 코드베이스에 걸친 엄격한 타입 힌트

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.11+
- UV 패키지 매니저 ([설치 가이드](https://docs.astral.sh/uv/))
- Google Gemini API 키 (필수)
- Naver CLOVA Studio API 키 (HCX 사용 시 선택)

### UV 설치

UV가 설치되지 않은 경우:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Homebrew (macOS)
brew install uv

# pip 사용
pip install uv
```

### 빠른 설정

#### 옵션 1: 자동 설정 (권장)
```bash
git clone https://github.com/your-username/RAGTrace.git
cd RAGTrace

# 자동 설정 스크립트 실행
chmod +x uv-setup.sh
./uv-setup.sh
```

#### 옵션 2: 수동 설정
```bash
git clone https://github.com/your-username/RAGTrace.git
cd RAGTrace

# 가상 환경 생성 및 의존성 설치
uv sync --all-extras

# 환경 변수 설정
cat > .env << 'EOF'
# 필수: Google Gemini API 키
GEMINI_API_KEY=your_gemini_api_key_here

# 선택: Naver HCX API 키
CLOVA_STUDIO_API_KEY=your_clova_studio_api_key_here

# 선택: 기본 LLM 설정
DEFAULT_LLM=gemini
EOF
```

#### 환경 테스트
```bash
# 설정 확인
uv run python hello.py
```

## 💻 사용법

### 웹 대시보드 (권장)

가장 직관적이고 기능이 풍부한 방법입니다:

```bash
# UV를 사용한 실행 (권장)
uv run streamlit run src/presentation/web/main.py

# 또는 Just 명령어 사용
just dashboard
```

웹 브라우저에서 http://localhost:8501 접속 후:
1. 🚀 **New Evaluation** 페이지로 이동
2. **LLM 모델 선택** (Gemini/HCX)
3. **프롬프트 타입 선택** (기본/한국어 기술문서/다국어)
4. **데이터셋 선택**
5. **🚀 평가 시작** 버튼 클릭

### CLI (고급 사용자)

```bash
# UV를 사용한 CLI 실행 (권장)
uv run python cli.py evaluate evaluation_data

# 특정 LLM 선택
uv run python cli.py evaluate evaluation_data.json --llm gemini
uv run python cli.py evaluate evaluation_data.json --llm hcx

# LLM과 임베딩 모델 독립 선택
uv run python cli.py evaluate evaluation_data.json --llm gemini --embedding hcx
uv run python cli.py evaluate evaluation_data.json --llm hcx --embedding gemini

# 커스텀 프롬프트 사용
uv run python cli.py evaluate evaluation_data.json --llm gemini --prompt-type korean_tech

# 사용 가능한 옵션 확인
uv run python cli.py list-datasets
uv run python cli.py list-prompts

# Just 명령어로 간편 실행
just eval evaluation_data
just eval-llm evaluation_data gemini
```

### UV 명령어 참조

```bash
# 의존성 관리
uv sync                    # 기본 의존성 설치
uv sync --all-extras      # 모든 추가 의존성 설치
uv sync --extra dev       # 개발 의존성만 설치
uv sync --no-dev         # 프로덕션 의존성만 설치

# 애플리케이션 실행
uv run streamlit run src/presentation/web/main.py
uv run python cli.py evaluate evaluation_data
uv run python hello.py   # 환경 테스트

# 개발 도구
uv run pytest           # 테스트 실행
uv run black src/        # 코드 포맷팅
uv run ruff check src/   # 린팅
uv run mypy src/         # 타입 체크
```

### Just 명령어 (선택사항)

Just가 설치된 경우 더 간편한 명령어 사용 가능:

```bash
just setup              # 환경 설정
just dashboard          # 웹 대시보드 실행
just eval              # 기본 평가 실행
just test              # 테스트 실행
just check             # 코드 품질 검사
just --list            # 사용 가능한 명령어 목록
```

## 📁 프로젝트 구조

```
RAGTrace/
├── 📂 src/                          # 소스 코드
│   ├── 📂 domain/                   # 도메인 모델
│   │   ├── entities/                # 핵심 엔티티
│   │   ├── value_objects/           # 값 객체 (메트릭, 임계값)
│   │   ├── exceptions.py            # 도메인 예외
│   │   └── prompts.py               # 프롬프트 타입 정의
│   │
│   ├── 📂 application/              # 애플리케이션 계층
│   │   ├── ports/                   # 인터페이스 정의
│   │   ├── services/                # 비즈니스 로직 서비스
│   │   └── use_cases/               # 유스케이스 구현
│   │
│   ├── 📂 infrastructure/           # 인프라스트럭처 계층
│   │   ├── llm/                     # LLM 어댑터
│   │   │   ├── gemini_adapter.py    # Google Gemini 연동 (HTTP 직접 호출)
│   │   │   ├── http_gemini_wrapper.py # HTTP Gemini API 래퍼
│   │   │   └── hcx_adapter.py       # Naver HCX 연동
│   │   ├── embedding/               # 임베딩 어댑터
│   │   │   ├── gemini_http_adapter.py # Google Gemini Embedding (HTTP)
│   │   │   └── hcx_adapter.py       # Naver HCX 임베딩 연동
│   │   ├── evaluation/              # 평가 프레임워크 연동
│   │   └── repository/              # 데이터 저장소
│   │
│   ├── 📂 presentation/             # 프레젠테이션 계층
│   │   ├── web/                     # 웹 대시보드
│   │   │   ├── components/          # UI 컴포넌트
│   │   │   │   ├── llm_selector.py  # LLM 선택 UI
│   │   │   │   └── prompt_selector.py # 프롬프트 선택 UI
│   │   │   └── main.py              # 메인 대시보드
│   │   └── main.py                  # CLI 진입점
│   │
│   ├── config.py                    # 설정 관리
│   └── container.py                 # DI 컨테이너
│
├── 📂 data/                         # 평가 데이터
│   ├── evaluation_data.json         # 샘플 데이터셋
│   └── db/                          # SQLite 데이터베이스
│
├── 📂 docs/                         # 문서
│   ├── RAGTRACE_METRICS.md          # 메트릭 상세 설명 (한국어)
│   └── LLM_Customization_Manual.md  # LLM 커스터마이징 가이드
│
├── cli.py                          # 고급 CLI 진입점
├── hello.py                        # 연결 테스트 스크립트
├── uv-setup.sh                     # UV 자동 설정 스크립트
├── justfile                        # Just 작업 실행기
├── pyproject.toml                  # UV 프로젝트 설정
├── uv.toml                         # UV 전용 설정
├── uv.lock                         # 의존성 락 파일
├── .python-version                 # Python 버전 지정
├── .env                           # 환경 변수 (생성 필요)
├── UV_SETUP.md                    # UV 상세 설정 가이드
├── CLAUDE.md                      # Claude Code 가이드
└── README.md                      # 이 파일
```

## 🔧 기술적 특징

### HTTP 직접 호출 아키텍처

RAGTrace는 안정성과 성능을 위해 LangChain의 Google GenAI 라이브러리 대신 HTTP API를 직접 호출합니다:

- **HttpGeminiWrapper**: Google Gemini API를 HTTP로 직접 호출하는 LangChain 호환 래퍼
- **GeminiHttpEmbeddingAdapter**: Gemini Embedding API의 HTTP 직접 호출 어댑터
- **타임아웃 방지**: DNS 해결 실패 및 라이브러리 내부 타임아웃 문제 해결
- **안정성 향상**: 네트워크 연결 문제에 대한 더 나은 제어와 오류 처리

이 접근 방식으로 기존의 0% 진행률 타임아웃 문제가 완전히 해결되었습니다.

## 🔧 고급 설정

### UV 환경 관리

#### 다중 환경 지원
```bash
# 개발 환경
uv sync --extra dev

# 성능 분석 환경
uv sync --extra performance

# 데이터 분석 환경
uv sync --extra analysis

# 전체 환경
uv sync --all-extras
```

#### 의존성 관리
```bash
# 새 패키지 추가
uv add numpy pandas

# 개발 전용 패키지 추가
uv add --dev pytest black

# 패키지 제거
uv remove numpy

# 의존성 업데이트
uv lock --upgrade

# 의존성 트리 확인
uv tree
```

### LLM 모델 설정

```bash
# .env 파일에서 상세 설정 가능
GEMINI_MODEL_NAME=models/gemini-2.5-flash-preview-05-20
GEMINI_EMBEDDING_MODEL_NAME=models/gemini-embedding-exp-03-07

HCX_MODEL_NAME=HCX-005

DEFAULT_LLM=gemini  # 또는 "hcx"
```

### 프롬프트 커스터마이징

```python
# 사용 가능한 프롬프트 타입
DEFAULT_PROMPT_TYPE=default           # 기본 RAGAS 프롬프트
# nuclear_hydro_tech                 # 원자력/수력 기술 문서용
# korean_formal                      # 한국어 공식 문서용
```

### 평가 데이터 형식

```json
{
  "question": "질문 내용",
  "answer": "모델이 생성한 답변",
  "contexts": ["관련 문서 1", "관련 문서 2"],
  "ground_truth": "정답 (Context Recall 계산용, 선택사항)"
}
```

## 📊 메트릭 해석

| 메트릭 | 범위 | 권장 임계값 | 의미 |
|--------|------|-------------|------|
| **Faithfulness** | 0.0-1.0 | ≥ 0.9 | 답변의 사실적 정확성 |
| **Answer Relevancy** | 0.0-1.0 | ≥ 0.8 | 질문-답변 연관성 |
| **Context Recall** | 0.0-1.0 | ≥ 0.9 | 정보 검색 완성도 |
| **Context Precision** | 0.0-1.0 | ≥ 0.8 | 검색 정확성 |
| **RAGAS Score** | 0.0-1.0 | ≥ 0.8 | 종합 성능 지표 |

자세한 메트릭 설명은 [docs/RAGTRACE_METRICS.md](docs/RAGTRACE_METRICS.md)를 참조하세요.

## 🐛 문제 해결

### 일반적인 문제

1. **API 키 오류**
   ```bash
   # .env 파일 확인
   cat .env | grep API_KEY
   ```

2. **Import 오류**
   ```bash
   # 의존성 재설치 (UV 사용)
   uv sync --all-extras
   
   # 또는 캐시 클리어 후 재설치
   uv cache clean
   uv sync --all-extras
   ```

3. **평가 타임아웃 문제**
   ```bash
   # HTTP 래퍼 사용으로 해결됨 (더 이상 타임아웃 없음)
   # 만약 여전히 문제가 있다면 더 적은 QA 쌍으로 테스트
   uv run python src/presentation/main.py evaluation_data_variant1 --llm gemini
   ```

4. **UV 관련 문제**
   ```bash
   # UV 캐시 클리어
   uv cache clean
   
   # UV 락 파일 재생성
   rm uv.lock
   uv lock
   
   # Python 버전 확인
   uv python list
   uv python install 3.11
   ```

5. **데이터베이스 문제**
   ```bash
   # 데이터베이스 초기화
   rm -f data/db/evaluations.db
   ```

### 디버그 명령어

```bash
# 기본 연결 테스트 (UV 사용)
uv run python hello.py

# 컨테이너 상태 확인
uv run python -c "from src.container import container; print('✅ Container OK')"

# 데이터셋 확인
uv run python cli.py list-datasets

# LLM 어댑터 테스트
uv run python -c "from src.container import get_evaluation_use_case_with_llm; print('✅ DI OK')"

# Just 명령어 사용 (간편함)
just test-connection
just eval
just diagnose
```

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 Apache License ver 2.0 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 글

- [RAGAS](https://github.com/explodinggradients/ragas) - 핵심 평가 프레임워크
- [Google Generative AI](https://ai.google.dev/) - Gemini LLM 지원
- [Naver CLOVA Studio](https://www.ncloud.com/product/aiService/clovaStudio) - HCX LLM 지원
- [Streamlit](https://streamlit.io/) - 웹 대시보드 프레임워크
- [dependency-injector](https://python-dependency-injector.ets-labs.org/) - 의존성 주입 프레임워크

---

**RAGTrace**로 더 나은 RAG 시스템을 구축하세요! 🚀

질문이나 제안사항이 있으시면 언제든지 Issue를 생성해 주세요.