"""
평가 체크포인트 서비스

대량 데이터셋 평가 시 중간 결과를 저장하고 복구하는 기능을 제공합니다.
"""

import json
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import uuid


class EvaluationCheckpoint:
    """평가 체크포인트 관리 클래스"""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.current_session_id = None
        self.current_checkpoint_file = None
        
    def start_session(self, dataset_name: str, dataset_size: int, config: Dict[str, Any]) -> str:
        """새로운 평가 세션 시작"""
        session_id = f"{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.current_session_id = session_id
        
        # 체크포인트 파일 경로
        self.current_checkpoint_file = self.checkpoint_dir / f"{session_id}.checkpoint"
        
        # 초기 체크포인트 생성
        initial_checkpoint = {
            'session_id': session_id,
            'dataset_name': dataset_name,
            'dataset_size': dataset_size,
            'config': config,
            'start_time': datetime.now().isoformat(),
            'status': 'started',
            'completed_items': 0,
            'individual_results': [],
            'partial_metrics': {},
            'error_count': 0,
            'last_update': datetime.now().isoformat()
        }
        
        self.save_checkpoint(initial_checkpoint)
        print(f"📋 평가 세션 시작: {session_id}")
        print(f"💾 체크포인트: {self.current_checkpoint_file}")
        
        return session_id
    
    def save_checkpoint(self, data: Dict[str, Any]):
        """체크포인트 저장"""
        data['last_update'] = datetime.now().isoformat()
        
        # JSON으로 저장 (가독성)
        with open(self.current_checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 백업용 pickle 저장 (안정성)
        backup_file = self.current_checkpoint_file.with_suffix('.backup')
        with open(backup_file, 'wb') as f:
            pickle.dump(data, f)
    
    def load_checkpoint(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """체크포인트 로드"""
        if session_id:
            checkpoint_file = self.checkpoint_dir / f"{session_id}.checkpoint"
        else:
            checkpoint_file = self.current_checkpoint_file
        
        if not checkpoint_file or not checkpoint_file.exists():
            return None
        
        try:
            # JSON 로드 시도
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as json_error:
            print(f"⚠️ JSON 로드 실패, 백업 시도: {json_error}")
            try:
                # 백업 pickle 로드 시도
                backup_file = checkpoint_file.with_suffix('.backup')
                with open(backup_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as pickle_error:
                print(f"❌ 백업 로드도 실패: {pickle_error}")
                return None
    
    def update_progress(self, completed_items: int, new_results: List[Dict[str, Any]], 
                       partial_metrics: Dict[str, float] = None, error_count: int = 0):
        """진행 상황 업데이트"""
        if not self.current_checkpoint_file:
            return
        
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return
        
        checkpoint['completed_items'] = completed_items
        checkpoint['individual_results'].extend(new_results)
        
        if partial_metrics:
            checkpoint['partial_metrics'] = partial_metrics
        
        checkpoint['error_count'] = error_count
        checkpoint['progress_percentage'] = (completed_items / checkpoint['dataset_size']) * 100
        
        # 예상 완료 시간 계산
        if completed_items > 0:
            start_time = datetime.fromisoformat(checkpoint['start_time'])
            elapsed = (datetime.now() - start_time).total_seconds()
            estimated_total = elapsed * (checkpoint['dataset_size'] / completed_items)
            remaining = estimated_total - elapsed
            checkpoint['estimated_completion'] = (datetime.now().timestamp() + remaining)
        
        self.save_checkpoint(checkpoint)
        
        # 진행 상황 출력
        progress = checkpoint['progress_percentage']
        print(f"💾 체크포인트 업데이트: {completed_items}/{checkpoint['dataset_size']} ({progress:.1f}%)")
    
    def complete_session(self, final_result: Dict[str, Any]):
        """세션 완료"""
        if not self.current_checkpoint_file:
            return
        
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return
        
        checkpoint['status'] = 'completed'
        checkpoint['completion_time'] = datetime.now().isoformat()
        checkpoint['final_result'] = final_result
        
        # 완료된 체크포인트를 결과 파일로 저장
        result_file = self.current_checkpoint_file.with_suffix('.result.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        self.save_checkpoint(checkpoint)
        print(f"✅ 평가 세션 완료: {self.current_session_id}")
        print(f"📄 최종 결과: {result_file}")
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """저장된 세션 목록"""
        sessions = []
        
        for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint"):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                sessions.append({
                    'session_id': data.get('session_id'),
                    'dataset_name': data.get('dataset_name'),
                    'dataset_size': data.get('dataset_size'),
                    'status': data.get('status'),
                    'progress': data.get('progress_percentage', 0),
                    'completed_items': data.get('completed_items', 0),
                    'start_time': data.get('start_time'),
                    'last_update': data.get('last_update'),
                    'checkpoint_file': str(checkpoint_file)
                })
            except Exception as e:
                print(f"⚠️ 세션 로드 실패 {checkpoint_file}: {e}")
        
        return sorted(sessions, key=lambda x: x.get('start_time', ''), reverse=True)
    
    def resume_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 재개"""
        checkpoint = self.load_checkpoint(session_id)
        if not checkpoint:
            print(f"❌ 세션을 찾을 수 없습니다: {session_id}")
            return None
        
        if checkpoint.get('status') == 'completed':
            print(f"ℹ️ 이미 완료된 세션입니다: {session_id}")
            return checkpoint
        
        self.current_session_id = session_id
        self.current_checkpoint_file = self.checkpoint_dir / f"{session_id}.checkpoint"
        
        print(f"🔄 세션 재개: {session_id}")
        print(f"📊 진행 상황: {checkpoint.get('completed_items', 0)}/{checkpoint.get('dataset_size', 0)}")
        
        return checkpoint
    
    def cleanup_old_sessions(self, days: int = 7):
        """오래된 세션 정리"""
        cutoff_time = time.time() - (days * 24 * 3600)
        cleaned = 0
        
        for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint"):
            if checkpoint_file.stat().st_mtime < cutoff_time:
                try:
                    # 백업 파일도 함께 삭제
                    backup_file = checkpoint_file.with_suffix('.backup')
                    if backup_file.exists():
                        backup_file.unlink()
                    
                    checkpoint_file.unlink()
                    cleaned += 1
                except Exception as e:
                    print(f"⚠️ 파일 삭제 실패 {checkpoint_file}: {e}")
        
        if cleaned > 0:
            print(f"🧹 오래된 체크포인트 {cleaned}개 정리 완료")


class BatchEvaluationManager:
    """배치 평가 관리자"""
    
    def __init__(self, checkpoint_manager: EvaluationCheckpoint, batch_size: int = 5):
        self.checkpoint = checkpoint_manager
        self.batch_size = batch_size
        
    def evaluate_with_checkpoints(self, dataset, evaluation_func, config: Dict[str, Any]) -> Dict[str, Any]:
        """체크포인트와 함께 배치 평가 실행"""
        dataset_name = config.get('dataset_name', 'unknown')
        dataset_size = len(dataset)
        
        # 세션 시작
        session_id = self.checkpoint.start_session(dataset_name, dataset_size, config)
        
        all_results = []
        completed_count = 0
        error_count = 0
        
        # 메모리 사용량 모니터링
        import psutil
        import gc
        
        try:
            # 배치별로 처리
            for batch_start in range(0, dataset_size, self.batch_size):
                batch_end = min(batch_start + self.batch_size, dataset_size)
                batch_data = dataset.select(range(batch_start, batch_end))
                
                print(f"🔄 배치 처리: {batch_start+1}-{batch_end}/{dataset_size}")
                
                # 메모리 사용량 체크
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 85:
                    print(f"⚠️ 메모리 사용량 높음 ({memory_percent:.1f}%) - 가비지 컬렉션 수행")
                    gc.collect()
                
                try:
                    # 배치 평가 실행
                    batch_result = evaluation_func(batch_data)
                    
                    # 개별 결과 추출
                    if hasattr(batch_result, 'to_pandas'):
                        df = batch_result.to_pandas()
                        batch_individual = df.to_dict('records')
                    elif isinstance(batch_result, dict) and 'individual_scores' in batch_result:
                        batch_individual = batch_result['individual_scores']
                    else:
                        # 폴백: 배치 크기만큼 평균 점수로 생성
                        avg_scores = self._extract_average_scores(batch_result)
                        batch_individual = [avg_scores] * len(batch_data)
                    
                    all_results.extend(batch_individual)
                    completed_count += len(batch_data)
                    
                    # 중간 메트릭 계산 (메모리 효율적으로)
                    partial_metrics = self._calculate_partial_metrics(all_results[-50:])  # 최근 50개만 사용
                    
                    # 체크포인트 업데이트
                    self.checkpoint.update_progress(
                        completed_count, 
                        batch_individual, 
                        partial_metrics, 
                        error_count
                    )
                    
                    # 배치 완료 대기 (API 제한 고려) - 큰 배치는 더 오래 대기
                    wait_time = min(2, self.batch_size * 0.2)
                    time.sleep(wait_time)
                    
                    # 메모리 정리
                    del batch_result, batch_individual
                    
                except Exception as batch_error:
                    error_count += 1
                    print(f"❌ 배치 {batch_start+1}-{batch_end} 처리 실패: {batch_error}")
                    
                    # 실패한 항목들을 0점으로 처리
                    failed_items = [self._create_zero_scores()] * len(batch_data)
                    all_results.extend(failed_items)
                    completed_count += len(batch_data)
                    
                    # 체크포인트 업데이트
                    self.checkpoint.update_progress(
                        completed_count, 
                        failed_items, 
                        error_count=error_count
                    )
                    
                    # 에러 발생 시 더 오래 대기
                    time.sleep(3)
                
                # 정기적인 메모리 정리
                if batch_start % (self.batch_size * 5) == 0:
                    gc.collect()
            
            # 최종 결과 계산
            final_result = self._compile_final_result(all_results, config, error_count)
            
            # 세션 완료
            self.checkpoint.complete_session(final_result)
            
            return final_result
            
        except Exception as e:
            print(f"❌ 평가 중 심각한 오류: {e}")
            # 부분 결과라도 저장
            partial_result = self._compile_final_result(all_results, config, error_count, partial=True)
            self.checkpoint.save_checkpoint({
                **self.checkpoint.load_checkpoint(),
                'status': 'failed',
                'error': str(e),
                'partial_result': partial_result
            })
            raise
    
    def _extract_average_scores(self, result) -> Dict[str, float]:
        """결과에서 평균 점수 추출"""
        scores = {}
        
        if isinstance(result, dict):
            for key, value in result.items():
                if key not in ['individual_scores', 'metadata'] and isinstance(value, (int, float)):
                    scores[key] = float(value)
        
        # 기본 메트릭이 없으면 0으로 설정
        default_metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'answer_correctness']
        for metric in default_metrics:
            if metric not in scores:
                scores[metric] = 0.0
        
        return scores
    
    def _create_zero_scores(self) -> Dict[str, float]:
        """0점 결과 생성"""
        return {
            'faithfulness': 0.0,
            'answer_relevancy': 0.0,
            'context_recall': 0.0,
            'context_precision': 0.0,
            'answer_correctness': 0.0
        }
    
    def _calculate_partial_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """부분 결과에서 메트릭 계산"""
        if not results:
            return {}
        
        metrics = {}
        metric_names = results[0].keys()
        
        for metric in metric_names:
            values = [r.get(metric, 0) for r in results if r.get(metric) is not None]
            if values:
                metrics[metric] = sum(values) / len(values)
            else:
                metrics[metric] = 0.0
        
        # RAGAS 종합 점수 계산
        core_metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
        if 'answer_correctness' in metrics:
            core_metrics.append('answer_correctness')
        
        core_values = [metrics.get(m, 0) for m in core_metrics if metrics.get(m, 0) > 0]
        if core_values:
            metrics['ragas_score'] = sum(core_values) / len(core_values)
        else:
            metrics['ragas_score'] = 0.0
        
        return metrics
    
    def _compile_final_result(self, individual_results: List[Dict[str, Any]], 
                            config: Dict[str, Any], error_count: int, partial: bool = False) -> Dict[str, Any]:
        """최종 결과 컴파일"""
        import uuid
        from datetime import datetime
        
        # 전체 메트릭 계산
        final_metrics = self._calculate_partial_metrics(individual_results)
        
        # 메타데이터 생성
        metadata = {
            'evaluation_id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now().isoformat(),
            'model': config.get('llm_type', 'unknown'),
            'embedding_model': config.get('embedding_type', 'unknown'),
            'prompt_type': str(config.get('prompt_type', 'unknown')),
            'dataset_size': len(individual_results),
            'dataset_name': config.get('dataset_name', 'unknown'),
            'error_count': error_count,
            'success_rate': ((len(individual_results) - error_count) / len(individual_results)) * 100 if individual_results else 0,
            'batch_size': self.batch_size,
            'partial_result': partial
        }
        
        # 최종 결과 구성
        result = {
            **final_metrics,
            'individual_scores': individual_results,
            'metadata': metadata
        }
        
        return result


def resume_evaluation_from_checkpoint(session_id: str) -> Optional[Dict[str, Any]]:
    """체크포인트에서 평가 재개"""
    checkpoint_manager = EvaluationCheckpoint()
    return checkpoint_manager.resume_session(session_id)