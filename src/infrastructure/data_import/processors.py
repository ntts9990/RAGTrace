"""
Batch Data Processors

대용량 데이터를 효율적으로 처리하기 위한 배치 처리 시스템.
메모리 효율성과 장애 복구 능력을 제공합니다.
"""

from typing import List, Iterator, Callable, Optional, Dict, Any
from dataclasses import dataclass, field
import asyncio
import time
from pathlib import Path
import json
import uuid
from datetime import datetime

from ...domain.entities.evaluation_data import EvaluationData
from ...domain.entities.evaluation_result import EvaluationResult


@dataclass
class BatchProgress:
    """배치 처리 진행 상황"""
    batch_id: str
    current_batch: int
    total_batches: int
    processed_items: int
    total_items: int
    start_time: datetime
    current_time: datetime = field(default_factory=datetime.now)
    errors: List[str] = field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        """진행률 (0.0 ~ 1.0)"""
        if self.total_items == 0:
            return 0.0
        return self.processed_items / self.total_items
    
    @property
    def elapsed_time(self) -> float:
        """경과 시간 (초)"""
        return (self.current_time - self.start_time).total_seconds()
    
    @property
    def items_per_second(self) -> float:
        """초당 처리 항목 수"""
        if self.elapsed_time == 0:
            return 0.0
        return self.processed_items / self.elapsed_time
    
    @property
    def estimated_remaining_time(self) -> float:
        """예상 남은 시간 (초)"""
        if self.items_per_second == 0:
            return 0.0
        remaining_items = self.total_items - self.processed_items
        return remaining_items / self.items_per_second


@dataclass 
class BatchConfig:
    """배치 처리 설정"""
    batch_size: int = 50
    max_retries: int = 3
    retry_delay: float = 1.0
    save_intermediate_results: bool = True
    intermediate_save_path: Optional[Path] = None
    enable_progress_callback: bool = True
    max_concurrent_batches: int = 1  # 동시 처리할 배치 수


