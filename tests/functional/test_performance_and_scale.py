"""
성능 및 대용량 데이터 테스트

시스템의 성능과 확장성을 테스트합니다.
"""

import pytest
import tempfile
import json
import csv
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# 시스템 패스 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import cli
from src.infrastructure.data_import.processors import BatchDataProcessor, BatchConfig
from src.infrastructure.data_import.validators import ImportDataValidator
from src.domain.entities.evaluation_data import EvaluationData


class TestPerformanceAndScale:
    """성능 및 확장성 테스트"""
    
    @pytest.fixture
    def runner(self):
        """CLI 테스트 러너"""
        return CliRunner()
    
    @pytest.fixture
    def large_csv_file(self):
        """대용량 CSV 파일 생성 (100개 항목)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['question', 'contexts', 'answer', 'ground_truth'])
            
            for i in range(100):
                writer.writerow([
                    f'테스트 질문 {i+1}',
                    f'테스트 컨텍스트 {i+1}-1;테스트 컨텍스트 {i+1}-2',
                    f'테스트 답변 {i+1}',
                    f'테스트 정답 {i+1}'
                ])
            
            yield f.name
        
        os.unlink(f.name)
    
    @pytest.fixture
    def medium_csv_file(self):
        """중간 크기 CSV 파일 생성 (10개 항목)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['question', 'contexts', 'answer', 'ground_truth'])
            
            for i in range(10):
                writer.writerow([
                    f'질문 {i+1}',
                    f'컨텍스트 {i+1}',
                    f'답변 {i+1}',
                    f'정답 {i+1}'
                ])
            
            yield f.name
        
        os.unlink(f.name)

    def test_large_data_import_performance(self, runner, large_csv_file):
        """대용량 데이터 Import 성능 테스트"""
        start_time = time.time()
        
        result = runner.invoke(cli.main, [
            'import-data', large_csv_file,
            '--batch-size', '20'
        ])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert '100개 항목 변환 완료' in result.output
        assert execution_time < 30  # 30초 이내에 완료되어야 함
        
        # 배치 처리 정보가 출력되는지 확인
        assert '배치 처리 정보' in result.output or '배치' in result.output
        
        # 정리
        output_file = large_csv_file.replace('.csv', '.json')
        if os.path.exists(output_file):
            # 출력 파일 크기 확인
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert len(data) == 100
            
            os.unlink(output_file)

    def test_batch_processor_performance(self):
        """배치 프로세서 성능 테스트"""
        # 테스트 데이터 생성
        test_data = []
        for i in range(50):
            test_data.append(EvaluationData(
                question=f"질문 {i+1}",
                contexts=[f"컨텍스트 {i+1}"],
                answer=f"답변 {i+1}",
                ground_truth=f"정답 {i+1}"
            ))
        
        # 배치 프로세서 설정
        config = BatchConfig(
            batch_size=10,
            max_retries=2,
            save_intermediate_results=False
        )
        processor = BatchDataProcessor(config)
        
        # 모킹된 처리 함수
        def mock_processor_func(batch_data):
            # 처리 시간 시뮬레이션
            time.sleep(0.01 * len(batch_data))
            return [f"결과 {data.question}" for data in batch_data]
        
        start_time = time.time()
        results = processor.process_batches_sync(test_data, mock_processor_func)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert len(results) == 50
        assert execution_time < 5  # 5초 이내에 완료
        
        # 진행 상황 확인
        progress = processor.get_progress_summary()
        assert progress is not None

    def test_memory_efficient_processing(self, runner, large_csv_file):
        """메모리 효율적 처리 테스트"""
        # 작은 배치 크기로 처리하여 메모리 사용량 최소화
        result = runner.invoke(cli.main, [
            'import-data', large_csv_file,
            '--batch-size', '5',  # 매우 작은 배치 크기
            '--validate'
        ])
        
        assert result.exit_code == 0
        assert '100개 항목 변환 완료' in result.output
        
        # 정리
        output_file = large_csv_file.replace('.csv', '.json')
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_validation_performance(self):
        """데이터 검증 성능 테스트"""
        # 대량의 테스트 데이터 생성
        test_data = []
        for i in range(200):
            test_data.append(EvaluationData(
                question=f"성능 테스트 질문 {i+1}",
                contexts=[f"컨텍스트 {i+1}-1", f"컨텍스트 {i+1}-2"],
                answer=f"성능 테스트 답변 {i+1}",
                ground_truth=f"성능 테스트 정답 {i+1}"
            ))
        
        validator = ImportDataValidator()
        
        start_time = time.time()
        result = validator.validate_data_list(test_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result.is_valid
        assert result.total_records == 200
        assert result.valid_records == 200
        assert execution_time < 2  # 2초 이내에 완료

    def test_concurrent_import_simulation(self, runner, medium_csv_file):
        """동시 Import 시뮬레이션 (순차적으로 실행)"""
        results = []
        
        # 여러 번의 Import 작업을 순차적으로 실행
        for i in range(3):
            start_time = time.time()
            
            result = runner.invoke(cli.main, [
                'import-data', medium_csv_file,
                '--output', f'/tmp/test_output_{i}.json'
            ])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            results.append({
                'exit_code': result.exit_code,
                'execution_time': execution_time,
                'output_file': f'/tmp/test_output_{i}.json'
            })
        
        # 모든 작업이 성공했는지 확인
        for i, result in enumerate(results):
            assert result['exit_code'] == 0
            assert result['execution_time'] < 10  # 각 작업이 10초 이내에 완료
            
            # 출력 파일 확인 및 정리
            if os.path.exists(result['output_file']):
                with open(result['output_file'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert len(data) == 10
                
                os.unlink(result['output_file'])

    def test_large_context_handling(self, runner):
        """대용량 컨텍스트 처리 테스트"""
        # 매우 긴 컨텍스트를 가진 데이터 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['question', 'contexts', 'answer', 'ground_truth'])
            
            # 각 컨텍스트가 1000자 정도인 데이터
            long_context = "매우 긴 컨텍스트 내용 " * 50  # 약 1000자
            contexts = f'"{long_context}";"{long_context}";"{long_context}"'
            
            for i in range(5):
                writer.writerow([
                    f'긴 컨텍스트 테스트 질문 {i+1}',
                    contexts,
                    f'긴 컨텍스트 테스트 답변 {i+1}',
                    f'긴 컨텍스트 테스트 정답 {i+1}'
                ])
            
            csv_file = f.name
        
        try:
            result = runner.invoke(cli.main, [
                'import-data', csv_file,
                '--validate'
            ])
            
            assert result.exit_code == 0
            assert '5개 항목 변환 완료' in result.output
            
            # 정리
            output_file = csv_file.replace('.csv', '.json')
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert len(data) == 5
                    # 컨텍스트가 제대로 분리되었는지 확인
                    assert len(data[0]['contexts']) == 3
                
                os.unlink(output_file)
        
        finally:
            os.unlink(csv_file)

    def test_file_size_limits(self, runner):
        """파일 크기 제한 테스트"""
        # 상당히 큰 파일 생성 (메모리 제한 내에서)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['question', 'contexts', 'answer', 'ground_truth'])
            
            # 500개 항목으로 큰 파일 생성
            for i in range(500):
                writer.writerow([
                    f'대용량 파일 테스트 질문 {i+1}',
                    f'대용량 파일 테스트 컨텍스트 {i+1}',
                    f'대용량 파일 테스트 답변 {i+1}',
                    f'대용량 파일 테스트 정답 {i+1}'
                ])
            
            csv_file = f.name
        
        try:
            # 큰 파일 처리 테스트
            start_time = time.time()
            
            result = runner.invoke(cli.main, [
                'import-data', csv_file,
                '--batch-size', '50'
            ])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert result.exit_code == 0
            assert '500개 항목 변환 완료' in result.output
            assert execution_time < 60  # 1분 이내에 완료
            
            # 정리
            output_file = csv_file.replace('.csv', '.json')
            if os.path.exists(output_file):
                # 출력 파일 크기 확인
                file_size = os.path.getsize(output_file)
                assert file_size > 0
                
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert len(data) == 500
                
                os.unlink(output_file)
        
        finally:
            os.unlink(csv_file)

    def test_progress_reporting_accuracy(self):
        """진행 상황 보고 정확성 테스트"""
        test_data = []
        for i in range(20):
            test_data.append(EvaluationData(
                question=f"진행률 테스트 질문 {i+1}",
                contexts=[f"컨텍스트 {i+1}"],
                answer=f"답변 {i+1}",
                ground_truth=f"정답 {i+1}"
            ))
        
        config = BatchConfig(
            batch_size=5,
            save_intermediate_results=False,
            enable_progress_callback=True
        )
        processor = BatchDataProcessor(config)
        
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append({
                'processed_items': progress.processed_items,
                'total_items': progress.total_items,
                'progress_percentage': progress.progress_percentage,
                'current_batch': progress.current_batch,
                'total_batches': progress.total_batches
            })
        
        processor.add_progress_callback(progress_callback)
        
        def mock_processor_func(batch_data):
            time.sleep(0.01)  # 처리 시간 시뮬레이션
            return [f"결과 {data.question}" for data in batch_data]
        
        results = processor.process_batches_sync(test_data, mock_processor_func)
        
        assert len(results) == 20
        assert len(progress_updates) == 4  # 4개 배치
        
        # 진행률이 올바르게 증가하는지 확인
        for i, update in enumerate(progress_updates):
            expected_processed = (i + 1) * 5
            assert update['processed_items'] == expected_processed
            assert update['total_items'] == 20
            assert update['current_batch'] == i + 1
            assert update['total_batches'] == 4
            
            expected_percentage = expected_processed / 20
            assert abs(update['progress_percentage'] - expected_percentage) < 0.01

    def test_error_recovery_performance(self):
        """오류 복구 성능 테스트"""
        test_data = []
        for i in range(15):
            test_data.append(EvaluationData(
                question=f"오류 복구 테스트 질문 {i+1}",
                contexts=[f"컨텍스트 {i+1}"],
                answer=f"답변 {i+1}",
                ground_truth=f"정답 {i+1}"
            ))
        
        config = BatchConfig(
            batch_size=5,
            max_retries=3,
            retry_delay=0.1,  # 빠른 재시도
            save_intermediate_results=False
        )
        processor = BatchDataProcessor(config)
        
        call_count = 0
        
        def failing_processor_func(batch_data):
            nonlocal call_count
            call_count += 1
            
            # 두 번째 배치에서 한 번 실패 후 성공
            if call_count == 2:
                raise Exception("일시적 오류")
            elif call_count == 3:  # 재시도에서 성공
                return [f"복구된 결과 {data.question}" for data in batch_data]
            
            return [f"결과 {data.question}" for data in batch_data]
        
        start_time = time.time()
        results = processor.process_batches_sync(test_data, failing_processor_func)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 오류가 발생했지만 일부 배치는 성공
        assert len(results) > 0
        assert execution_time < 5  # 재시도 포함해서 5초 이내
        
        # 진행 상황에 오류가 기록되었는지 확인
        progress = processor.get_progress_summary()
        assert progress is not None

    @pytest.mark.slow
    def test_stress_test_import_validation(self, runner):
        """스트레스 테스트: Import + 검증"""
        # 대량 데이터 생성 (1000개 항목)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['question', 'contexts', 'answer', 'ground_truth'])
            
            for i in range(1000):
                writer.writerow([
                    f'스트레스 테스트 질문 {i+1}',
                    f'스트레스 테스트 컨텍스트 {i+1}',
                    f'스트레스 테스트 답변 {i+1}',
                    f'스트레스 테스트 정답 {i+1}'
                ])
            
            csv_file = f.name
        
        try:
            start_time = time.time()
            
            result = runner.invoke(cli.main, [
                'import-data', csv_file,
                '--validate',
                '--batch-size', '100'
            ])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert result.exit_code == 0
            assert '1000개 항목 변환 완료' in result.output
            assert '성공률: 100.0%' in result.output
            assert execution_time < 120  # 2분 이내에 완료
            
            # 정리
            output_file = csv_file.replace('.csv', '.json')
            if os.path.exists(output_file):
                # 파일 크기 및 내용 확인
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert len(data) == 1000
                
                os.unlink(output_file)
        
        finally:
            os.unlink(csv_file)