"""파일 리포지토리 팩토리"""

from src.application.ports.repository import EvaluationRepositoryPort
from src.infrastructure.repository.file_adapter import FileRepositoryAdapter
from src.utils.paths import get_evaluation_data_path


class FileRepositoryFactory:
    """FileRepositoryAdapter 인스턴스를 생성하는 팩토리"""

    def create_repository(self, dataset_name: str) -> EvaluationRepositoryPort:
        """
        주어진 데이터셋 이름으로 FileRepositoryAdapter를 생성합니다.
        
        Args:
            dataset_name: 데이터셋 이름
            
        Returns:
            EvaluationRepositoryPort: 파일 리포지토리 어댑터
            
        Raises:
            FileNotFoundError: 데이터셋 파일을 찾을 수 없는 경우
        """
        dataset_path = get_evaluation_data_path(dataset_name)
        if not dataset_path:
            raise FileNotFoundError(f"'{dataset_name}' 데이터셋을 찾을 수 없습니다.")
        
        return FileRepositoryAdapter(file_path=str(dataset_path))