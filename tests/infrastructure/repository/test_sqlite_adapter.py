"""SQLite 어댑터 테스트"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.repository.sqlite_adapter import SQLiteAdapter


@pytest.fixture
def temp_db_path():
    """임시 데이터베이스 경로 생성"""
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir) / "test_evaluations.db"


@pytest.fixture
def sqlite_adapter(temp_db_path):
    """테스트용 SQLite 어댑터"""
    return SQLiteAdapter(temp_db_path)


@pytest.fixture
def sample_evaluation_data():
    """샘플 평가 데이터"""
    return {
        "timestamp": "2025-01-01T10:00:00",
        "faithfulness": 0.85,
        "answer_relevancy": 0.92,
        "context_recall": 0.78,
        "context_precision": 0.88,
        "ragas_score": 0.86,
        "metadata": {"model": "gemini-2.5-flash", "dataset": "evaluation_data.json"},
        "individual_scores": [
            {"faithfulness": 0.9, "answer_relevancy": 0.95},
            {"faithfulness": 0.8, "answer_relevancy": 0.89},
        ],
    }


class TestSQLiteAdapterInitialization:
    """SQLite 어댑터 초기화 테스트"""

    def test_init_with_custom_path(self, temp_db_path):
        """커스텀 경로로 초기화 테스트"""
        adapter = SQLiteAdapter(temp_db_path)
        assert adapter.db_path == temp_db_path
        assert temp_db_path.exists()

    def test_init_with_default_path(self):
        """기본 경로로 초기화 테스트"""
        with patch(
            "src.infrastructure.repository.sqlite_adapter.DATABASE_PATH"
        ) as mock_path:
            mock_path.parent = MagicMock()
            adapter = SQLiteAdapter()
            assert adapter.db_path == mock_path

    def test_database_table_creation(self, sqlite_adapter, temp_db_path):
        """데이터베이스 테이블 생성 확인"""
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()

        # 테이블 존재 확인
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='evaluations'
        """
        )
        table = cursor.fetchone()
        conn.close()

        assert table is not None
        assert table[0] == "evaluations"

    def test_database_schema(self, sqlite_adapter, temp_db_path):
        """데이터베이스 스키마 확인"""
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(evaluations)")
        columns = cursor.fetchall()
        conn.close()

        expected_columns = {
            "id",
            "timestamp",
            "faithfulness",
            "answer_relevancy",
            "context_recall",
            "context_precision",
            "ragas_score",
            "raw_data",
        }
        actual_columns = {col[1] for col in columns}

        assert actual_columns == expected_columns


class TestSQLiteAdapterSaveEvaluation:
    """평가 결과 저장 테스트"""

    def test_save_evaluation_success(self, sqlite_adapter, sample_evaluation_data):
        """평가 결과 저장 성공 테스트"""
        evaluation_id = sqlite_adapter.save_evaluation(sample_evaluation_data)

        assert isinstance(evaluation_id, int)
        assert evaluation_id > 0

    def test_save_evaluation_with_auto_timestamp(self, sqlite_adapter):
        """타임스탬프 자동 생성 테스트"""
        data = {"faithfulness": 0.85, "answer_relevancy": 0.92}

        evaluation_id = sqlite_adapter.save_evaluation(data)
        saved_data = sqlite_adapter.get_evaluation(evaluation_id)

        assert saved_data["timestamp"] is not None
        # 타임스탬프가 현재 시간 근처인지 확인
        saved_time = datetime.fromisoformat(saved_data["timestamp"])
        now = datetime.now()
        time_diff = abs((now - saved_time).total_seconds())
        assert time_diff < 10  # 10초 이내

    def test_save_evaluation_with_none_values(self, sqlite_adapter):
        """None 값 포함 데이터 저장 테스트"""
        data = {"faithfulness": None, "answer_relevancy": 0.85, "context_recall": None}

        evaluation_id = sqlite_adapter.save_evaluation(data)
        saved_data = sqlite_adapter.get_evaluation(evaluation_id)

        assert saved_data["faithfulness"] is None
        assert saved_data["answer_relevancy"] == 0.85
        assert saved_data["context_recall"] is None

    def test_save_evaluation_with_complex_raw_data(self, sqlite_adapter):
        """복잡한 raw_data 저장 테스트"""
        data = {
            "faithfulness": 0.85,
            "complex_data": {
                "nested": {"array": [1, 2, 3]},
                "korean": "한글 테스트",
                "unicode": "🎯📊✅",
            },
        }

        evaluation_id = sqlite_adapter.save_evaluation(data)
        saved_data = sqlite_adapter.get_evaluation(evaluation_id)

        raw_data = saved_data["raw_data"]
        assert raw_data["complex_data"]["nested"]["array"] == [1, 2, 3]
        assert raw_data["complex_data"]["korean"] == "한글 테스트"
        assert raw_data["complex_data"]["unicode"] == "🎯📊✅"


