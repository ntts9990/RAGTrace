from typing import Dict, Any
from datasets import Dataset

from src.application.ports.llm import LlmPort
from src.application.ports.repository import EvaluationRepositoryPort


class EvaluationService:
    """평가 비즈니스 로직을 수행하는 서비스 (Use Case)"""

    def __init__(
        self,
        llm_port: LlmPort,
        repository_port: EvaluationRepositoryPort,
        evaluation_runner: Any,  # RagasEvalAdapter
    ):
        self.llm_port = llm_port
        self.repository_port = repository_port
        self.evaluation_runner = evaluation_runner

    def run_evaluation(self) -> Dict[str, float]:
        """
        데이터 로드, 데이터셋 변환, 평가 실행의 전체 과정을 관장합니다.
        """
        # 1. 데이터 로드 (Port를 통해)
        evaluation_data_list = self.repository_port.load_data()
        if not evaluation_data_list:
            raise ValueError("평가 데이터가 없습니다.")

        print(f"평가할 데이터 개수: {len(evaluation_data_list)}개")

        # 2. Ragas가 요구하는 Dataset 형식으로 변환
        data_dict = {
            "question": [d.question for d in evaluation_data_list],
            "contexts": [d.contexts for d in evaluation_data_list],
            "answer": [d.answer for d in evaluation_data_list],
            "ground_truth": [d.ground_truth for d in evaluation_data_list],
        }
        dataset = Dataset.from_dict(data_dict)

        # 3. LLM 객체 가져오기 (Port를 통해)
        llm = self.llm_port.get_llm()

        # 4. 평가 실행 (Infrastructure에 위임)
        result = self.evaluation_runner.evaluate(
            dataset=dataset,
            llm=llm
        )
        
        # 5. 결과 검증
        if not result or all(v == 0.0 for v in result.values()):
            print("\n경고: 모든 평가 점수가 0입니다. 다음을 확인해주세요:")
            print("1. API 키가 올바르게 설정되었는지 확인")
            print("2. Gemini API 할당량이 남아있는지 확인")
            print("3. 네트워크 연결이 정상인지 확인")
            print("4. 평가 데이터 형식이 올바른지 확인")
        
        return result 