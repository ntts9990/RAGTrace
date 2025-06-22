# RAGTrace 기능 테스트 계획

## 개요
이 문서는 RAGTrace의 주요 기능에 대한 테스트 계획을 제시합니다. 실제 사용자 시나리오를 기반으로 각 기능이 정상적으로 작동하는지 확인하는 것을 목표로 합니다.

## 테스트 범위

### 1. CLI 기능 테스트

#### 1.1 기본 평가 실행
```bash
# 테스트 1: 기본 평가
python cli.py evaluate evaluation_data_small

# 예상 결과:
# - 평가가 성공적으로 완료
# - RAGAS 점수 및 4개 메트릭 표시
# - 에러 없이 종료
```

#### 1.2 LLM/임베딩 모델 선택
```bash
# 테스트 2: Gemini LLM + BGE-M3 임베딩
python cli.py evaluate evaluation_data_small --llm gemini --embedding bge_m3

# 테스트 3: HCX LLM + HCX 임베딩 (API 키 필요)
python cli.py evaluate evaluation_data_small --llm hcx --embedding hcx

# 예상 결과:
# - 선택한 모델이 로그에 표시됨
# - 각 모델별로 평가 완료
# - BGE-M3 사용 시 GPU/CPU 자동 감지
```

#### 1.3 프롬프트 타입 테스트
```bash
# 테스트 4: 한국어 기술 문서 프롬프트
python cli.py evaluate evaluation_data_small --prompt-type nuclear_hydro_tech

# 예상 결과:
# - 선택한 프롬프트 타입 적용
# - 평가 결과에 반영
```

#### 1.4 보조 명령어
```bash
# 테스트 5: 데이터셋 목록
python cli.py list-datasets

# 테스트 6: 프롬프트 목록
python cli.py list-prompts

# 예상 결과:
# - 사용 가능한 데이터셋/프롬프트 목록 표시
# - 에러 없이 정보 출력
```

### 2. Web Dashboard 기능 테스트

#### 2.1 페이지 접근성 테스트
```
테스트 시나리오:
1. streamlit run src/presentation/web/main.py 실행
2. http://localhost:8501 접속
3. 각 페이지 이동 확인:
   - Overview
   - New Evaluation
   - Historical
   - Detailed Analysis
   - Metrics Explanation
   - Performance

예상 결과:
- 모든 페이지가 에러 없이 로드
- 네비게이션이 정상 작동
```

#### 2.2 새 평가 실행 (New Evaluation)
```
테스트 시나리오:
1. New Evaluation 페이지 접속
2. LLM 선택: Gemini
3. 임베딩 선택: BGE-M3
4. 프롬프트 타입: Default
5. 데이터셋: evaluation_data_small
6. "Start Evaluation" 클릭

예상 결과:
- API 키 검증 통과
- 실시간 진행률 표시
- 평가 완료 후 결과 표시
- 레이더 차트와 메트릭 카드 생성
```

#### 2.3 평가 이력 확인 (Historical)
```
테스트 시나리오:
1. 여러 번 평가 실행 후 Historical 페이지 접속
2. 평가 목록 확인
3. 개별 평가 상세보기 (Expander 클릭)
4. 두 평가 선택하여 비교

예상 결과:
- 모든 평가 이력 표시
- 타임스탬프, 모델, 점수 정보 정확
- 비교 차트 정상 생성
```

#### 2.4 상세 분석 (Detailed Analysis)
```
테스트 시나리오:
1. Historical에서 평가 선택
2. "View Detailed Analysis" 클릭
3. QA 쌍별 점수 확인
4. 히트맵, 박스플롯 확인

예상 결과:
- 개별 QA 점수 정확히 표시
- 시각화 차트 정상 렌더링
- 컨텍스트 정보 표시
```

### 3. 데이터 검증 테스트

#### 3.1 입력 데이터 형식 검증
```python
# 테스트: 잘못된 형식의 데이터
{
  "question": "질문만 있음"
  # contexts, answer, ground_truth 누락
}

예상 결과:
- 명확한 에러 메시지 출력
- 누락된 필드 안내
- 프로그램 크래시 없음
```

#### 3.2 API 키 검증
```
테스트 시나리오:
1. 잘못된 API 키로 평가 시도
2. API 키 없이 평가 시도

예상 결과:
- 명확한 에러 메시지
- API 키 설정 가이드 제공
- 웹 UI에서 빨간색 경고 표시
```

