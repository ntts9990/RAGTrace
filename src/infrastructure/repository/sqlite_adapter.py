"""SQLite 데이터베이스 어댑터"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.paths import DATABASE_PATH, ensure_directory_exists


class SQLiteAdapter:
    """SQLite 데이터베이스 어댑터

    평가 결과를 SQLite 데이터베이스에 저장하고 조회하는 기능을 제공합니다.
    """

    def __init__(self, db_path: Path | None = None):
        """SQLite 어댑터 초기화

        Args:
            db_path: 데이터베이스 파일 경로 (None이면 기본 경로 사용)
        """
        self.db_path = db_path or DATABASE_PATH
        self._init_db()

    def _init_db(self):
        """데이터베이스 초기화"""
        # 디렉토리 생성
        ensure_directory_exists(self.db_path.parent)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                faithfulness REAL,
                answer_relevancy REAL,
                context_recall REAL,
                context_precision REAL,
                ragas_score REAL,
                raw_data TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def save_evaluation(self, evaluation_data: dict[str, Any]) -> int:
        """평가 결과 저장

        Args:
            evaluation_data: 평가 결과 데이터

        Returns:
            int: 저장된 레코드의 ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 현재 시간을 타임스탬프로 사용 (데이터에 없는 경우)
        timestamp = evaluation_data.get("timestamp", datetime.now().isoformat())

        cursor.execute(
            """
            INSERT INTO evaluations 
            (timestamp, faithfulness, answer_relevancy, context_recall, 
             context_precision, ragas_score, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                timestamp,
                evaluation_data.get("faithfulness"),
                evaluation_data.get("answer_relevancy"),
                evaluation_data.get("context_recall"),
                evaluation_data.get("context_precision"),
                evaluation_data.get("ragas_score"),
                json.dumps(evaluation_data, ensure_ascii=False),
            ),
        )

        evaluation_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return evaluation_id

    def get_evaluation(self, evaluation_id: int) -> dict[str, Any] | None:
        """특정 평가 결과 조회

        Args:
            evaluation_id: 평가 ID

        Returns:
            평가 결과 데이터 또는 None
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, timestamp, faithfulness, answer_relevancy, 
                   context_recall, context_precision, ragas_score, raw_data
            FROM evaluations 
            WHERE id = ?
        """,
            (evaluation_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "timestamp": row[1],
            "faithfulness": row[2],
            "answer_relevancy": row[3],
            "context_recall": row[4],
            "context_precision": row[5],
            "ragas_score": row[6],
            "raw_data": json.loads(row[7]) if row[7] else None,
        }

    def get_all_evaluations(self, limit: int | None = None) -> list[dict[str, Any]]:
        """모든 평가 결과 조회

        Args:
            limit: 조회할 최대 개수 (None이면 모두 조회)

        Returns:
            평가 결과 데이터 리스트
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        query = """
            SELECT id, timestamp, faithfulness, answer_relevancy, 
                   context_recall, context_precision, ragas_score, raw_data
            FROM evaluations 
            ORDER BY timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        evaluations = []
        for row in rows:
            evaluations.append(
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "faithfulness": row[2],
                    "answer_relevancy": row[3],
                    "context_recall": row[4],
                    "context_precision": row[5],
                    "ragas_score": row[6],
                    "raw_data": json.loads(row[7]) if row[7] else None,
                }
            )

        return evaluations

    def delete_evaluation(self, evaluation_id: int) -> bool:
        """평가 결과 삭제

        Args:
            evaluation_id: 삭제할 평가 ID

        Returns:
            bool: 삭제 성공 여부
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM evaluations WHERE id = ?", (evaluation_id,))
        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()

        return deleted_count > 0

    def get_statistics(self) -> dict[str, Any]:
        """평가 통계 조회

        Returns:
            통계 데이터
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 총 평가 횟수
        cursor.execute("SELECT COUNT(*) FROM evaluations")
        total_count = cursor.fetchone()[0]

        # 평균 점수들
        cursor.execute(
            """
            SELECT 
                AVG(faithfulness) as avg_faithfulness,
                AVG(answer_relevancy) as avg_answer_relevancy,
                AVG(context_recall) as avg_context_recall,
                AVG(context_precision) as avg_context_precision,
                AVG(ragas_score) as avg_ragas_score
            FROM evaluations 
            WHERE faithfulness IS NOT NULL
        """
        )
        avg_row = cursor.fetchone()

        # 최신 평가
        cursor.execute(
            """
            SELECT timestamp 
            FROM evaluations 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        )
        latest_row = cursor.fetchone()

        conn.close()

        return {
            "total_evaluations": total_count,
            "average_scores": {
                "faithfulness": avg_row[0] if avg_row[0] else 0,
                "answer_relevancy": avg_row[1] if avg_row[1] else 0,
                "context_recall": avg_row[2] if avg_row[2] else 0,
                "context_precision": avg_row[3] if avg_row[3] else 0,
                "ragas_score": avg_row[4] if avg_row[4] else 0,
            },
            "latest_evaluation": latest_row[0] if latest_row else None,
        }

    def clear_all_data(self):
        """모든 데이터 삭제 (테스트용)"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM evaluations")
        conn.commit()
        conn.close()
