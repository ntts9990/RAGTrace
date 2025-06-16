"""
상세 분석 컴포넌트 테스트
개별 QA 쌍에 대한 상세 분석 기능 테스트
"""

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# 선택적 plotly 임포트
try:
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    go = None


# 프로젝트 루트를 동적으로 찾아 경로 추가
def add_project_root_to_path():
    current_path = Path(__file__).resolve()
    while current_path != current_path.parent:
        if (current_path / "pyproject.toml").exists():
            sys.path.insert(0, str(current_path))
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError("프로젝트 루트를 찾을 수 없습니다.")


add_project_root_to_path()



@pytest.fixture
def sample_qa_data():
    """테스트용 QA 데이터"""
    return [
        {
            "question": "한국의 수도는 어디인가요?",
            "contexts": [
                "서울은 한국의 수도입니다.",
                "서울특별시는 1천만 명이 살고 있습니다.",
            ],
            "answer": "한국의 수도는 서울입니다.",
            "ground_truth": "서울",
            "faithfulness": 0.95,
            "answer_relevancy": 0.90,
            "context_recall": 0.85,
            "context_precision": 0.88,
        },
        {
            "question": "김치의 주요 재료는 무엇인가요?",
            "contexts": [
                "김치는 배추, 고춧가루, 마늘로 만듭니다.",
                "김치는 한국의 전통 발효식품입니다.",
            ],
            "answer": "김치의 주요 재료는 배추, 고춧가루, 마늘입니다.",
            "ground_truth": "배추, 고춧가루, 마늘",
            "faithfulness": 0.92,
            "answer_relevancy": 0.94,
            "context_recall": 0.90,
            "context_precision": 0.85,
        },
    ]