class TestSQLiteAdapterGetEvaluation:
    """평가 결과 조회 테스트"""

    def test_get_evaluation_success(self, sqlite_adapter, sample_evaluation_data):
        """평가 결과 조회 성공 테스트"""
        evaluation_id = sqlite_adapter.save_evaluation(sample_evaluation_data)
        retrieved_data = sqlite_adapter.get_evaluation(evaluation_id)

        assert retrieved_data["id"] == evaluation_id
        assert retrieved_data["faithfulness"] == 0.85
        assert retrieved_data["answer_relevancy"] == 0.92
        assert retrieved_data["raw_data"]["metadata"]["model"] == "gemini-2.5-flash"

    def test_get_evaluation_not_found(self, sqlite_adapter):
        """존재하지 않는 평가 ID 조회 테스트"""
        result = sqlite_adapter.get_evaluation(999999)
        assert result is None

    def test_get_evaluation_data_types(self, sqlite_adapter, sample_evaluation_data):
        """조회된 데이터의 타입 확인 테스트"""
        evaluation_id = sqlite_adapter.save_evaluation(sample_evaluation_data)
        retrieved_data = sqlite_adapter.get_evaluation(evaluation_id)

        assert isinstance(retrieved_data["id"], int)
        assert isinstance(retrieved_data["timestamp"], str)
        assert isinstance(retrieved_data["faithfulness"], float)
        assert isinstance(retrieved_data["raw_data"], dict)


class TestSQLiteAdapterGetAllEvaluations:
    """모든 평가 결과 조회 테스트"""

    def test_get_all_evaluations_empty(self, sqlite_adapter):
        """빈 데이터베이스에서 조회 테스트"""
        results = sqlite_adapter.get_all_evaluations()
        assert results == []

    def test_get_all_evaluations_multiple(self, sqlite_adapter):
        """여러 평가 결과 조회 테스트"""
        # 3개 평가 결과 저장
        data1 = {"faithfulness": 0.8, "timestamp": "2025-01-01T10:00:00"}
        data2 = {"faithfulness": 0.9, "timestamp": "2025-01-01T11:00:00"}
        data3 = {"faithfulness": 0.7, "timestamp": "2025-01-01T12:00:00"}

        id1 = sqlite_adapter.save_evaluation(data1)
        id2 = sqlite_adapter.save_evaluation(data2)
        id3 = sqlite_adapter.save_evaluation(data3)

        results = sqlite_adapter.get_all_evaluations()

        assert len(results) == 3
        # 최신 순으로 정렬되어 있는지 확인
        assert results[0]["id"] == id3  # 가장 최신
        assert results[1]["id"] == id2
        assert results[2]["id"] == id1  # 가장 오래된

    def test_get_all_evaluations_with_limit(self, sqlite_adapter):
        """제한된 개수로 조회 테스트"""
        # 5개 평가 결과 저장
        for i in range(5):
            sqlite_adapter.save_evaluation({"faithfulness": 0.8 + i * 0.02})

        # 3개만 조회
        results = sqlite_adapter.get_all_evaluations(limit=3)
        assert len(results) == 3

    def test_get_all_evaluations_ordering(self, sqlite_adapter):
        """시간순 정렬 확인 테스트"""
        older_data = {"faithfulness": 0.8, "timestamp": "2025-01-01T10:00:00"}
        newer_data = {"faithfulness": 0.9, "timestamp": "2025-01-01T11:00:00"}

        sqlite_adapter.save_evaluation(older_data)
        sqlite_adapter.save_evaluation(newer_data)

        results = sqlite_adapter.get_all_evaluations()

        # 최신 것이 먼저 와야 함
        assert results[0]["timestamp"] == "2025-01-01T11:00:00"
        assert results[1]["timestamp"] == "2025-01-01T10:00:00"