### 4. 성능 및 안정성 테스트

#### 4.1 대용량 데이터 처리
```bash
# 100개 이상의 QA 쌍 평가
python cli.py evaluate large_evaluation_data --verbose

예상 결과:
- 메모리 오버플로우 없음
- 진행률 정확히 표시
- 타임아웃 없이 완료
```

#### 4.2 동시 실행 테스트
```
테스트 시나리오:
1. CLI로 평가 실행 중
2. 동시에 웹 대시보드에서 다른 평가 실행

예상 결과:
- 두 평가 모두 정상 완료
- SQLite DB 충돌 없음
- 결과가 올바르게 저장
```

### 5. 오프라인 환경 테스트

#### 5.1 BGE-M3 로컬 임베딩
```bash
# 인터넷 연결 차단 후
python cli.py evaluate evaluation_data_small --llm gemini --embedding bge_m3

예상 결과:
- BGE-M3는 정상 작동 (로컬 모델)
- Gemini LLM만 API 에러
- 부분 실패 시 명확한 안내
```

### 6. Docker 환경 테스트

#### 6.1 Docker 이미지 실행
```bash
docker run -p 8501:8501 -e GEMINI_API_KEY="key" ghcr.io/ntts9990/ragtrace:latest

예상 결과:
- 컨테이너 정상 시작
- 웹 UI 접근 가능
- 평가 기능 정상 작동
```

## 테스트 체크리스트

### 필수 테스트
- [ ] CLI 기본 평가 실행
- [ ] 웹 대시보드 모든 페이지 접근
- [ ] 새 평가 실행 (웹)
- [ ] 평가 이력 확인
- [ ] 각 LLM 모델 테스트 (Gemini, HCX)
- [ ] 각 임베딩 모델 테스트 (Gemini, HCX, BGE-M3)
- [ ] 잘못된 데이터 형식 처리
- [ ] API 키 검증

### 선택적 테스트
- [ ] 대용량 데이터 처리
- [ ] 동시 실행
- [ ] 오프라인 환경
- [ ] Docker 배포
- [ ] 성능 모니터링

## 자동화 테스트 스크립트

```bash
#!/bin/bash
# functional_test.sh

echo "=== RAGTrace 기능 테스트 시작 ==="

# 1. CLI 기본 테스트
echo "1. CLI 기본 평가 테스트..."
python cli.py evaluate evaluation_data_small --output test_result_1.json
if [ $? -eq 0 ]; then
    echo "✅ CLI 기본 평가 성공"
else
    echo "❌ CLI 기본 평가 실패"
fi

# 2. 모델 조합 테스트
echo "2. 다양한 모델 조합 테스트..."
python cli.py evaluate evaluation_data_small --llm gemini --embedding bge_m3 --output test_result_2.json
if [ $? -eq 0 ]; then
    echo "✅ Gemini + BGE-M3 조합 성공"
else
    echo "❌ Gemini + BGE-M3 조합 실패"
fi

# 3. 데이터셋 목록 테스트
echo "3. 보조 명령어 테스트..."
python cli.py list-datasets
python cli.py list-prompts

# 4. 웹 대시보드 실행 테스트
echo "4. 웹 대시보드 실행 테스트..."
timeout 30s streamlit run src/presentation/web/main.py &
STREAMLIT_PID=$!
sleep 10

# 웹 서버 응답 확인
curl -s http://localhost:8501 > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ 웹 대시보드 정상 실행"
else
    echo "❌ 웹 대시보드 실행 실패"
fi

kill $STREAMLIT_PID 2>/dev/null

echo "=== 테스트 완료 ==="
```

## 예상 소요 시간

- 전체 필수 테스트: 약 30분
- 자동화 스크립트: 약 5분
- 수동 웹 UI 테스트: 약 15분
- 선택적 테스트: 추가 20분

## 테스트 결과 보고

각 테스트 완료 후 다음 정보를 기록:
1. 테스트 일시
2. 테스트 환경 (OS, Python 버전, 의존성 버전)
3. 성공/실패 여부
4. 실패 시 에러 메시지
5. 성능 지표 (실행 시간, 메모리 사용량)
6. 개선 사항 제안