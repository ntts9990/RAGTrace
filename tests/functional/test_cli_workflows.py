"""
CLI 워크플로우 통합 테스트

사용자가 CLI를 통해 수행하는 전체 워크플로우를 테스트합니다.
"""

import pytest
import tempfile
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# CLI 모듈을 import하기 위한 시스템 패스 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import cli
from src.domain.entities.evaluation_data import EvaluationData
from src.domain.entities.evaluation_result import EvaluationResult


class TestCLIWorkflows:
    """CLI 워크플로우 통합 테스트"""
    
    @pytest.fixture
    def sample_data_file(self):
        """테스트용 데이터 파일 생성"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            sample_data = [
                {
                    "question": "테스트 질문 1",
                    "contexts": ["테스트 컨텍스트 1", "테스트 컨텍스트 2"],
                    "answer": "테스트 답변 1",
                    "ground_truth": "테스트 정답 1"
                },
                {
                    "question": "테스트 질문 2", 
                    "contexts": ["테스트 컨텍스트 3"],
                    "answer": "테스트 답변 2",
                    "ground_truth": "테스트 정답 2"
                }
            ]
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
            yield f.name
        
        # 정리
        os.unlink(f.name)
    
    @pytest.fixture
    def mock_evaluation_result(self):
        """모킹된 평가 결과"""
        return EvaluationResult(
            faithfulness=0.8,
            answer_relevancy=0.9,
            context_recall=0.7,
            context_precision=0.85,
            ragas_score=0.8125,
            individual_scores=[],
            metadata={"dataset_name": "test_dataset", "model_name": "test_model"}
        )

    def test_list_datasets_command(self):
        """데이터셋 목록 조회 명령어 테스트"""
        with patch('cli.get_available_datasets') as mock_get_datasets, \
             patch('sys.argv', ['cli.py', 'list-datasets']), \
             patch('builtins.print') as mock_print:
            
            mock_get_datasets.return_value = ['dataset1', 'dataset2', 'dataset3']
            
            # CLI main 함수 직접 호출
            cli.main()
            
            # print 호출 확인
            print_calls = [str(call) for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            
            assert 'dataset1' in output
            assert 'dataset2' in output  
            assert 'dataset3' in output

    def test_list_datasets_empty(self):
        """빈 데이터셋 목록 테스트"""
        with patch('cli.get_available_datasets') as mock_get_datasets, \
             patch('sys.argv', ['cli.py', 'list-datasets']), \
             patch('builtins.print') as mock_print:
            
            mock_get_datasets.return_value = []
            
            cli.main()
            
            # print 호출 확인
            print_calls = [str(call) for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            
            assert '사용 가능한 데이터셋이 없습니다' in output

    def test_list_prompts_command(self):
        """프롬프트 타입 목록 조회 명령어 테스트"""
        with patch('sys.argv', ['cli.py', 'list-prompts']), \
             patch('builtins.print') as mock_print:
            
            cli.main()
            
            # print 호출 확인
            print_calls = [str(call) for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            
            assert '사용 가능한 프롬프트 타입' in output
            assert 'default' in output

    @patch('cli.container')
    @patch('cli.get_evaluation_data_path')
    def test_evaluate_basic_workflow(self, mock_path, mock_container, mock_evaluation_result, sample_data_file):
        """기본 평가 워크플로우 테스트"""
        # Mock 설정
        mock_path.return_value = sample_data_file
        
        # Container와 관련 서비스들 모킹
        mock_llm = MagicMock()
        mock_embedding = MagicMock()
        mock_ragas_adapter = MagicMock()
        mock_use_case = MagicMock()
        
        mock_container.llm_providers.return_value = {'gemini': mock_llm}
        mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
        mock_container.ragas_eval_adapter.return_value = mock_ragas_adapter
        mock_container.run_evaluation_use_case.return_value = mock_use_case
        
        mock_use_case.execute.return_value = mock_evaluation_result
        
        # 평가 실행
        with patch('sys.argv', ['cli.py', 'evaluate', 'test_dataset', '--llm', 'gemini', '--embedding', 'bge_m3']), \
             patch('builtins.print') as mock_print:
            
            cli.main()
            
            # print 호출 확인
            print_calls = [str(call) for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            
            assert '평가를 시작합니다' in output
            assert '평가가 완료되었습니다' in output
            assert 'RAGAS Score' in output

    @patch('cli.container')
    @patch('cli.get_evaluation_data_path')
    def test_evaluate_with_output_file(self, mock_path, mock_container, runner, mock_evaluation_result, sample_data_file):
        """결과 파일 저장 옵션 테스트"""
        mock_path.return_value = sample_data_file
        
        # Container 모킹
        mock_llm = MagicMock()
        mock_embedding = MagicMock()
        mock_use_case = MagicMock()
        
        mock_container.llm_providers.return_value = {'gemini': mock_llm}
        mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
        mock_container.ragas_eval_adapter.return_value = MagicMock()
        mock_container.run_evaluation_use_case.return_value = mock_use_case
        
        mock_use_case.execute.return_value = mock_evaluation_result
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
            result = runner.invoke(cli.main, [
                'evaluate', 'test_dataset',
                '--llm', 'gemini',
                '--embedding', 'bge_m3',
                '--output', output_file.name
            ])
            
            assert result.exit_code == 0
            assert f'결과가 {output_file.name}에 저장되었습니다' in result.output
            
            # 출력 파일 검증
            assert os.path.exists(output_file.name)
            with open(output_file.name, 'r', encoding='utf-8') as f:
                saved_result = json.load(f)
                assert 'ragas_score' in saved_result
            
            # 정리
            os.unlink(output_file.name)

    @patch('cli.container')
    def test_evaluate_missing_dataset(self, mock_container, runner):
        """존재하지 않는 데이터셋 처리 테스트"""
        with patch('cli.get_evaluation_data_path') as mock_path:
            mock_path.return_value = None  # 데이터셋을 찾을 수 없음
            
            result = runner.invoke(cli.main, [
                'evaluate', 'nonexistent_dataset',
                '--llm', 'gemini'
            ])
            
            assert result.exit_code == 1
            assert '데이터셋을 찾을 수 없습니다' in result.output

    @patch('cli.container')
    @patch('cli.get_evaluation_data_path') 
    def test_evaluate_api_key_missing(self, mock_path, mock_container, runner, sample_data_file):
        """API 키 누락 시 오류 처리 테스트"""
        mock_path.return_value = sample_data_file
        mock_container.llm_providers.return_value = {'hcx': MagicMock()}
        
        # CLOVA_STUDIO_API_KEY가 없는 상황 시뮬레이션
        with patch('cli.settings.CLOVA_STUDIO_API_KEY', None):
            result = runner.invoke(cli.main, [
                'evaluate', 'test_dataset',
                '--llm', 'hcx'
            ])
            
            assert result.exit_code == 1
            assert 'CLOVA_STUDIO_API_KEY를 설정해야 합니다' in result.output

    @patch('cli.container')
    @patch('cli.get_evaluation_data_path')
    def test_evaluate_with_verbose_output(self, mock_path, mock_container, runner, mock_evaluation_result, sample_data_file):
        """상세 출력 옵션 테스트"""
        mock_path.return_value = sample_data_file
        
        # Container 모킹
        mock_llm = MagicMock()
        mock_embedding = MagicMock() 
        mock_use_case = MagicMock()
        
        mock_container.llm_providers.return_value = {'gemini': mock_llm}
        mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
        mock_container.ragas_eval_adapter.return_value = MagicMock()
        mock_container.run_evaluation_use_case.return_value = mock_use_case
        
        mock_use_case.execute.return_value = mock_evaluation_result
        
        result = runner.invoke(cli.main, [
            'evaluate', 'test_dataset',
            '--llm', 'gemini',
            '--embedding', 'bge_m3',
            '--verbose'
        ])
        
        assert result.exit_code == 0
        assert '상세한 로그가 활성화되었습니다' in result.output

    def test_help_command(self, runner):
        """도움말 명령어 테스트"""
        result = runner.invoke(cli.main, ['--help'])
        
        assert result.exit_code == 0
        assert 'RAGTrace - RAG 시스템 성능 평가 도구' in result.output
        assert 'evaluate' in result.output
        assert 'list-datasets' in result.output
        assert 'list-prompts' in result.output
        assert 'import-data' in result.output

    def test_invalid_command(self, runner):
        """잘못된 명령어 처리 테스트"""
        result = runner.invoke(cli.main, ['invalid-command'])
        
        assert result.exit_code == 1
        assert '알 수 없는 명령어' in result.output

    @patch('cli.container')
    @patch('cli.get_evaluation_data_path')
    def test_evaluation_exception_handling(self, mock_path, mock_container, runner, sample_data_file):
        """평가 중 예외 발생 처리 테스트"""
        mock_path.return_value = sample_data_file
        
        # Container 모킹
        mock_llm = MagicMock()
        mock_embedding = MagicMock()
        mock_use_case = MagicMock()
        
        mock_container.llm_providers.return_value = {'gemini': mock_llm}
        mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
        mock_container.ragas_eval_adapter.return_value = MagicMock()
        mock_container.run_evaluation_use_case.return_value = mock_use_case
        
        # 평가 중 예외 발생 시뮬레이션
        mock_use_case.execute.side_effect = Exception("테스트 예외")
        
        result = runner.invoke(cli.main, [
            'evaluate', 'test_dataset',
            '--llm', 'gemini',
            '--embedding', 'bge_m3'
        ])
        
        assert result.exit_code == 1
        assert '평가 중 오류가 발생했습니다' in result.output
        assert '테스트 예외' in result.output

    @patch('cli.validate_settings')
    def test_settings_validation_failure(self, mock_validate, runner):
        """설정 검증 실패 처리 테스트"""
        mock_validate.side_effect = ValueError("설정 오류 테스트")
        
        result = runner.invoke(cli.main, ['list-datasets'])
        
        assert result.exit_code == 1
        assert '설정 오류' in result.output
        assert '설정 오류 테스트' in result.output

    def test_multiple_commands_sequence(self, runner):
        """여러 명령어 순차 실행 테스트 (실제 사용자 워크플로우)"""
        # 1. 데이터셋 목록 확인
        with patch('cli.get_available_datasets') as mock_get_datasets:
            mock_get_datasets.return_value = ['test_data', 'sample_data']
            
            result1 = runner.invoke(cli.main, ['list-datasets'])
            assert result1.exit_code == 0
            assert 'test_data' in result1.output
        
        # 2. 프롬프트 타입 확인  
        result2 = runner.invoke(cli.main, ['list-prompts'])
        assert result2.exit_code == 0
        assert 'default' in result2.output
        
        # 3. 평가 실행 (모킹됨)
        with patch('cli.container') as mock_container, \
             patch('cli.get_evaluation_data_path') as mock_path:
            
            mock_path.return_value = '/fake/path'
            mock_llm = MagicMock()
            mock_embedding = MagicMock()
            mock_use_case = MagicMock()
            
            mock_container.llm_providers.return_value = {'gemini': mock_llm}
            mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
            mock_container.ragas_eval_adapter.return_value = MagicMock()
            mock_container.run_evaluation_use_case.return_value = mock_use_case
            
            mock_result = EvaluationResult(
                faithfulness=0.9,
                answer_relevancy=0.8,
                context_recall=0.85,
                context_precision=0.75,
                ragas_score=0.825,
                individual_scores=[],
                metadata={"dataset_name": "test_data", "model_name": "gemini"}
            )
            mock_use_case.execute.return_value = mock_result
            
            result3 = runner.invoke(cli.main, [
                'evaluate', 'test_data',
                '--llm', 'gemini',
                '--embedding', 'bge_m3'
            ])
            assert result3.exit_code == 0
            assert 'RAGAS Score' in result3.output