# 📊 Excel/CSV 데이터 Import 가이드

RAGTrace는 Excel과 CSV 파일에서 평가 데이터를 직접 import할 수 있는 강력한 기능을 제공합니다. 이 가이드는 데이터 준비부터 평가 실행까지의 전 과정을 상세히 설명합니다.

## 🎯 빠른 시작

```bash
# 1. Excel/CSV 파일을 JSON으로 변환 (검증 포함)
uv run python cli.py import-data your_data.xlsx --validate

# 2. 변환된 데이터로 평가 실행
uv run python cli.py evaluate your_data --llm gemini --embedding bge_m3
```

## 📋 필수 데이터 구조

### 필수 컬럼 (4개)

Excel 또는 CSV 파일에는 **반드시** 다음 4개 컬럼이 포함되어야 합니다:

| 컬럼명 | 타입 | 설명 | 필수 여부 |
|--------|------|------|-----------|
| `question` | 문자열 | 평가할 질문 | ✅ 필수 |
| `contexts` | 문자열/배열 | 참고 문맥들 | ✅ 필수 |
| `answer` | 문자열 | 시스템이 생성한 답변 | ✅ 필수 |
| `ground_truth` | 문자열 | 정답 기준 | ✅ 필수 |

### 컬럼명 규칙
- 컬럼명은 **대소문자를 구분**합니다
- 공백이나 특수문자는 사용하지 마세요
- 정확히 위 이름을 사용해야 합니다

## 🔍 contexts 필드 작성 방법

`contexts` 필드는 여러 형식을 지원하여 기존 데이터를 쉽게 변환할 수 있습니다.

### 1. JSON 배열 형식 (권장)

```json
["원자로는 핵분열을 통해 열을 생성하는 핵심 장치이다", "증기발생기는 1차 계통의 열을 2차 계통으로 전달한다", "터빈발전기는 증기의 운동에너지를 전기에너지로 변환한다"]
```

**장점:**
- 가장 명확하고 구조화된 형식
- JSON 파싱 오류 가능성 최소화
- 개별 문맥 구분이 정확함

### 2. 세미콜론(;) 구분자

```
원자로는 핵분열을 통해 열을 생성하는 핵심 장치이다;증기발생기는 1차 계통의 열을 2차 계통으로 전달한다;터빈발전기는 증기의 운동에너지를 전기에너지로 변환한다
```

**사용 케이스:**
- 기존 시스템에서 세미콜론으로 구분된 데이터
- Excel에서 간단하게 입력할 때

### 3. 파이프(|) 구분자

```
원자로는 핵분열을 통해 열을 생성하는 핵심 장치이다|증기발생기는 1차 계통의 열을 2차 계통으로 전달한다|터빈발전기는 증기의 운동에너지를 전기에너지로 변환한다
```

**사용 케이스:**
- 파이프 구분자를 사용하는 기존 시스템
- 텍스트에 세미콜론이 포함된 경우

### 4. 단일 문맥

```
원자력 발전소는 핵분열 에너지를 이용하여 전기를 생산하는 시설이다
```

**사용 케이스:**
- 하나의 긴 문맥만 있는 경우
- 단일 문서 기반 QA 시스템

## 📝 실제 데이터 예시

### Excel 파일 예시

| question | contexts | answer | ground_truth |
|----------|----------|--------|--------------|
| 원자력 발전소의 주요 구성요소는 무엇인가요? | ["원자로는 핵분열을 통해 열을 생성하는 핵심 장치이다", "증기발생기는 1차 계통의 열을 2차 계통으로 전달한다", "터빈발전기는 증기의 운동에너지를 전기에너지로 변환한다"] | 원자력 발전소의 주요 구성요소는 원자로, 증기발생기, 터빈발전기입니다. | 원자로, 증기발생기, 터빈발전기 |
| 수력발전의 원리는 무엇인가요? | 물의 위치에너지를 터빈의 운동에너지로 변환한다;댐이나 저수지에서 물을 높은 곳에 저장한다;물이 떨어지면서 터빈을 회전시켜 발전기를 돌린다 | 수력발전은 높은 곳에 저장된 물의 위치에너지를 이용하여 전기를 생산하는 방식입니다. | 물의 위치에너지를 이용한 발전 |

### CSV 파일 예시

```csv
question,contexts,answer,ground_truth
"원자력 발전소의 주요 구성요소는 무엇인가요?","[""원자로는 핵분열을 통해 열을 생성하는 핵심 장치이다"", ""증기발생기는 1차 계통의 열을 2차 계통으로 전달한다""]","원자력 발전소의 주요 구성요소는 원자로, 증기발생기입니다.","원자로, 증기발생기"
"수력발전의 원리는?","물의 위치에너지 활용;댐에서 물 저장;터빈 회전으로 발전","수력발전은 물의 위치에너지를 활용합니다.","위치에너지 활용"
```

## 🚀 CLI 사용법

### 기본 변환

```bash
# Excel 파일 변환
uv run python cli.py import-data evaluation_data.xlsx

# CSV 파일 변환
uv run python cli.py import-data evaluation_data.csv

# 출력 파일 지정
uv run python cli.py import-data evaluation_data.xlsx --output converted_data.json
```

### 검증 옵션

```bash
# 데이터 검증 수행 (권장)
uv run python cli.py import-data evaluation_data.xlsx --validate

# 검증 결과 예시:
# 📊 데이터 검증 결과:
#    전체: 10개
#    유효: 9개
#    성공률: 90.0%
#    ❌ 오류: 1개
#    ⚠️ 경고: 3개
```

### 배치 처리

