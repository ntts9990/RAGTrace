# 폐쇄망 환경 RAGTrace 개선 계획

## 현재 상황 분석

### 폐쇄망에서 가능한 기능
✅ **BGE-M3 로컬 임베딩**: 완전 오프라인 동작 가능
✅ **로컬 데이터 처리**: 파일 기반 평가 데이터
✅ **SQLite 저장소**: 외부 DB 연결 불필요
✅ **웹 대시보드**: 로컬 서버 실행

### 폐쇄망에서 제한되는 기능
❌ **Gemini API**: 인터넷 연결 필요
❌ **HCX API**: 인터넷 연결 필요
❌ **모델 자동 다운로드**: Hugging Face Hub 접근 불가

## 우선순위별 개선사항

### 🚨 1순위: 오프라인 LLM 지원 (Critical)

#### 문제점
- 현재 Gemini와 HCX 모델은 모두 API 기반
- 폐쇄망에서는 평가 자체가 불가능

#### 해결 방안
```python
# 1. Ollama 통합
class OllamaAdapter(LLMAdapter):
    """로컬 Ollama 서버 연동"""
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
    
    def generate(self, prompt: str) -> str:
        # Ollama API 호출
        pass

# 2. HuggingFace Transformers 직접 통합
class LocalTransformersAdapter(LLMAdapter):
    """로컬 HuggingFace 모델 직접 실행"""
    def __init__(self, model_path: str, device: str = "auto"):
        self.model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
```

#### 구현 단계
1. **Ollama 어댑터 개발** (가장 실용적)
2. **Transformers 직접 통합** (메모리 효율성 고려)
3. **vLLM 서버 연동** (고성능 추론용)
4. **설정 UI 추가** (모델 경로/서버 URL 설정)

### 🔧 2순위: 오프라인 모델 관리 시스템 (High)

#### 문제점
- BGE-M3 모델이 수동으로 다운로드되어 있어야 함
- 새로운 환경 구축 시 모델 준비 복잡

#### 해결 방안
```bash
# 모델 패키징 스크립트
python scripts/package_models.py --output models_package.tar.gz
# 포함 내용:
# - BGE-M3 (임베딩)
# - Llama 3.1 8B (LLM)
# - Qwen2.5 7B (한국어 특화)
# - 설치 스크립트
```

#### 기능 설계
```python
class OfflineModelManager:
    """오프라인 모델 관리"""
    
    def scan_available_models(self) -> Dict[str, ModelInfo]:
        """로컬에 설치된 모델 스캔"""
        pass
    
    def install_model_package(self, package_path: str):
        """모델 패키지 설치"""
        pass
    
    def validate_models(self) -> ModelValidationReport:
        """모델 무결성 검증"""
        pass
```

### 📊 3순위: 향상된 데이터 관리 (Medium)

#### 문제점
- 현재 JSON 파일 기반으로만 데이터 입력
- 대용량 데이터 처리 시 불편

#### 해결 방안
```python
# 1. 다양한 형식 지원
class DataImporter:
    """다양한 데이터 형식 지원"""
    
    def import_excel(self, file_path: str) -> List[EvaluationData]:
        """Excel 파일 import"""
        pass
    
    def import_csv(self, file_path: str) -> List[EvaluationData]:
        """CSV 파일 import"""
        pass
    
    def import_database(self, connection_string: str) -> List[EvaluationData]:
        """로컬 DB import"""
        pass

# 2. 배치 처리 지원  
class BatchProcessor:
    """대용량 데이터 배치 처리"""
    
    def process_large_dataset(self, dataset_path: str, batch_size: int = 50):
        """청크 단위 처리로 메모리 효율성 확보"""
        pass
```

### 🎯 4순위: 전용 설정 관리 (Medium)

#### 문제점
- API 키 설정이 폐쇄망에서 의미 없음
- 오프라인 환경 특화 설정 부족

#### 해결 방안
```python
# config/air_gapped.py
class AirGappedConfig:
    """폐쇄망 전용 설정"""
    
    # 로컬 모델 경로
    LOCAL_LLM_PATH: str = "./models/llama3.1-8b"
    LOCAL_EMBEDDING_PATH: str = "./models/bge-m3"
    
    # Ollama 서버 설정
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODELS: List[str] = ["llama3.1:8b", "qwen2.5:7b"]
    
    # 배치 처리 설정
    BATCH_SIZE: int = 10  # 메모리 고려하여 작게
    ENABLE_GPU: bool = True
    
    # 네트워크 관련 비활성화
    DISABLE_INTERNET_CHECK: bool = True
    OFFLINE_MODE: bool = True
```

### 🖥️ 5순위: 개선된 UI/UX (Low)