class TestSQLiteAdapterDeleteEvaluation:
    """평가 결과 삭제 테스트"""

    def test_delete_evaluation_success(self, sqlite_adapter, sample_evaluation_data):
        """평가 결과 삭제 성공 테스트"""
        evaluation_id = sqlite_adapter.save_evaluation(sample_evaluation_data)

        # 삭제 전 존재 확인
        assert sqlite_adapter.get_evaluation(evaluation_id) is not None

        # 삭제 실행
        success = sqlite_adapter.delete_evaluation(evaluation_id)
        assert success is True

        # 삭제 후 없음 확인
        assert sqlite_adapter.get_evaluation(evaluation_id) is None

    def test_delete_evaluation_not_found(self, sqlite_adapter):
        """존재하지 않는 평가 삭제 테스트"""
        success = sqlite_adapter.delete_evaluation(999999)
        assert success is False


class TestSQLiteAdapterStatistics:
    """통계 기능 테스트"""

    def test_get_statistics_empty_database(self, sqlite_adapter):
        """빈 데이터베이스 통계 테스트"""
        stats = sqlite_adapter.get_statistics()

        assert stats["total_evaluations"] == 0
        assert stats["average_scores"]["faithfulness"] == 0
        assert stats["latest_evaluation"] is None

    def test_get_statistics_with_data(self, sqlite_adapter):
        """데이터가 있는 경우 통계 테스트"""
        # 테스트 데이터 저장
        data1 = {
            "faithfulness": 0.8,
            "answer_relevancy": 0.9,
            "context_recall": 0.7,
            "context_precision": 0.85,
            "ragas_score": 0.82,
            "timestamp": "2025-01-01T10:00:00",
        }
        data2 = {
            "faithfulness": 0.9,
            "answer_relevancy": 0.8,
            "context_recall": 0.9,
            "context_precision": 0.75,
            "ragas_score": 0.84,
            "timestamp": "2025-01-01T11:00:00",
        }

        sqlite_adapter.save_evaluation(data1)
        sqlite_adapter.save_evaluation(data2)

        stats = sqlite_adapter.get_statistics()

        assert stats["total_evaluations"] == 2
        assert (
            abs(stats["average_scores"]["faithfulness"] - 0.85) < 0.01
        )  # (0.8 + 0.9) / 2
        assert (
            abs(stats["average_scores"]["answer_relevancy"] - 0.85) < 0.01
        )  # (0.9 + 0.8) / 2
        assert stats["latest_evaluation"] == "2025-01-01T11:00:00"

    def test_get_statistics_with_none_values(self, sqlite_adapter):
        """None 값이 포함된 데이터의 통계 테스트"""
        data1 = {"faithfulness": 0.8, "answer_relevancy": None}
        data2 = {"faithfulness": None, "answer_relevancy": 0.9}
        data3 = {"faithfulness": 0.9, "answer_relevancy": 0.8}

        sqlite_adapter.save_evaluation(data1)
        sqlite_adapter.save_evaluation(data2)
        sqlite_adapter.save_evaluation(data3)

        stats = sqlite_adapter.get_statistics()

        assert stats["total_evaluations"] == 3
        # None 값은 평균 계산에서 제외됨
        assert (
            abs(stats["average_scores"]["faithfulness"] - 0.85) < 0.01
        )  # (0.8 + 0.9) / 2


