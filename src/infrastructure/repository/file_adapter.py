import json

from src.application.ports.repository import EvaluationRepositoryPort
from src.domain import EvaluationData


class FileRepositoryAdapter(EvaluationRepositoryPort):
    """파일 시스템에서 평가 데이터셋을 로드하는 구현체 (Adapter)"""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_data(self) -> list[EvaluationData]:
        """
        지정된 경로의 JSON 파일을 읽어 EvaluationData 객체 리스트로 변환합니다.
        """
        try:
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)

            return [EvaluationData(**item) for item in data]
        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다 - {self.file_path}")
            return []
        except json.JSONDecodeError:
            print(f"오류: JSON 파싱 중 오류가 발생했습니다 - {self.file_path}")
            return []
        except Exception as e:
            print(f"데이터 로드 중 예기치 않은 오류 발생: {e}")
            return []
