"""
Database Service

데이터베이스 관련 서비스입니다.
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any

import pandas as pd

from src.utils.paths import DATABASE_PATH
from ..models.evaluation_model import EvaluationResult, EvaluationModel


class DatabaseService:
    """데이터베이스 서비스"""
    
    @staticmethod
    def init_db() -> None:
        """데이터베이스 초기화"""
        db_path = DATABASE_PATH
        db_path.parent.mkdir(exist_ok=True)

        conn = sqlite3.connect(str(db_path))
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
    
    @staticmethod
    def save_evaluation_result(result_dict: Dict[str, Any]) -> None:
        """평가 결과 저장"""
        DatabaseService.init_db()

        conn = sqlite3.connect(str(DATABASE_PATH))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO evaluations (
                timestamp, faithfulness, answer_relevancy, 
                context_recall, context_precision, ragas_score, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now().isoformat(),
                result_dict.get("faithfulness", 0),
                result_dict.get("answer_relevancy", 0),
                result_dict.get("context_recall", 0),
                result_dict.get("context_precision", 0),
                result_dict.get("ragas_score", 0),
                json.dumps(result_dict),
            ),
        )

        conn.commit()
        conn.close()
    
    @staticmethod
    def load_evaluation_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """평가 이력 로드"""
        DatabaseService.init_db()

        conn = sqlite3.connect(str(DATABASE_PATH))

        query = """
            SELECT timestamp, faithfulness, answer_relevancy, 
                   context_recall, context_precision, ragas_score
            FROM evaluations 
            ORDER BY timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df.to_dict("records")
    
    @staticmethod
    def load_latest_result() -> Optional[Dict[str, Any]]:
        """최신 평가 결과 로드"""
        history = DatabaseService.load_evaluation_history(limit=1)
        return history[0] if history else None
    
    @staticmethod
    def get_previous_result() -> Optional[Dict[str, Any]]:
        """이전 평가 결과 반환"""
        history = DatabaseService.load_evaluation_history(limit=2)
        return history[1] if len(history) > 1 else None
    
    @staticmethod
    def get_evaluation_by_index(index: int) -> Optional[Dict[str, Any]]:
        """인덱스로 특정 평가 결과 반환"""
        history = DatabaseService.load_evaluation_history()
        return history[index] if 0 <= index < len(history) else None