class TestSQLiteAdapterUtilityMethods:
    """유틸리티 메서드 테스트"""

    def test_clear_all_data(self, sqlite_adapter, sample_evaluation_data):
        """모든 데이터 삭제 테스트"""
        # 데이터 추가
        sqlite_adapter.save_evaluation(sample_evaluation_data)
        sqlite_adapter.save_evaluation(sample_evaluation_data)

        # 데이터가 있는지 확인
        assert len(sqlite_adapter.get_all_evaluations()) == 2

        # 모든 데이터 삭제
        sqlite_adapter.clear_all_data()

        # 데이터가 삭제되었는지 확인
        assert len(sqlite_adapter.get_all_evaluations()) == 0


class TestSQLiteAdapterErrorHandling:
    """에러 처리 테스트"""

    def test_invalid_database_path(self):
        """잘못된 데이터베이스 경로 테스트"""
        invalid_path = Path("/invalid/readonly/path/test.db")

        # 읽기 전용 경로에 DB 생성 시도 시 에러 발생 확인
        with pytest.raises((sqlite3.OperationalError, PermissionError, OSError)):
            adapter = SQLiteAdapter(invalid_path)
            adapter.save_evaluation({"faithfulness": 0.8})

    def test_corrupted_json_handling(self, sqlite_adapter, temp_db_path):
        """손상된 JSON 데이터 처리 테스트"""
        # 직접 DB에 잘못된 JSON 삽입
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO evaluations 
            (timestamp, faithfulness, raw_data)
            VALUES (?, ?, ?)
        """,
            ("2025-01-01T10:00:00", 0.8, "invalid json"),
        )
        conn.commit()
        conn.close()

        # 조회 시 JSON 파싱 오류 발생 확인
        with pytest.raises(json.JSONDecodeError):
            sqlite_adapter.get_evaluation(1)


# 통합 테스트
class TestSQLiteAdapterIntegration:
    """SQLite 어댑터 통합 테스트"""

    def test_full_lifecycle(self, sqlite_adapter):
        """전체 라이프사이클 테스트"""
        # 1. 데이터 저장
        evaluation_data = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.92,
            "metadata": {"test": True},
        }

        evaluation_id = sqlite_adapter.save_evaluation(evaluation_data)

        # 2. 개별 조회
        retrieved = sqlite_adapter.get_evaluation(evaluation_id)
        assert retrieved["faithfulness"] == 0.85
        assert retrieved["raw_data"]["metadata"]["test"] is True

        # 3. 전체 조회
        all_evaluations = sqlite_adapter.get_all_evaluations()
        assert len(all_evaluations) == 1
        assert all_evaluations[0]["id"] == evaluation_id

        # 4. 통계 확인
        stats = sqlite_adapter.get_statistics()
        assert stats["total_evaluations"] == 1
        assert stats["average_scores"]["faithfulness"] == 0.85

        # 5. 삭제
        success = sqlite_adapter.delete_evaluation(evaluation_id)
        assert success is True

        # 6. 삭제 확인
        assert sqlite_adapter.get_evaluation(evaluation_id) is None
        assert len(sqlite_adapter.get_all_evaluations()) == 0

    def test_concurrent_operations(self, sqlite_adapter):
        """동시 작업 시뮬레이션 테스트"""
        evaluation_ids = []

        # 여러 평가 결과를 빠르게 저장
        for i in range(10):
            data = {
                "faithfulness": 0.8 + i * 0.01,
                "timestamp": f"2025-01-01T10:{i:02d}:00",
            }
            evaluation_id = sqlite_adapter.save_evaluation(data)
            evaluation_ids.append(evaluation_id)

        # 모든 데이터가 정상적으로 저장되었는지 확인
        all_evaluations = sqlite_adapter.get_all_evaluations()
        assert len(all_evaluations) == 10

        # 각 평가 결과를 개별적으로 조회 가능한지 확인
        for eval_id in evaluation_ids:
            result = sqlite_adapter.get_evaluation(eval_id)
            assert result is not None
            assert result["id"] == eval_id