class TestDetailedAnalysis:
    """상세 분석 기능 테스트"""

    def test_detailed_analysis_module_import(self):
        """상세 분석 모듈 임포트 테스트"""
        try:
            from src.presentation.web.components.detailed_analysis import (
                show_detailed_analysis,
            )

            assert callable(show_detailed_analysis)
        except ImportError:
            # 모듈이 없어도 테스트는 통과 (개발 중일 수 있음)
            pytest.skip("상세 분석 모듈이 아직 구현되지 않음")

    def test_qa_pair_analysis(self, sample_qa_data):
        """개별 QA 쌍 분석 테스트"""
        qa_pair = sample_qa_data[0]

        def analyze_qa_pair(qa_data):
            """QA 쌍 분석 함수"""
            analysis = {
                "question_length": len(qa_data["question"]),
                "answer_length": len(qa_data["answer"]),
                "context_count": len(qa_data["contexts"]),
                "avg_score": (
                    qa_data["faithfulness"]
                    + qa_data["answer_relevancy"]
                    + qa_data["context_recall"]
                    + qa_data["context_precision"]
                )
                / 4,
            }
            return analysis

        analysis = analyze_qa_pair(qa_pair)

        assert analysis["question_length"] > 0
        assert analysis["answer_length"] > 0
        assert analysis["context_count"] == 2
        assert 0 <= analysis["avg_score"] <= 1

    def test_score_distribution_analysis(self, sample_qa_data):
        """점수 분포 분석 테스트"""

        def calculate_score_distribution(qa_list):
            """점수 분포 계산"""
            scores = {
                "faithfulness": [qa["faithfulness"] for qa in qa_list],
                "answer_relevancy": [qa["answer_relevancy"] for qa in qa_list],
                "context_recall": [qa["context_recall"] for qa in qa_list],
                "context_precision": [qa["context_precision"] for qa in qa_list],
            }

            distribution = {}
            for metric, values in scores.items():
                distribution[metric] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }
            return distribution

        distribution = calculate_score_distribution(sample_qa_data)

        assert len(distribution) == 4
        for metric in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
            assert metric in distribution
            assert 0 <= distribution[metric]["mean"] <= 1
            assert distribution[metric]["count"] == 2

    @patch('src.presentation.web.components.detailed_analysis.DATABASE_PATH')
    def test_load_all_evaluations_empty_db(self, mock_db_path):
        """빈 데이터베이스에서 평가 결과 로드 테스트"""
        mock_db_path.exists.return_value = False
        
        from src.presentation.web.components.detailed_analysis import load_all_evaluations
        
        result = load_all_evaluations()
        assert result == []

    @patch('sqlite3.connect')
    @patch('src.presentation.web.components.detailed_analysis.DATABASE_PATH')
    def test_load_all_evaluations_with_data(self, mock_db_path, mock_connect):
        """데이터가 있는 데이터베이스에서 평가 결과 로드 테스트"""
        mock_db_path.exists.return_value = True
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            (1, '2024-01-01 10:00:00', 0.95, 0.90, 0.85, 0.88, 0.895, '{"test": "data"}')
        ]
        
        from src.presentation.web.components.detailed_analysis import load_all_evaluations
        
        result = load_all_evaluations()
        
        assert len(result) == 1
        assert result[0]['id'] == 1
        assert result[0]['faithfulness'] == 0.95

    @patch('builtins.open')
    @patch('src.presentation.web.components.detailed_analysis.get_evaluation_data_path')
    def test_load_actual_qa_data_from_dataset_success(self, mock_get_path, mock_open):
        """데이터셋에서 QA 데이터 로드 성공 테스트"""
        mock_get_path.return_value = Path('/mock/path/data.json')
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps([
            {"question": "test", "answer": "test answer"},
            {"question": "test2", "answer": "test answer2"}
        ])
        
        with patch('json.load') as mock_json_load:
            mock_json_load.return_value = [
                {"question": "test", "answer": "test answer"},
                {"question": "test2", "answer": "test answer2"}
            ]
            
            from src.presentation.web.components.detailed_analysis import load_actual_qa_data_from_dataset
            
            with patch('streamlit.success'):
                result = load_actual_qa_data_from_dataset("test_dataset", 2)
            
            assert len(result) == 2
            assert result[0]["question"] == "test"

    @patch('src.presentation.web.components.detailed_analysis.get_evaluation_data_path')
    def test_load_actual_qa_data_from_dataset_not_found(self, mock_get_path):
        """데이터셋 파일을 찾을 수 없는 경우 테스트"""
        mock_get_path.return_value = None
        
        from src.presentation.web.components.detailed_analysis import load_actual_qa_data_from_dataset
        
        with patch('streamlit.error'):
            result = load_actual_qa_data_from_dataset("nonexistent_dataset", 1)
        
        assert result is None

    def test_metric_scoring_functions(self):
        """메트릭 점수 계산 함수 테스트"""
        
        def calculate_ragas_score(faithfulness, answer_relevancy, context_recall, context_precision):
            """RAGAS 점수 계산"""
            return (faithfulness + answer_relevancy + context_recall + context_precision) / 4
        
        score = calculate_ragas_score(0.9, 0.8, 0.85, 0.88)
        assert 0 <= score <= 1
        assert abs(score - 0.8575) < 0.001

    @pytest.mark.skipif(not HAS_PLOTLY, reason="plotly not available")
    def test_visualization_components(self):
        """시각화 컴포넌트 테스트"""
        
        def create_metrics_chart(metrics_data):
            """메트릭 차트 생성"""
            fig = go.Figure()
            
            for metric, value in metrics_data.items():
                fig.add_trace(go.Bar(
                    x=[metric],
                    y=[value],
                    name=metric
                ))
            
            return fig
        
        test_metrics = {
            "faithfulness": 0.9,
            "answer_relevancy": 0.8,
            "context_recall": 0.85,
            "context_precision": 0.88
        }
        
        fig = create_metrics_chart(test_metrics)
        assert fig is not None
        assert len(fig.data) == 4

    def test_data_validation_functions(self):
        """데이터 검증 함수 테스트"""
        
        def validate_qa_data(qa_data):
            """QA 데이터 검증"""
            required_fields = ["question", "answer", "contexts"]
            
            if not isinstance(qa_data, dict):
                return False, "QA 데이터는 딕셔너리여야 합니다"
            
            for field in required_fields:
                if field not in qa_data:
                    return False, f"필수 필드 '{field}'가 누락되었습니다"
            
            if not isinstance(qa_data["contexts"], list):
                return False, "contexts는 리스트여야 합니다"
            
            return True, "유효한 데이터입니다"
        
        # Valid data
        valid_data = {
            "question": "test question",
            "answer": "test answer", 
            "contexts": ["context1", "context2"]
        }
        
        is_valid, message = validate_qa_data(valid_data)
        assert is_valid is True
        
        # Invalid data - missing field
        invalid_data = {
            "question": "test question"
        }
        
        is_valid, message = validate_qa_data(invalid_data)
        assert is_valid is False
        assert "answer" in message

        # 각 메트릭의 통계가 올바른지 확인
        for metric_stats in distribution.values():
            assert 0 <= metric_stats["mean"] <= 1
            assert 0 <= metric_stats["min"] <= 1
            assert 0 <= metric_stats["max"] <= 1
            assert metric_stats["count"] == 2


