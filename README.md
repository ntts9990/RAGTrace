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
- **타임아웃 관리**: 장시간 실행 방지를 위한 지능적 타임아웃
- **부분 성공 허용**: API 실패 시에도 가능한 결과 제공
- **타입 안전성**: 전체 코드베이스에 걸친 엄격한 타입 힌트

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.11+
- Google Gemini API 키 (필수)
- Naver CLOVA Studio API 키 (HCX 사용 시 선택)

### 설치 및 설정

1. **리포지토리 클론:**
   ```bash
   git clone https://github.com/your-username/RAGTrace.git
   cd RAGTrace
   ```

2. **가상 환경 및 의존성 설치:**
   ```bash
   # uv 사용 (권장)
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   uv pip install dependency-injector ragas google-generativeai python-dotenv
   uv pip install streamlit plotly pandas numpy requests

   # 또는 pip 사용
   pip install -r requirements.txt
   ```

3. **환경 변수 설정:**
   ```bash
   # .env 파일 생성
   cat > .env << 'EOF'
   # 필수: Google Gemini API 키
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # 선택: Naver HCX API 키
   CLOVA_STUDIO_API_KEY=your_clova_studio_api_key_here
   
   # 선택: 기본 LLM 설정
   DEFAULT_LLM=gemini
   EOF
   ```

## 💻 사용법

### 웹 대시보드 (권장)

가장 직관적이고 기능이 풍부한 방법입니다:

```bash
streamlit run src/presentation/web/main.py
```

웹 브라우저에서 http://localhost:8501 접속 후:
1. 🚀 **New Evaluation** 페이지로 이동
2. **LLM 모델 선택** (Gemini/HCX)
3. **프롬프트 타입 선택** (기본/한국어 기술문서/다국어)
4. **데이터셋 선택**
5. **🚀 평가 시작** 버튼 클릭

### CLI (고급 사용자)

```bash
# 기본 평가 (Gemini 사용)
python cli.py evaluate evaluation_data

# 특정 LLM 선택
python cli.py evaluate evaluation_data.json --llm gemini
python cli.py evaluate evaluation_data.json --llm hcx

# LLM과 임베딩 모델 독립 선택
python cli.py evaluate evaluation_data.json --llm gemini --embedding hcx
python cli.py evaluate evaluation_data.json --llm hcx --embedding gemini

# 커스텀 프롬프트 사용
python cli.py evaluate evaluation_data.json --llm gemini --prompt-type korean_tech

# 사용 가능한 옵션 확인
python cli.py list-datasets
python cli.py list-prompts

# 상세 로그와 함께 실행
python cli.py evaluate evaluation_data --llm gemini --verbose
```

### 기본 실행

```bash
# 설정된 기본 LLM으로 간단 실행
python src/presentation/main.py
```

### 연결 테스트

```bash
# API 연결 및 기본 기능 테스트
python hello.py
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
│   │   │   ├── gemini_adapter.py    # Google Gemini 연동
│   │   │   └── hcx_adapter.py       # Naver HCX 연동
│   │   ├── embedding/               # 임베딩 어댑터
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
├── hello.py                        # 연결 테스트
├── .env                           # 환경 변수 (생성 필요)
├── CLAUDE.md                      # Claude Code 가이드
└── README.md                      # 이 파일
```

## 🔧 고급 설정

### LLM 모델 설정

```python
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
   # 의존성 재설치
   uv pip install dependency-injector ragas google-generativeai
   ```

3. **성능 문제**
   ```bash
   # 더 적은 QA 쌍으로 테스트
   # 또는 timeout 증가 (config.py에서 설정)
   ```

4. **데이터베이스 문제**
   ```bash
   # 데이터베이스 초기화
   rm -f data/db/evaluations.db
   ```

### 디버그 명령어

```bash
# 기본 연결 테스트
python hello.py

# 컨테이너 상태 확인
python -c "from src.container import container; print('✅ Container OK')"

# 데이터셋 확인
python cli.py list-datasets

# LLM 어댑터 테스트
python -c "from src.container import get_evaluation_use_case_with_llm; print('✅ DI OK')"
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