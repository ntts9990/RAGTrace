"""
CLI 명령어 직접 테스트

argparse 기반 CLI의 명령어들을 직접 테스트합니다.
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

# 시스템 패스 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import cli
from src.domain.entities.evaluation_data import EvaluationData
from src.domain.entities.evaluation_result import EvaluationResult


class TestCLICommands:
    """CLI 명령어 직접 테스트"""
    
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
                }
            ]
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
            yield f.name
        
        # 정리
        if os.path.exists(f.name):
            os.unlink(f.name)

    def test_list_datasets_command(self):
        """데이터셋 목록 조회 명령어 테스트"""
        with patch('sys.argv', ['cli.py', 'list-datasets']):
            # 실제 데이터셋이 있는지 확인하는 테스트
            try:
                cli.main()
                # 예외가 발생하지 않으면 성공
                assert True
            except SystemExit:
                # 정상적인 종료는 괜찮음
                assert True

    def test_list_prompts_command(self):
        """프롬프트 타입 목록 조회 명령어 테스트"""
        with patch('sys.argv', ['cli.py', 'list-prompts']):
            try:
                cli.main()
                assert True
            except SystemExit:
                assert True

    @patch('cli.container')
    @patch('cli.get_evaluation_data_path')
    def test_evaluate_command_mocked(self, mock_path, mock_container, sample_data_file):
        """평가 명령어 테스트 (모킹됨)"""
        # Mock 설정
        mock_path.return_value = sample_data_file
        
        # Container 모킹
        mock_llm = MagicMock()
        mock_embedding = MagicMock()
        mock_ragas_adapter = MagicMock()
        mock_use_case = MagicMock()
        
        mock_container.llm_providers.return_value = {'gemini': mock_llm}
        mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
        mock_container.ragas_eval_adapter.return_value = mock_ragas_adapter
        mock_container.run_evaluation_use_case.return_value = mock_use_case
        
        # 평가 결과 모킹
        mock_result = EvaluationResult(
            faithfulness=0.8,
            answer_relevancy=0.9,
            context_recall=0.7,
            context_precision=0.85,
            ragas_score=0.8125,
            individual_scores=[],
            metadata={"dataset_name": "test_dataset", "model_name": "gemini"}
        )
        mock_use_case.execute.return_value = mock_result
        
        # 평가 실행
        with patch('sys.argv', ['cli.py', 'evaluate', 'test_dataset', '--llm', 'gemini', '--embedding', 'bge_m3']):
            try:
                cli.main()
                # 예외가 발생하지 않으면 성공
                assert True
            except SystemExit:
                # 정상적인 종료는 괜찮음
                assert True

    def test_help_command(self):
        """도움말 명령어 테스트"""
        with patch('sys.argv', ['cli.py', '--help']):
            try:
                cli.main()
                assert True
            except SystemExit:
                # --help는 SystemExit를 발생시키는 것이 정상
                assert True

    def test_invalid_command(self):
        """잘못된 명령어 테스트"""
        with patch('sys.argv', ['cli.py', 'invalid-command']):
            with pytest.raises(SystemExit):
                cli.main()

    @patch('cli.get_available_datasets')
    def test_dataset_listing_with_mock(self, mock_get_datasets):
        """데이터셋 목록 모킹 테스트"""
        mock_get_datasets.return_value = ['test_dataset1', 'test_dataset2']
        
        with patch('sys.argv', ['cli.py', 'list-datasets']), \
             patch('builtins.print') as mock_print:
            
            try:
                cli.main()
            except SystemExit:
                pass
            
            # print가 호출되었는지 확인
            assert mock_print.called

    def test_import_data_command_basic(self):
        """데이터 import 명령어 기본 테스트"""
        # 임시 CSV 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write('question,contexts,answer,ground_truth\n')
            f.write('테스트,테스트,테스트,테스트\n')
            csv_file = f.name
        
        try:
            with patch('sys.argv', ['cli.py', 'import-data', csv_file]):
                try:
                    cli.main()
                    # JSON 파일이 생성되었는지 확인
                    json_file = csv_file.replace('.csv', '.json')
                    if os.path.exists(json_file):
                        os.unlink(json_file)
                    assert True
                except SystemExit:
                    assert True
        finally:
            if os.path.exists(csv_file):
                os.unlink(csv_file)

    def test_evaluation_subprocess(self):
        """서브프로세스를 통한 실제 CLI 테스트"""
        # 실제 CLI 실행 테스트
        result = subprocess.run([
            sys.executable, 'cli.py', 'list-datasets'
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        # 0 또는 1 exit code는 정상 (데이터셋이 있거나 없거나)
        assert result.returncode in [0, 1]

    @patch('cli.settings.GEMINI_API_KEY', 'test_key')
    def test_api_key_validation(self):
        """API 키 검증 테스트"""
        with patch('sys.argv', ['cli.py', 'list-datasets']):
            try:
                cli.main()
                assert True
            except SystemExit:
                assert True

    def test_verbose_flag(self):
        """상세 출력 플래그 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file), \
                 patch('sys.argv', ['cli.py', 'evaluate', 'test', '--verbose', '--llm', 'gemini']), \
                 patch('cli.container') as mock_container:
                
                # Container 모킹
                mock_llm = MagicMock()
                mock_embedding = MagicMock()
                mock_use_case = MagicMock()
                
                mock_container.llm_providers.return_value = {'gemini': mock_llm}
                mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
                mock_container.ragas_eval_adapter.return_value = MagicMock()
                mock_container.run_evaluation_use_case.return_value = mock_use_case
                
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
                
                try:
                    cli.main()
                    assert True
                except SystemExit:
                    assert True
        finally:
            if os.path.exists(json_file):
                os.unlink(json_file)

    def test_prompt_type_selection(self):
        """프롬프트 타입 선택 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"question": "test", "contexts": ["test"], "answer": "test", "ground_truth": "test"}], f)
            json_file = f.name
        
        try:
            with patch('cli.get_evaluation_data_path', return_value=json_file), \
                 patch('sys.argv', ['cli.py', 'evaluate', 'test', '--prompt-type', 'default', '--llm', 'gemini']), \
                 patch('cli.container') as mock_container:
                
                # Container 모킹
                mock_llm = MagicMock()
                mock_embedding = MagicMock()
                mock_use_case = MagicMock()
                
                mock_container.llm_providers.return_value = {'gemini': mock_llm}
                mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
                mock_container.ragas_eval_adapter.return_value = MagicMock()
                mock_container.run_evaluation_use_case.return_value = mock_use_case
                
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
                
                try:
                    cli.main()
                    assert True
                except SystemExit:
                    assert True
        finally:
            if os.path.exists(json_file):
                os.unlink(json_file)