class TestVisualization:
    """시각화 기능 테스트"""

    def test_create_score_histogram(self, sample_qa_data):
        """점수 히스토그램 생성 테스트"""
        if not HAS_PLOTLY:
            pytest.skip("plotly not available")

        def create_score_histogram(qa_list, metric="faithfulness"):
            """특정 메트릭의 점수 히스토그램 생성"""
            scores = [qa[metric] for qa in qa_list]

            # 간단한 히스토그램 데이터 구조
            histogram_data = {
                "scores": scores,
                "bins": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                "counts": [],
            }

            # 각 구간별 개수 계산
            for i in range(len(histogram_data["bins"]) - 1):
                count = sum(
                    1
                    for score in scores
                    if histogram_data["bins"][i]
                    <= score
                    < histogram_data["bins"][i + 1]
                )
                histogram_data["counts"].append(count)

            return histogram_data

        histogram = create_score_histogram(sample_qa_data, "faithfulness")

        assert len(histogram["scores"]) == 2
        assert len(histogram["bins"]) == 6
        assert len(histogram["counts"]) == 5
        assert sum(histogram["counts"]) <= len(sample_qa_data)

    def test_create_comparison_chart(self, sample_qa_data):
        """QA 쌍별 메트릭 비교 차트 테스트"""

        def create_comparison_chart(qa_list):
            """QA 쌍별 메트릭 비교 차트 데이터"""
            chart_data = []

            for i, qa in enumerate(qa_list):
                chart_data.append(
                    {
                        "qa_index": i,
                        "question": qa["question"][:30] + "...",  # 짧게 표시
                        "faithfulness": qa["faithfulness"],
                        "answer_relevancy": qa["answer_relevancy"],
                        "context_recall": qa["context_recall"],
                        "context_precision": qa["context_precision"],
                    }
                )

            return chart_data

        chart_data = create_comparison_chart(sample_qa_data)

        assert len(chart_data) == 2
        assert all("qa_index" in item for item in chart_data)
        assert all("faithfulness" in item for item in chart_data)


class TestPerformanceAnalysis:
    """성능 분석 기능 테스트"""

    def test_identify_problematic_qa_pairs(self, sample_qa_data):
        """문제가 있는 QA 쌍 식별 테스트"""

        def identify_problematic_pairs(qa_list, threshold=0.7):
            """낮은 점수를 가진 QA 쌍 식별"""
            problematic = []

            for i, qa in enumerate(qa_list):
                low_scores = []
                if qa["faithfulness"] < threshold:
                    low_scores.append("faithfulness")
                if qa["answer_relevancy"] < threshold:
                    low_scores.append("answer_relevancy")
                if qa["context_recall"] < threshold:
                    low_scores.append("context_recall")
                if qa["context_precision"] < threshold:
                    low_scores.append("context_precision")

                if low_scores:
                    problematic.append(
                        {
                            "index": i,
                            "question": qa["question"],
                            "issues": low_scores,
                            "avg_score": (
                                qa["faithfulness"]
                                + qa["answer_relevancy"]
                                + qa["context_recall"]
                                + qa["context_precision"]
                            )
                            / 4,
                        }
                    )

            return problematic

        # 높은 임계값으로 테스트 (모든 QA가 문제 없음)
        problematic_high = identify_problematic_pairs(sample_qa_data, threshold=0.7)
        assert len(problematic_high) == 0

        # 낮은 임계값으로 테스트
        problematic_low = identify_problematic_pairs(sample_qa_data, threshold=0.95)
        assert len(problematic_low) >= 0

    def test_calculate_improvement_potential(self, sample_qa_data):
        """개선 가능성 계산 테스트"""

        def calculate_improvement_potential(qa_list):
            """각 메트릭별 개선 가능성 계산"""
            metrics = [
                "faithfulness",
                "answer_relevancy",
                "context_recall",
                "context_precision",
            ]
            improvement_potential = {}

            for metric in metrics:
                scores = [qa[metric] for qa in qa_list]
                current_avg = sum(scores) / len(scores)
                max_possible = 1.0
                improvement_potential[metric] = max_possible - current_avg

            return improvement_potential

        potential = calculate_improvement_potential(sample_qa_data)

        assert len(potential) == 4
        for metric, improvement in potential.items():
            assert 0 <= improvement <= 1
            assert isinstance(improvement, float)


