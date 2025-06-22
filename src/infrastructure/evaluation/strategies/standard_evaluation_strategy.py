"""
Standard Evaluation Strategy

기본 RAGAS 메트릭을 사용한 표준 평가 전략입니다.
"""

from typing import Any, List
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.run_config import RunConfig

from .base_strategy import EvaluationStrategy


class StandardEvaluationStrategy(EvaluationStrategy):
    """기본 RAGAS 메트릭을 사용한 표준 평가 전략"""
    
    def __init__(self, llm, embeddings):
        super().__init__(llm, embeddings)
        
        # HCX 사용 시 순차 처리로 API 한도 방지
        max_workers = 1
        timeout = 600  # HCX 사용 시 타임아웃 증가
        
        # LLM이 HCX가 아닌 경우 더 많은 워커 사용 가능
        if hasattr(llm, 'model') and 'HCX' not in str(llm.model):
            max_workers = 4
            timeout = 300
        
        self.run_config = RunConfig(
            timeout=timeout,
            max_retries=5,  # 재시도 횟수 증가
            max_workers=max_workers,
            max_wait=120,   # 대기 시간 증가
            log_tenacity=True
        )
        
        # 설정 확인 로그
        print(f"⚙️ RAGAS 설정 적용됨:")
        print(f"   - LLM 모델: {getattr(llm, 'model', 'Unknown')}")
        print(f"   - 워커 수: {max_workers}")
        print(f"   - 타임아웃: {timeout}초")
        print(f"   - 재시도: 5회")
    
    def get_metrics(self) -> List[Any]:
        """기본 RAGAS 메트릭 반환"""
        return [
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        ]
    
    def run_evaluation(self, dataset: Dataset) -> Any:
        """기본 RAGAS 평가 실행"""
        print("🚀 표준 RAGAS 평가 실행 중...")
        print(f"📊 데이터셋 크기: {len(dataset)}개 QA 쌍")
        print(f"🤖 LLM 모델: {self.llm.model}")
        
        # 임베딩 모델 정보 출력
        embedding_info = f"🌐 임베딩 모델: {type(self.embeddings).__name__}"
        if hasattr(self.embeddings, 'model_name'):
            embedding_info += f" ({self.embeddings.model_name})"
        elif hasattr(self.embeddings, 'device'):
            embedding_info += f" (디바이스: {self.embeddings.device})"
        print(embedding_info)
        
        # HCX 사용 시 추가 환경 변수 설정으로 강제 순차 처리
        import os
        original_env = {}
        if 'HCX' in str(self.llm.model):
            print("🔧 HCX 모델 감지 - 순차 처리 강제 적용")
            # 스레드 풀 크기 제한
            original_env['RAGAS_MAX_WORKERS'] = os.environ.get('RAGAS_MAX_WORKERS', '')
            original_env['NUMEXPR_MAX_THREADS'] = os.environ.get('NUMEXPR_MAX_THREADS', '')
            os.environ['RAGAS_MAX_WORKERS'] = '1'
            os.environ['NUMEXPR_MAX_THREADS'] = '1'
        
        try:
            # HCX 사용 시 파싱 오류 허용도 증가
            run_config = self.run_config
            if 'HCX' in str(self.llm.model):
                from ragas.run_config import RunConfig
                run_config = RunConfig(
                    timeout=self.run_config.timeout,
                    max_retries=self.run_config.max_retries,
                    max_workers=1,  # 강제로 1로 설정
                    max_wait=self.run_config.max_wait,
                    log_tenacity=True,
                    exception_types=(Exception,),  # 더 넓은 예외 허용
                )
                print(f"🔧 HCX 전용 RunConfig 적용: 워커={run_config.max_workers}")
            
            result = evaluate(
                dataset=dataset,
                metrics=self.get_metrics(),
                llm=self.llm,
                embeddings=self.embeddings,
                run_config=run_config,
                raise_exceptions=False,
            )
        finally:
            # 환경 변수 복원
            for key, value in original_env.items():
                if value:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]
        
        return result
    
    def get_strategy_name(self) -> str:
        """전략 이름 반환"""
        return "표준 RAGAS 평가 (영어)"