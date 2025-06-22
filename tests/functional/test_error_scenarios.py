"""
오류 시나리오 테스트

다양한 실패 케이스와 오류 처리를 테스트합니다.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from click.testing import CliRunner

# 시스템 패스 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import cli
from src.domain.exceptions.evaluation_exceptions import (
    InvalidEvaluationDataError, 
    EvaluationTimeoutError,
    LLMConnectionError
)
from src.domain.entities.evaluation_data import EvaluationData


class TestErrorScenarios:
    """오류 시나리오 테스트"""
    
    @pytest.fixture
    def runner(self):
        """CLI 테스트 러너"""
        return CliRunner()
    
    @pytest.fixture
    def corrupted_json_file(self):
        """손상된 JSON 파일"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content}')  # 잘못된 JSON
            yield f.name
        
        os.unlink(f.name)
    
    @pytest.fixture
    def invalid_data_json_file(self):
        """잘못된 데이터 구조의 JSON 파일"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            invalid_data = [
                {
                    "wrong_field": "value",
                    "another_wrong": "value2"
                    # 필수 필드들이 없음
                }
            ]
            json.dump(invalid_data, f)
            yield f.name
        
        os.unlink(f.name)

    def test_file_not_found_error(self, runner):
        """파일을 찾을 수 없는 오류 테스트"""
        result = runner.invoke(cli.main, [
            'evaluate', 'nonexistent_dataset',
            '--llm', 'gemini'
        ])
        
        assert result.exit_code == 1
        assert '데이터셋을 찾을 수 없습니다' in result.output

    def test_import_nonexistent_file(self, runner):
        """존재하지 않는 파일 import 오류"""
        result = runner.invoke(cli.main, [
            'import-data', '/path/to/nonexistent/file.csv'
        ])
        
        assert result.exit_code == 1
        assert '변환 중 오류가 발생했습니다' in result.output

    def test_import_corrupted_file(self, runner, corrupted_json_file):
        """손상된 파일 import 오류"""
        # CSV로 이름 변경해서 테스트
        csv_file = corrupted_json_file.replace('.json', '.csv')
        os.rename(corrupted_json_file, csv_file)
        
        try:
            result = runner.invoke(cli.main, ['import-data', csv_file])
            
            assert result.exit_code == 1
            assert '변환 중 오류가 발생했습니다' in result.output
            
        finally:
            if os.path.exists(csv_file):
                os.unlink(csv_file)

    def test_permission_denied_error(self, runner):
        """권한 거부 오류 시뮬레이션"""
        # 읽기 권한이 없는 파일 생성 (Unix 시스템에서만)
        if os.name != 'nt':  # Windows가 아닌 경우
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write('question,contexts,answer,ground_truth\n')
                f.write('test,test,test,test\n')
                csv_file = f.name
            
            try:
                # 파일 권한 제거
                os.chmod(csv_file, 0o000)
                
                result = runner.invoke(cli.main, ['import-data', csv_file])
                
                assert result.exit_code == 1
                assert '변환 중 오류가 발생했습니다' in result.output
                
            finally:
                # 권한 복원 후 삭제
                os.chmod(csv_file, 0o644)
                os.unlink(csv_file)

    @patch('cli.container')
    def test_llm_initialization_error(self, mock_container, runner):
        """LLM 초기화 오류 테스트"""
        mock_container.llm_providers.side_effect = Exception("LLM 초기화 실패")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file):
                result = runner.invoke(cli.main, [
                    'evaluate', 'test_dataset',
                    '--llm', 'gemini'
                ])
                
                assert result.exit_code == 1
                assert 'LLM 또는' in result.output and '어댑터 초기화 중 오류' in result.output
        
        finally:
            os.unlink(json_file)

    @patch('cli.container')
    def test_missing_api_key_error(self, mock_container, runner):
        """API 키 누락 오류 테스트"""
        mock_container.llm_providers.return_value = {'hcx': MagicMock()}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file), \
                 patch('cli.settings.CLOVA_STUDIO_API_KEY', None):
                
                result = runner.invoke(cli.main, [
                    'evaluate', 'test_dataset',
                    '--llm', 'hcx'
                ])
                
                assert result.exit_code == 1
                assert 'CLOVA_STUDIO_API_KEY를 설정해야 합니다' in result.output
        
        finally:
            os.unlink(json_file)

    @patch('cli.container')
    @patch('cli.get_evaluation_data_path')
    def test_evaluation_runtime_error(self, mock_path, mock_container, runner):
        """평가 중 런타임 오류 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            mock_path.return_value = json_file
            
            # Container 모킹
            mock_llm = MagicMock()
            mock_embedding = MagicMock()
            mock_use_case = MagicMock()
            
            mock_container.llm_providers.return_value = {'gemini': mock_llm}
            mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
            mock_container.ragas_eval_adapter.return_value = MagicMock()
            mock_container.run_evaluation_use_case.return_value = mock_use_case
            
            # 평가 중 오류 발생 시뮬레이션
            mock_use_case.execute.side_effect = LLMConnectionError("평가 처리 중 오류")
            
            result = runner.invoke(cli.main, [
                'evaluate', 'test_dataset',
                '--llm', 'gemini',
                '--embedding', 'bge_m3'
            ])
            
            assert result.exit_code == 1
            assert '평가 중 오류가 발생했습니다' in result.output
            assert '평가 처리 중 오류' in result.output
        
        finally:
            os.unlink(json_file)

    def test_invalid_prompt_type_error(self, runner):
        """잘못된 프롬프트 타입 오류 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file):
                result = runner.invoke(cli.main, [
                    'evaluate', 'test_dataset',
                    '--llm', 'gemini',
                    '--prompt-type', 'invalid_prompt_type'
                ])
                
                assert result.exit_code == 1
                assert '잘못된 프롬프트 타입' in result.output
        
        finally:
            os.unlink(json_file)

    def test_output_file_permission_error(self, runner):
        """출력 파일 권한 오류 테스트"""
        if os.name != 'nt':  # Windows가 아닌 경우
            # 쓰기 권한이 없는 디렉토리 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                readonly_dir = Path(temp_dir) / 'readonly'
                readonly_dir.mkdir()
                os.chmod(readonly_dir, 0o444)  # 읽기 전용
                
                output_file = readonly_dir / 'output.json'
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
                    json_file = f.name
                
                try:
                    with patch('cli.get_evaluation_data_path', return_value=json_file), \
                         patch('cli.container') as mock_container:
                        
                        # Container 모킹
                        mock_llm = MagicMock()
                        mock_embedding = MagicMock()
                        mock_use_case = MagicMock()
                        
                        mock_container.llm_providers.return_value = {'gemini': mock_llm}
                        mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
                        mock_container.ragas_eval_adapter.return_value = MagicMock()
                        mock_container.run_evaluation_use_case.return_value = mock_use_case
                        
                        from src.domain.entities.evaluation_result import EvaluationResult
                        
                        mock_result = EvaluationResult(
                            faithfulness=0.8,
                            answer_relevancy=0.9,
                            context_recall=0.7,
                            context_precision=0.85,
                            ragas_score=0.8125,
                            individual_scores=[],
                            metadata={"dataset_name": "test", "model_name": "gemini"}
                        )
                        mock_use_case.execute.return_value = mock_result
                        
                        result = runner.invoke(cli.main, [
                            'evaluate', 'test_dataset',
                            '--llm', 'gemini',
                            '--embedding', 'bge_m3',
                            '--output', str(output_file)
                        ])
                        
                        # 평가는 성공하지만 파일 저장에서 오류 발생
                        assert result.exit_code == 1
                        assert '평가 중 오류가 발생했습니다' in result.output
                
                finally:
                    os.chmod(readonly_dir, 0o755)  # 권한 복원
                    os.unlink(json_file)

    def test_network_timeout_simulation(self, runner):
        """네트워크 타임아웃 시뮬레이션"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file), \
                 patch('cli.container') as mock_container:
                
                # Container 모킹
                mock_llm = MagicMock()
                mock_embedding = MagicMock()
                mock_use_case = MagicMock()
                
                mock_container.llm_providers.return_value = {'gemini': mock_llm}
                mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
                mock_container.ragas_eval_adapter.return_value = MagicMock()
                mock_container.run_evaluation_use_case.return_value = mock_use_case
                
                # 네트워크 타임아웃 시뮬레이션
                import requests
                mock_use_case.execute.side_effect = requests.exceptions.Timeout("네트워크 타임아웃")
                
                result = runner.invoke(cli.main, [
                    'evaluate', 'test_dataset',
                    '--llm', 'gemini',
                    '--embedding', 'bge_m3'
                ])
                
                assert result.exit_code == 1
                assert '평가 중 오류가 발생했습니다' in result.output
        
        finally:
            os.unlink(json_file)

    def test_memory_error_simulation(self, runner):
        """메모리 부족 오류 시뮬레이션"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file), \
                 patch('cli.container') as mock_container:
                
                # Container 모킹
                mock_llm = MagicMock()
                mock_embedding = MagicMock()
                mock_use_case = MagicMock()
                
                mock_container.llm_providers.return_value = {'gemini': mock_llm}
                mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
                mock_container.ragas_eval_adapter.return_value = MagicMock()
                mock_container.run_evaluation_use_case.return_value = mock_use_case
                
                # 메모리 오류 시뮬레이션
                mock_use_case.execute.side_effect = MemoryError("메모리 부족")
                
                result = runner.invoke(cli.main, [
                    'evaluate', 'test_dataset',
                    '--llm', 'gemini',
                    '--embedding', 'bge_m3'
                ])
                
                assert result.exit_code == 1
                assert '평가 중 오류가 발생했습니다' in result.output
        
        finally:
            os.unlink(json_file)

    def test_invalid_json_data_structure(self, runner, invalid_data_json_file):
        """잘못된 JSON 데이터 구조 오류 테스트"""
        with patch('cli.get_evaluation_data_path', return_value=invalid_data_json_file), \
             patch('cli.container') as mock_container:
            
            # Container 모킹
            mock_llm = MagicMock()
            mock_embedding = MagicMock()
            mock_use_case = MagicMock()
            
            mock_container.llm_providers.return_value = {'gemini': mock_llm}
            mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
            mock_container.ragas_eval_adapter.return_value = MagicMock()
            mock_container.run_evaluation_use_case.return_value = mock_use_case
            
            # 데이터 구조 오류로 인한 예외 시뮬레이션
            mock_use_case.execute.side_effect = InvalidEvaluationDataError("잘못된 데이터 구조")
            
            result = runner.invoke(cli.main, [
                'evaluate', 'test_dataset',
                '--llm', 'gemini',
                '--embedding', 'bge_m3'
            ])
            
            assert result.exit_code == 1
            assert '평가 중 오류가 발생했습니다' in result.output

    def test_disk_space_error_simulation(self, runner):
        """디스크 공간 부족 오류 시뮬레이션"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file), \
                 patch('cli.container') as mock_container:
                
                # Container 모킹
                mock_llm = MagicMock()
                mock_embedding = MagicMock()
                mock_use_case = MagicMock()
                
                mock_container.llm_providers.return_value = {'gemini': mock_llm}
                mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
                mock_container.ragas_eval_adapter.return_value = MagicMock()
                mock_container.run_evaluation_use_case.return_value = mock_use_case
                
                from src.domain.entities.evaluation_result import EvaluationResult
                
                mock_result = EvaluationResult(
                    faithfulness=0.8,
                    answer_relevancy=0.9,
                    context_recall=0.7,
                    context_precision=0.85,
                    ragas_score=0.8125,
                    individual_scores=[],
                    metadata={"dataset_name": "test", "model_name": "gemini"}
                )
                mock_use_case.execute.return_value = mock_result
                
                # 파일 쓰기 시 디스크 공간 부족 시뮬레이션
                with patch('builtins.open', side_effect=OSError("디스크 공간 부족")):
                    result = runner.invoke(cli.main, [
                        'evaluate', 'test_dataset',
                        '--llm', 'gemini',
                        '--embedding', 'bge_m3',
                        '--output', '/tmp/output.json'
                    ])
                    
                    assert result.exit_code == 1
                    assert '평가 중 오류가 발생했습니다' in result.output
        
        finally:
            os.unlink(json_file)

    def test_malformed_csv_import(self, runner):
        """잘못된 형식의 CSV 파일 import 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # 잘못된 CSV 형식 (따옴표 불일치)
            f.write('question,contexts,answer,ground_truth\n')
            f.write('"unterminated quote,test,test,test\n')  # 따옴표가 닫히지 않음
            csv_file = f.name
        
        try:
            result = runner.invoke(cli.main, ['import-data', csv_file])
            
            assert result.exit_code == 1
            assert '변환 중 오류가 발생했습니다' in result.output
        
        finally:
            os.unlink(csv_file)

    def test_concurrent_file_access_error(self, runner):
        """동시 파일 접근 오류 시뮬레이션"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('question,contexts,answer,ground_truth\n')
            f.write('test,test,test,test\n')
            csv_file = f.name
        
        try:
            # 파일이 다른 프로세스에서 사용 중인 상황 시뮬레이션
            with patch('pandas.read_csv', side_effect=PermissionError("파일이 사용 중입니다")):
                result = runner.invoke(cli.main, ['import-data', csv_file])
                
                assert result.exit_code == 1
                assert '변환 중 오류가 발생했습니다' in result.output
        
        finally:
            os.unlink(csv_file)

    def test_verbose_error_reporting(self, runner):
        """상세 오류 보고 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file), \
                 patch('cli.container') as mock_container:
                
                # Container 모킹
                mock_llm = MagicMock()
                mock_embedding = MagicMock()
                mock_use_case = MagicMock()
                
                mock_container.llm_providers.return_value = {'gemini': mock_llm}
                mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
                mock_container.ragas_eval_adapter.return_value = MagicMock()
                mock_container.run_evaluation_use_case.return_value = mock_use_case
                
                # 상세한 오류 정보가 포함된 예외
                mock_use_case.execute.side_effect = Exception("상세한 오류 메시지")
                
                result = runner.invoke(cli.main, [
                    'evaluate', 'test_dataset',
                    '--llm', 'gemini',
                    '--embedding', 'bge_m3',
                    '--verbose'
                ])
                
                assert result.exit_code == 1
                assert '평가 중 오류가 발생했습니다' in result.output
                assert '상세한 오류 메시지' in result.output
                # verbose 모드에서는 traceback도 출력되어야 함
        
        finally:
            os.unlink(json_file)