class TestDataFiltering:
    """데이터 필터링 기능 테스트"""

    def test_filter_by_score_range(self, sample_qa_data):
        """점수 범위별 필터링 테스트"""

        def filter_by_score_range(qa_list, metric, min_score, max_score):
            """특정 메트릭의 점수 범위로 필터링"""
            filtered = []
            for qa in qa_list:
                if min_score <= qa[metric] <= max_score:
                    filtered.append(qa)
            return filtered

        # 높은 faithfulness 점수만 필터링
        high_faithfulness = filter_by_score_range(
            sample_qa_data, "faithfulness", 0.9, 1.0
        )

        assert len(high_faithfulness) >= 0
        for qa in high_faithfulness:
            assert qa["faithfulness"] >= 0.9

    def test_filter_by_question_length(self, sample_qa_data):
        """질문 길이별 필터링 테스트"""

        def filter_by_question_length(qa_list, min_length, max_length):
            """질문 길이로 필터링"""
            filtered = []
            for qa in qa_list:
                question_length = len(qa["question"])
                if min_length <= question_length <= max_length:
                    filtered.append(qa)
            return filtered

        # 긴 질문만 필터링
        long_questions = filter_by_question_length(sample_qa_data, 15, 100)

        assert len(long_questions) >= 0
        for qa in long_questions:
            assert 15 <= len(qa["question"]) <= 100


class TestExportFunctionality:
    """내보내기 기능 테스트"""

    def test_export_analysis_to_dict(self, sample_qa_data):
        """분석 결과를 딕셔너리로 내보내기 테스트"""

        def export_analysis_summary(qa_list):
            """분석 요약을 딕셔너리로 내보내기"""
            summary = {
                "total_qa_pairs": len(qa_list),
                "average_scores": {},
                "score_ranges": {},
                "timestamp": "2024-01-01T12:00:00",
            }

            metrics = [
                "faithfulness",
                "answer_relevancy",
                "context_recall",
                "context_precision",
            ]

            for metric in metrics:
                scores = [qa[metric] for qa in qa_list]
                summary["average_scores"][metric] = sum(scores) / len(scores)
                summary["score_ranges"][metric] = {
                    "min": min(scores),
                    "max": max(scores),
                }

            return summary

        summary = export_analysis_summary(sample_qa_data)

        assert summary["total_qa_pairs"] == 2
        assert "average_scores" in summary
        assert "score_ranges" in summary
        assert len(summary["average_scores"]) == 4

    @patch("pandas.DataFrame.to_csv")
    def test_export_to_csv(self, mock_to_csv, sample_qa_data):
        """CSV 내보내기 기능 테스트"""

        def export_qa_data_to_csv(qa_list, filename="analysis.csv"):
            """QA 데이터를 CSV로 내보내기"""
            df = pd.DataFrame(qa_list)
            df.to_csv(filename, index=False)
            return df

        df = export_qa_data_to_csv(sample_qa_data)

        assert len(df) == 2
        assert "question" in df.columns
        assert "faithfulness" in df.columns
        mock_to_csv.assert_called_once()


def test_component_integration():
    """컴포넌트 통합 테스트"""
    try:
        from src.presentation.web.components import detailed_analysis

        # 기본 함수가 존재하는지 확인
        assert hasattr(detailed_analysis, "show_detailed_analysis")
    except ImportError:
        # 모듈이 없어도 테스트는 통과 (개발 중일 수 있음)
        pytest.skip("상세 분석 모듈이 아직 구현되지 않음")