```bash
# 대용량 데이터 배치 처리 (기본값: 50개씩)
uv run python cli.py import-data large_dataset.xlsx --batch-size 100

# 배치 처리 정보 출력 예시:
# 🔄 배치 처리 정보:
#    배치 크기: 100
#    예상 배치 수: 5
#    대용량 처리 시 배치 처리를 권장합니다.
```

### 완전한 워크플로우

```bash
# 1. 데이터 변환 및 검증
uv run python cli.py import-data my_evaluation_data.xlsx --validate --output my_data.json

# 2. 변환된 데이터를 data/ 디렉토리로 이동
mv my_data.json data/

# 3. 평가 실행
uv run python cli.py evaluate my_data --llm gemini --embedding bge_m3 --verbose

# 4. 결과 저장
uv run python cli.py evaluate my_data --llm gemini --embedding bge_m3 --output results.json
```

## 🔧 고급 기능

### 인코딩 지원

시스템은 다양한 인코딩을 자동으로 감지합니다:

- **UTF-8** (기본값, 권장)
- **CP949** (한국어 Windows)
- **EUC-KR** (한국어 레거시)
- **Latin-1** (서유럽)

### 오류 처리

Import 과정에서 발생할 수 있는 오류들:

| 오류 유형 | 원인 | 해결 방법 |
|----------|------|-----------|
| 필수 컬럼 누락 | question, contexts, answer, ground_truth 중 누락 | 모든 필수 컬럼 추가 |
| 파일 형식 오류 | .xlsx, .xls, .csv 이외의 형식 | 지원되는 형식으로 변환 |
| 인코딩 오류 | 지원되지 않는 문자 인코딩 | UTF-8로 저장 후 재시도 |
| JSON 파싱 오류 | contexts의 잘못된 JSON 형식 | JSON 형식 확인 또는 구분자 사용 |

### 데이터 검증 규칙

검증 과정에서 확인되는 항목들:

**오류 (평가 불가):**
- 빈 질문, 답변, 정답
- 빈 contexts 배열
- 필수 컬럼 누락

**경고 (평가 가능하지만 품질 개선 권장):**
- 너무 짧은 질문 (5자 미만)
- 너무 짧은 답변 (3자 미만)
- 너무 많은 contexts (10개 초과)
- 질문과 답변이 동일한 경우

## 📊 배치 처리 시스템

대용량 데이터 처리를 위한 고급 기능입니다.

### 배치 처리의 장점

1. **메모리 효율성**: 전체 데이터를 메모리에 로드하지 않고 청크 단위로 처리
2. **장애 복구**: 개별 배치 실패 시에도 다른 배치는 계속 처리
3. **진행 추적**: 실시간 진행률과 예상 완료 시간 제공
4. **중간 저장**: 처리 중간에 결과를 저장하여 안전성 확보

### 배치 처리 설정

```bash
# 배치 크기 조정 (기본값: 50)
uv run python cli.py import-data large_data.csv --batch-size 200

# 대용량 파일의 경우 자동으로 배치 처리 권장 메시지 표시
# 예상 배치 수와 처리 시간 정보 제공
```

### 성능 가이드라인

| 데이터 크기 | 권장 배치 크기 | 예상 처리 시간 |
|-------------|----------------|----------------|
| ~100개 | 50 (기본값) | 1-2분 |
| 100-1000개 | 100-200 | 5-10분 |
| 1000-10000개 | 200-500 | 30-60분 |
| 10000개+ | 500-1000 | 1시간+ |

## 🛠️ 문제 해결

### 자주 발생하는 문제들

**1. "필수 컬럼이 누락되었습니다" 오류**
```bash
# 해결: 정확한 컬럼명 확인
# 올바른 컬럼명: question, contexts, answer, ground_truth
# 대소문자 구분 주의!
```

**2. "contexts JSON 파싱 오류"**
```bash
# 해결: JSON 형식 확인 또는 구분자 사용
# 올바른 JSON: ["context 1", "context 2"]
# 또는 구분자 사용: context 1;context 2
```

**3. "파일을 읽을 수 없습니다" 오류**
```bash
# 해결: 파일 경로와 권한 확인
ls -la your_file.xlsx  # 파일 존재 및 권한 확인
```

**4. 인코딩 문제**
```bash
# 해결: UTF-8로 다시 저장
# Excel: 파일 > 다른 이름으로 저장 > CSV UTF-8
```

### 디버깅 팁

```bash
# 상세한 오류 정보 확인
uv run python cli.py import-data problematic_data.xlsx --validate

# 작은 샘플 데이터로 테스트
head -n 5 large_data.csv > test_sample.csv
uv run python cli.py import-data test_sample.csv --validate
```

## 📚 추가 리소스

### 관련 문서
- [CLAUDE.md](../CLAUDE.md): 전체 시스템 개요 및 개발자 가이드
- [RAGTRACE_METRICS.md](RAGTRACE_METRICS.md): 평가 메트릭 상세 설명
- [Docker_Deployment_Guide.md](Docker_Deployment_Guide.md): Docker 배포 가이드

### 예제 파일
- `data/evaluation_data.json`: 표준 JSON 형식 예제
- `data/evaluation_data_variant1.json`: 다양한 데이터 형식 예제

### 지원 및 문의
- GitHub Issues: 버그 리포트 및 기능 요청
- 개발자 문서: 시스템 확장 및 커스터마이징 가이드

---

이 가이드를 통해 Excel/CSV 데이터를 RAGTrace에서 효과적으로 활용하실 수 있습니다. 추가 질문이나 지원이 필요하시면 언제든 문의해 주세요! 🚀