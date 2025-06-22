"""
기본 워크플로우 테스트

핵심 기능들의 기본적인 동작을 테스트합니다.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 시스템 패스 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.data_import.importers import CSVImporter, ExcelImporter, ImporterFactory
from src.infrastructure.data_import.validators import ImportDataValidator
from src.domain.entities.evaluation_data import EvaluationData
from src.utils.paths import get_available_datasets


class TestBasicWorkflows:
    """기본 워크플로우 테스트"""
    
    def test_csv_importer_workflow(self):
        """CSV 임포터 기본 워크플로우 테스트"""
        # CSV 파일 생성
        csv_content = """question,contexts,answer,ground_truth
"테스트 질문","테스트 컨텍스트","테스트 답변","테스트 정답"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_file = f.name
        
        try:
            # 임포터 생성 및 검증
            importer = CSVImporter()
            assert importer.validate_format(csv_file)
            
            # 데이터 임포트
            data_list = importer.import_data(csv_file)
            
            # 결과 검증
            assert len(data_list) == 1
            assert isinstance(data_list[0], EvaluationData)
            assert data_list[0].question == "테스트 질문"
            assert data_list[0].contexts == ["테스트 컨텍스트"]
            assert data_list[0].answer == "테스트 답변"
            assert data_list[0].ground_truth == "테스트 정답"
            
        finally:
            os.unlink(csv_file)

    def test_importer_factory_workflow(self):
        """임포터 팩토리 워크플로우 테스트"""
        # CSV 임포터 생성
        csv_importer = ImporterFactory.create_importer('test.csv')
        assert isinstance(csv_importer, CSVImporter)
        
        # Excel 임포터 생성
        excel_importer = ImporterFactory.create_importer('test.xlsx')
        assert isinstance(excel_importer, ExcelImporter)
        
        # 지원 형식 확인
        formats = ImporterFactory.get_supported_formats()
        assert '.csv' in formats
        assert '.xlsx' in formats
        assert '.xls' in formats

    def test_data_validator_workflow(self):
        """데이터 검증기 워크플로우 테스트"""
        # 유효한 데이터 생성
        valid_data = [
            EvaluationData(
                question="유효한 질문",
                contexts=["컨텍스트 1", "컨텍스트 2"],
                answer="유효한 답변",
                ground_truth="유효한 정답"
            )
        ]
        
        validator = ImportDataValidator()
        result = validator.validate_data_list(valid_data)
        
        # 검증 결과 확인
        assert result.is_valid
        assert result.total_records == 1
        assert result.valid_records == 1
        assert result.success_rate == 1.0
        assert len(result.errors) == 0
        
        # 요약 메시지 생성 테스트
        summary = validator.get_validation_summary(result)
        assert "검증 결과" in summary
        assert "성공률: 100.0%" in summary

    def test_invalid_data_validation(self):
        """잘못된 데이터 검증 테스트"""
        # 잘못된 데이터 (빈 질문) - EvaluationData에서 예외가 발생해야 함
        with pytest.raises(ValueError, match="Question cannot be empty"):
            EvaluationData(
                question="",  # 빈 질문
                contexts=["컨텍스트"],
                answer="답변",
                ground_truth="정답"
            )

    def test_contexts_parsing_variations(self):
        """다양한 contexts 형식 파싱 테스트"""
        importer = CSVImporter()
        
        # JSON 배열 형식
        json_contexts = '["ctx1", "ctx2", "ctx3"]'
        parsed = importer._parse_contexts(json_contexts)
        assert parsed == ["ctx1", "ctx2", "ctx3"]
        
        # 세미콜론 구분
        semicolon_contexts = "ctx1;ctx2;ctx3"
        parsed = importer._parse_contexts(semicolon_contexts)
        assert parsed == ["ctx1", "ctx2", "ctx3"]
        
        # 파이프 구분
        pipe_contexts = "ctx1|ctx2|ctx3"
        parsed = importer._parse_contexts(pipe_contexts)
        assert parsed == ["ctx1", "ctx2", "ctx3"]
        
        # 단일 컨텍스트
        single_context = "single context"
        parsed = importer._parse_contexts(single_context)
        assert parsed == ["single context"]

    def test_error_handling(self):
        """오류 처리 테스트"""
        # 존재하지 않는 파일
        importer = CSVImporter()
        with pytest.raises(ImportError):
            importer.import_data("nonexistent_file.csv")
        
        # 지원되지 않는 형식
        with pytest.raises(ValueError):
            ImporterFactory.create_importer("test.txt")

    def test_dataset_discovery(self):
        """데이터셋 발견 기능 테스트"""
        # 실제 데이터셋 확인 (현재 data/ 디렉토리에 있는 파일들)
        datasets = get_available_datasets()
        
        # 최소한 하나의 데이터셋이 있어야 함
        assert len(datasets) > 0
        assert isinstance(datasets, list)
        
        # 실제 데이터셋들이 있는지 확인
        for dataset in datasets:
            assert isinstance(dataset, str)
            assert len(dataset) > 0

    def test_evaluation_data_validation(self):
        """EvaluationData 엔티티 검증 테스트"""
        # 유효한 데이터
        valid_data = EvaluationData(
            question="테스트 질문",
            contexts=["컨텍스트"],
            answer="테스트 답변",
            ground_truth="테스트 정답"
        )
        assert valid_data.question == "테스트 질문"
        
        # 빈 질문 - 예외 발생해야 함
        with pytest.raises(ValueError, match="Question cannot be empty"):
            EvaluationData(
                question="",
                contexts=["컨텍스트"],
                answer="답변",
                ground_truth="정답"
            )
        
        # 빈 컨텍스트 - 예외 발생해야 함
        with pytest.raises(ValueError, match="Contexts cannot be empty"):
            EvaluationData(
                question="질문",
                contexts=[],
                answer="답변",
                ground_truth="정답"
            )

    def test_complete_import_validation_workflow(self):
        """완전한 Import + 검증 워크플로우 테스트"""
        # CSV 데이터 준비
        csv_content = """question,contexts,answer,ground_truth
"좋은 질문","좋은 컨텍스트","좋은 답변","좋은 정답"
"짧음","컨텍스트","답변","정답"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_file = f.name
        
        try:
            # 1. Import
            importer = ImporterFactory.create_importer(csv_file)
            assert importer.validate_format(csv_file)
            
            data_list = importer.import_data(csv_file)
            assert len(data_list) == 2
            
            # 2. 검증
            validator = ImportDataValidator()
            result = validator.validate_data_list(data_list)
            
            # 모든 데이터가 유효해야 함
            assert result.is_valid
            assert result.total_records == 2
            assert result.valid_records == 2
            
            # 하지만 경고가 있을 수 있음 (짧은 질문)
            summary = validator.get_validation_summary(result)
            assert "검증 결과" in summary
            
        finally:
            os.unlink(csv_file)

    def test_memory_efficient_processing_simulation(self):
        """메모리 효율적 처리 시뮬레이션"""
        # 여러 개의 데이터 생성
        data_list = []
        for i in range(10):
            data_list.append(EvaluationData(
                question=f"질문 {i+1}",
                contexts=[f"컨텍스트 {i+1}"],
                answer=f"답변 {i+1}",
                ground_truth=f"정답 {i+1}"
            ))
        
        # 검증 처리
        validator = ImportDataValidator()
        result = validator.validate_data_list(data_list)
        
        assert result.total_records == 10
        assert result.valid_records == 10
        assert result.success_rate == 1.0

    def test_edge_cases(self):
        """엣지 케이스 테스트"""
        importer = CSVImporter()
        
        # 매우 긴 컨텍스트
        long_context = "매우 긴 컨텍스트 " * 101  # 1000+ 글자
        parsed = importer._parse_contexts(long_context)
        assert len(parsed) == 1
        assert len(parsed[0]) > 1000
        
        # 특수 문자가 포함된 컨텍스트
        special_context = '["특수;문자|포함", "두번째;컨텍스트"]'
        parsed = importer._parse_contexts(special_context)
        assert len(parsed) == 2
        assert "특수;문자|포함" in parsed
        assert "두번째;컨텍스트" in parsed

    def test_configuration_validation(self):
        """설정 검증 테스트"""
        from src.config import SUPPORTED_LLM_TYPES, SUPPORTED_EMBEDDING_TYPES
        
        # 지원되는 LLM 타입 확인
        assert 'gemini' in SUPPORTED_LLM_TYPES
        assert 'hcx' in SUPPORTED_LLM_TYPES
        
        # 지원되는 임베딩 타입 확인
        assert 'gemini' in SUPPORTED_EMBEDDING_TYPES
        assert 'hcx' in SUPPORTED_EMBEDDING_TYPES
        assert 'bge_m3' in SUPPORTED_EMBEDDING_TYPES
        
        # 기본 설정값들이 지원되는 타입에 포함되어야 함
        from src.config import settings
        assert settings.DEFAULT_LLM in SUPPORTED_LLM_TYPES
        assert settings.DEFAULT_EMBEDDING in SUPPORTED_EMBEDDING_TYPES