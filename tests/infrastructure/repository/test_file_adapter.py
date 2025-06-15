import json
import pytest
from src.infrastructure.repository import FileRepositoryAdapter
from src.domain.entities import EvaluationData

@pytest.fixture
def temp_json_file(tmp_path):
    """테스트용 임시 JSON 파일을 생성하는 pytest fixture"""
    data = [
        {
            "question": "q1",
            "contexts": ["c1"],
            "answer": "a1",
            "ground_truth": "g1"
        },
        {
            "question": "q2",
            "contexts": ["c2-1", "c2-2"],
            "answer": "a2",
            "ground_truth": "g2"
        }
    ]
    file_path = tmp_path / "test_data.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    return str(file_path)

def test_file_repository_load_data_success(temp_json_file):
    """파일 리포지토리가 JSON 파일을 성공적으로 로드하는지 테스트"""
    # Arrange
    adapter = FileRepositoryAdapter(file_path=temp_json_file)

    # Act
    loaded_data = adapter.load_data()

    # Assert
    assert len(loaded_data) == 2
    assert isinstance(loaded_data[0], EvaluationData)
    assert loaded_data[0].question == "q1"
    assert loaded_data[1].contexts == ["c2-1", "c2-2"]

def test_file_repository_file_not_found():
    """파일이 존재하지 않을 때 빈 리스트를 반환하는지 테스트"""
    # Arrange
    adapter = FileRepositoryAdapter(file_path="non_existent_file.json")

    # Act
    loaded_data = adapter.load_data()

    # Assert
    assert loaded_data == []

def test_file_repository_invalid_json(tmp_path):
    """JSON 형식이 잘못되었을 때 빈 리스트를 반환하는지 테스트"""
    # Arrange
    invalid_json_path = tmp_path / "invalid.json"
    with open(invalid_json_path, 'w', encoding='utf-8') as f:
        f.write("{'invalid': 'json'}")  # Invalid JSON format
    
    adapter = FileRepositoryAdapter(file_path=str(invalid_json_path))

    # Act
    loaded_data = adapter.load_data()

    # Assert
    assert loaded_data == [] 