class BatchDataProcessor:
    """배치 데이터 처리기"""
    
    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()
        self.current_progress: Optional[BatchProgress] = None
        self.progress_callbacks: List[Callable[[BatchProgress], None]] = []
    
    def add_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """진행 상황 콜백 함수 추가"""
        self.progress_callbacks.append(callback)
    
    def create_batches(self, data_list: List[EvaluationData]) -> Iterator[List[EvaluationData]]:
        """데이터를 배치 단위로 분할"""
        batch_size = self.config.batch_size
        for i in range(0, len(data_list), batch_size):
            yield data_list[i:i + batch_size]
    
    async def process_batches_async(self,
                                   data_list: List[EvaluationData],
                                   processor_func: Callable[[List[EvaluationData]], List[EvaluationResult]]) -> List[EvaluationResult]:
        """비동기 배치 처리"""
        batch_id = str(uuid.uuid4())[:8]
        batches = list(self.create_batches(data_list))
        
        # 진행 상황 초기화
        self.current_progress = BatchProgress(
            batch_id=batch_id,
            current_batch=0,
            total_batches=len(batches),
            processed_items=0,
            total_items=len(data_list),
            start_time=datetime.now()
        )
        
        all_results = []
        
        # 배치 처리 (현재는 순차 처리, 추후 병렬 처리 확장 가능)
        for batch_idx, batch_data in enumerate(batches):
            try:
                # 배치 처리 시도
                batch_results = await self._process_single_batch_with_retry(
                    batch_data, processor_func, batch_idx + 1
                )
                
                all_results.extend(batch_results)
                
                # 진행 상황 업데이트
                self.current_progress.current_batch = batch_idx + 1
                self.current_progress.processed_items += len(batch_data)
                self.current_progress.current_time = datetime.now()
                
                # 중간 결과 저장
                if self.config.save_intermediate_results:
                    await self._save_intermediate_results(all_results, batch_idx + 1)
                
                # 진행 상황 콜백 호출
                if self.config.enable_progress_callback:
                    for callback in self.progress_callbacks:
                        callback(self.current_progress)
                
            except Exception as e:
                error_msg = f"배치 {batch_idx + 1} 처리 실패: {str(e)}"
                self.current_progress.errors.append(error_msg)
                print(f"❌ {error_msg}")
                # 오류 발생해도 다음 배치 계속 처리
                continue
        
        return all_results
    
    def process_batches_sync(self,
                            data_list: List[EvaluationData],
                            processor_func: Callable[[List[EvaluationData]], List[EvaluationResult]]) -> List[EvaluationResult]:
        """동기 배치 처리 (기존 시스템과 호환)"""
        return asyncio.run(self.process_batches_async(data_list, processor_func))
    
    async def _process_single_batch_with_retry(self,
                                              batch_data: List[EvaluationData],
                                              processor_func: Callable[[List[EvaluationData]], List[EvaluationResult]],
                                              batch_number: int) -> List[EvaluationResult]:
        """재시도 로직이 포함된 단일 배치 처리"""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                print(f"🔄 배치 {batch_number} 처리 중... (시도 {attempt + 1}/{self.config.max_retries})")
                
                # 실제 처리 함수 호출
                if asyncio.iscoroutinefunction(processor_func):
                    results = await processor_func(batch_data)
                else:
                    results = processor_func(batch_data)
                
                print(f"✅ 배치 {batch_number} 완료 ({len(results)}개 결과)")
                return results
                
            except Exception as e:
                last_exception = e
                print(f"⚠️ 배치 {batch_number} 시도 {attempt + 1} 실패: {str(e)}")
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
        
        # 모든 재시도 실패
        raise Exception(f"배치 {batch_number} 최대 재시도 횟수 초과: {str(last_exception)}")
    
    async def _save_intermediate_results(self, results: List[EvaluationResult], batch_number: int):
        """중간 결과 저장"""
        if not self.config.intermediate_save_path:
            return
        
        try:
            save_path = self.config.intermediate_save_path
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 배치별 결과 저장
            batch_file = save_path / f"batch_{batch_number:04d}_results.json"
            
            # EvaluationResult를 JSON 직렬화 가능한 형태로 변환
            serializable_results = []
            for result in results:
                serializable_results.append({
                    'evaluation_id': result.evaluation_id,
                    'dataset_name': result.dataset_name,
                    'model_name': result.model_name,
                    'embedding_model_name': getattr(result, 'embedding_model_name', 'unknown'),
                    'prompt_type': getattr(result, 'prompt_type', 'default'),
                    'metrics': result.metrics.to_dict() if hasattr(result.metrics, 'to_dict') else {},
                    'individual_scores': result.individual_scores,
                    'evaluation_time': result.evaluation_time.isoformat() if result.evaluation_time else None,
                    'data_count': result.data_count
                })
            
            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ 중간 결과 저장 실패: {str(e)}")
    
    def get_progress_summary(self) -> Optional[str]:
        """현재 진행 상황 요약 반환"""
        if not self.current_progress:
            return None
        
        progress = self.current_progress
        
        summary_lines = [
            f"🔄 배치 처리 진행 상황 (ID: {progress.batch_id})",
            f"   진행률: {progress.progress_percentage:.1%} ({progress.processed_items}/{progress.total_items})",
            f"   배치: {progress.current_batch}/{progress.total_batches}",
            f"   경과 시간: {progress.elapsed_time:.1f}초",
            f"   처리 속도: {progress.items_per_second:.1f} 항목/초",
        ]
        
        if progress.estimated_remaining_time > 0:
            summary_lines.append(f"   예상 남은 시간: {progress.estimated_remaining_time:.1f}초")
        
        if progress.errors:
            summary_lines.append(f"   ❌ 오류: {len(progress.errors)}개")
        
        return "\n".join(summary_lines)


class ProgressDisplayCallback:
    """콘솔용 진행 상황 표시 콜백"""
    
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self.last_update_time = 0.0
    
    def __call__(self, progress: BatchProgress):
        """진행 상황 콘솔 출력"""
        current_time = time.time()
        
        # 업데이트 간격 체크
        if current_time - self.last_update_time < self.update_interval:
            return
        
        self.last_update_time = current_time
        
        # 진행률 바 생성
        bar_length = 30
        filled_length = int(bar_length * progress.progress_percentage)
        bar = '█' * filled_length + '▒' * (bar_length - filled_length)
        
        print(f"\r🔄 [{bar}] {progress.progress_percentage:.1%} "
              f"({progress.processed_items}/{progress.total_items}) "
              f"- {progress.items_per_second:.1f} 항목/초 "
              f"- 남은 시간: {progress.estimated_remaining_time:.0f}초", end='', flush=True)
        
        # 배치 완료 시 새 줄
        if progress.current_batch == progress.total_batches:
            print()  # 새 줄