"""포트 인터페이스 테스트"""
import pytest
from abc import ABC
from unittest.mock import MagicMock

from src.application.ports.evaluation import EvaluationRunnerPort
from src.application.ports.llm import LlmPort
from src.application.ports.repository import EvaluationRepositoryPort


class TestEvaluationRunnerPort:
    """EvaluationRunnerPort 테스트"""
    
    def test_abstract_method_coverage(self):
        """추상 메서드의 pass 문 커버리지 테스트"""
        # 추상 클래스를 직접 인스턴스화할 수 없으므로
        # 구체적인 구현체를 만들어 테스트
        class TestEvaluationRunner(EvaluationRunnerPort):
            def evaluate(self, dataset, llm):
                # 부모 클래스의 추상 메서드 호출하여 pass 문 실행
                super().evaluate(dataset, llm)
                return {"test": 0.5}
        
        runner = TestEvaluationRunner()
        result = runner.evaluate(MagicMock(), MagicMock())
        assert result["test"] == 0.5


class TestLlmPort:
    """LlmPort 테스트"""
    
    def test_abstract_method_coverage(self):
        """추상 메서드의 pass 문 커버리지 테스트"""
        class TestLlmPort(LlmPort):
            def get_llm(self):
                # 부모 클래스의 추상 메서드 호출하여 pass 문 실행
                super().get_llm()
                return MagicMock()
        
        llm_port = TestLlmPort()
        llm = llm_port.get_llm()
        assert llm is not None


class TestEvaluationRepositoryPort:
    """EvaluationRepositoryPort 테스트"""
    
    def test_abstract_method_coverage(self):
        """추상 메서드의 pass 문 커버리지 테스트"""
        class TestRepositoryPort(EvaluationRepositoryPort):
            def load_data(self):
                # 부모 클래스의 추상 메서드 호출하여 pass 문 실행
                super().load_data()
                return []
        
        repo_port = TestRepositoryPort()
        data = repo_port.load_data()
        assert data == [] 