"""
Chart Service

차트 생성 관련 서비스입니다.
"""

from typing import List, Dict, Any
import pandas as pd
import plotly.graph_objects as go

from ..models.evaluation_model import EvaluationResult, EvaluationModel


class ChartService:
    """차트 생성 서비스"""
    
    @staticmethod
    def create_radar_chart(result: EvaluationResult) -> go.Figure:
        """레이더 차트 생성"""
        metrics = EvaluationModel.get_metrics_list()
        values = [getattr(result, metric) for metric in metrics]
        labels = EvaluationModel.get_metrics_labels()

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],  # 첫 번째 값을 마지막에 추가하여 차트를 닫음
                theta=labels + [labels[0]],
                fill="toself",
                name="RAGAS 점수",
                line_color="rgb(32, 201, 151)",
            )
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            title="📊 메트릭 균형도",
            height=400,
        )

        return fig
    
    @staticmethod
    def create_bar_chart(result: EvaluationResult) -> go.Figure:
        """바 차트 생성"""
        metrics = EvaluationModel.get_metrics_list()
        values = [getattr(result, metric) for metric in metrics]
        labels = EvaluationModel.get_metrics_labels()

        # 색상 매핑
        colors = [EvaluationModel.get_metric_color(v) for v in values]

        fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color=colors)])

        fig.update_layout(
            title="📊 메트릭별 성능",
            yaxis_title="점수",
            yaxis=dict(range=[0, 1]),
            height=400,
        )

        return fig
    
    @staticmethod
    def create_trend_chart(history: List[Dict[str, Any]]) -> go.Figure:
        """트렌드 차트 생성"""
        if len(history) <= 1:
            return None
        
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        fig = go.Figure()

        metrics = EvaluationModel.get_metrics_list() + ["ragas_score"]
        colors = ["blue", "green", "orange", "red", "purple"]

        for metric, color in zip(metrics, colors, strict=False):
            if metric in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[metric],
                        mode="lines+markers",
                        name=metric.replace("_", " ").title(),
                        line=dict(color=color),
                    )
                )

        fig.update_layout(
            title="📈 평가 점수 트렌드",
            xaxis_title="시간",
            yaxis_title="점수",
            yaxis=dict(range=[0, 1]),
            height=400,
        )

        return fig
    
    @staticmethod
    def create_comparison_chart(eval1: Dict[str, Any], eval2: Dict[str, Any]) -> go.Figure:
        """두 평가 결과 비교 차트"""
        metrics = EvaluationModel.get_metrics_list() + ["ragas_score"]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                name=f'평가 1 ({eval1["timestamp"]})',
                x=metrics,
                y=[eval1.get(m, 0) for m in metrics],
                marker_color="lightblue",
            )
        )

        fig.add_trace(
            go.Bar(
                name=f'평가 2 ({eval2["timestamp"]})',
                x=metrics,
                y=[eval2.get(m, 0) for m in metrics],
                marker_color="darkblue",
            )
        )

        fig.update_layout(
            title="📊 평가 결과 비교", 
            barmode="group", 
            yaxis=dict(range=[0, 1]), 
            height=400
        )

        return fig