#### 개선 영역
```python
# 1. 오프라인 상태 표시
class OfflineStatusWidget:
    """오프라인 모드 상태 표시"""
    def render(self):
        st.info("🔒 오프라인 모드 - 로컬 모델 사용 중")
        st.success(f"✅ LLM: {current_llm_model}")
        st.success(f"✅ 임베딩: {current_embedding_model}")

# 2. 모델 상태 모니터링
class ModelHealthDashboard:
    """모델 상태 대시보드"""
    def show_model_status(self):
        st.subheader("🏥 모델 상태")
        # GPU 사용률, 메모리 사용량, 응답 시간 등
```

## 구현 로드맵

### Phase 1: 핵심 오프라인 기능 (2-3주)
```python
# 목표: 폐쇄망에서 기본 평가 가능
1. Ollama 어댑터 구현
   - 기본 LLM 통신
   - RAGAS 평가 통합
   
2. 오프라인 모드 설정
   - 네트워크 체크 비활성화
   - 로컬 전용 설정

3. 기본 테스트
   - Ollama + BGE-M3 조합으로 평가 실행
   - 웹 대시보드에서 오프라인 모드 표시
```

### Phase 2: 모델 관리 개선 (1-2주)
```python
# 목표: 모델 설치/관리 자동화
1. 모델 패키징 도구
   - 필요한 모델들을 하나의 패키지로
   - 설치 스크립트 포함

2. 모델 검증 시스템
   - 모델 파일 무결성 체크
   - 호환성 검증

3. 설정 마법사
   - 첫 실행 시 모델 경로 설정
   - 자동 환경 감지
```

### Phase 3: 데이터 처리 강화 (1-2주)
```python
# 목표: 다양한 데이터 형식 지원
1. 데이터 Import 확장
   - Excel, CSV 지원
   - 데이터 검증 강화

2. 배치 처리 최적화
   - 대용량 데이터 청크 처리
   - 진행률 표시

3. 결과 Export 확장
   - 다양한 형식으로 결과 출력
   - 보고서 템플릿
```

## 예상 기술 스택

### 오프라인 LLM
```yaml
옵션 1 - Ollama (권장):
  장점: 설치 간단, 다양한 모델 지원, API 호환성
  단점: 별도 서버 필요
  
옵션 2 - Transformers 직접:
  장점: 완전 통합, 의존성 최소화
  단점: 메모리 사용량 높음, 복잡성

옵션 3 - vLLM:
  장점: 고성능, 배치 처리 우수
  단점: GPU 필수, 복잡한 설정
```

### 데이터 처리
```yaml
Import 라이브러리:
  - pandas: Excel/CSV 처리
  - openpyxl: Excel 고급 기능
  - sqlalchemy: 로컬 DB 연결

배치 처리:
  - 청크 기반 Iterator 패턴
  - asyncio로 비동기 처리
  - 메모리 모니터링
```

## 설치 패키지 구성안

```
📦 RAGTrace-AirGapped-v1.0.0/
├── 📁 application/
│   ├── ragtrace-docker-image.tar     # Docker 이미지
│   ├── install.sh                    # 자동 설치 스크립트
│   └── requirements-offline.txt      # 오프라인 의존성
├── 📁 models/
│   ├── bge-m3/                      # BGE-M3 임베딩 모델
│   ├── llama3.1-8b/                 # Llama 3.1 8B
│   └── qwen2.5-7b/                  # Qwen 2.5 7B (한국어)
├── 📁 sample-data/
│   ├── evaluation_samples.json      # 샘플 평가 데이터
│   ├── template.xlsx                # Excel 템플릿
│   └── import_guide.md              # 데이터 준비 가이드
├── 📁 docs/
│   ├── Air_Gapped_Setup_Guide.md    # 폐쇄망 설치 가이드
│   ├── Model_Management.md          # 모델 관리 가이드
│   └── Troubleshooting.md           # 문제 해결
└── README_AirGapped.md              # 폐쇄망 전용 README
```

## 최종 권장사항

### 즉시 구현 필요 (Critical)
1. **Ollama 통합** - 가장 실용적인 오프라인 LLM 솔루션
2. **오프라인 모드 설정** - 네트워크 의존성 제거
3. **모델 상태 확인** - 사용 가능한 모델 자동 감지

### 단기 구현 권장 (1개월 내)
1. **모델 패키징 도구** - 쉬운 배포를 위한 필수 도구
2. **Excel/CSV Import** - 실무에서 가장 많이 요청되는 기능
3. **배치 처리** - 대용량 데이터 처리 필수

### 장기 개선 사항
1. **다양한 로컬 LLM 지원** - 선택의 폭 확대
2. **고급 모델 관리** - 버전 관리, 자동 업데이트
3. **전용 UI** - 폐쇄망 환경에 특화된 인터페이스

이러한 개선을 통해 RAGTrace를 완전한 오프라인 RAG 평가 솔루션으로 발전시킬 수 있습니다.