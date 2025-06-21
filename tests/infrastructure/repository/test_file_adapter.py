import json
from unittest.mock import mock_open, patch

import pytest

from src.domain.entities.evaluation_data import EvaluationData
from src.domain.exceptions.evaluation_exceptions import InvalidDataFormatError
from src.infrastructure.repository.file_adapter import FileRepositoryAdapter


@pytest.fixture
def temp_json_file(tmp_path):
    """테스트용 임시 JSON 파일을 생성하는 pytest fixture"""
    data = [
        {"question": "q1", "contexts": ["c1"], "answer": "a1", "ground_truth": "g1"},
        {
            "question": "q2",
            "contexts": ["c2-1", "c2-2"],
            "answer": "a2",
            "ground_truth": "g2",
        },
    ]
    file_path = tmp_path / "test_data.json"
    with open(file_path, "w", encoding="utf-8") as f:
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
    """파일이 존재하지 않을 때 InvalidDataFormatError가 발생하는지 테스트"""
    # Arrange
    adapter = FileRepositoryAdapter(file_path="non_existent_file.json")

    # Act & Assert
    with pytest.raises(InvalidDataFormatError):
        adapter.load_data()


def test_file_repository_invalid_json(tmp_path):
    """JSON 형식이 잘못되었을 때 InvalidDataFormatError가 발생하는지 테스트"""
    # Arrange
    invalid_json_path = tmp_path / "invalid.json"
    with open(invalid_json_path, "w", encoding="utf-8") as f:
        f.write("{'invalid': 'json'}")  # Invalid JSON format

    adapter = FileRepositoryAdapter(file_path=str(invalid_json_path))

    # Act & Assert
    with pytest.raises(InvalidDataFormatError):
        adapter.load_data()


class TestFileRepositoryAdapter:
    """FileRepositoryAdapter 테스트"""

    def test_init(self):
        """초기화 테스트"""
        adapter = FileRepositoryAdapter("test.json")
        assert adapter.file_path == "test.json"

    def test_load_data_success(self):
        """데이터 로드 성공 테스트"""
        test_data = [
            {
                "question": "질문1",
                "answer": "답변1",
                "contexts": ["컨텍스트1"],
                "ground_truth": "정답1",
            },
            {
                "question": "질문2",
                "answer": "답변2",
                "contexts": ["컨텍스트2"],
                "ground_truth": "정답2",
            },
        ]

        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            adapter = FileRepositoryAdapter("test.json")
            result = adapter.load_data()

            assert len(result) == 2
            assert all(isinstance(item, EvaluationData) for item in result)
            assert result[0].question == "질문1"
            assert result[1].question == "질문2"

    def test_load_data_file_not_found(self, capsys):
        """파일을 찾을 수 없는 경우 테스트"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            adapter = FileRepositoryAdapter("nonexistent.json")
            result = adapter.load_data()

            assert result == []
            captured = capsys.readouterr()
            assert "오류: 파일을 찾을 수 없습니다" in captured.out

    def test_load_data_json_decode_error(self, capsys):
        """JSON 디코딩 오류 테스트"""
        invalid_json = "{ invalid json }"

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            adapter = FileRepositoryAdapter("invalid.json")
            result = adapter.load_data()

            assert result == []
            captured = capsys.readouterr()
            assert "오류: JSON 파싱 중 오류가 발생했습니다" in captured.out

    def test_load_data_general_exception(self, capsys):
        """일반 예외 처리 테스트"""
        with patch("builtins.open", side_effect=PermissionError("권한 없음")):
            adapter = FileRepositoryAdapter("permission_denied.json")
            result = adapter.load_data()

            assert result == []
            captured = capsys.readouterr()
            assert "데이터 로드 중 예기치 않은 오류 발생" in captured.out
