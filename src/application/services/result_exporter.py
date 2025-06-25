"""
결과 내보내기 서비스

평가 결과를 CSV 파일과 분석 보고서로 내보내는 기능을 제공합니다.
"""

import csv
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd


class ResultExporter:
    """평가 결과 내보내기 서비스"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_to_csv(self, result: Dict[str, Any], filename: Optional[str] = None) -> str:
        """평가 결과를 CSV 파일로 내보내기"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ragas_evaluation_{timestamp}.csv"
        
        csv_path = self.output_dir / filename
        
        # 메타데이터 정보
        metadata = result.get("metadata", {})
        
        # 개별 점수 데이터 준비
        individual_scores = result.get("individual_scores", [])
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            # CSV 헤더 정의
            fieldnames = [
                'item_id', 'faithfulness', 'answer_relevancy', 
                'context_recall', 'context_precision'
            ]
            
            # answer_correctness가 있으면 추가
            if individual_scores and 'answer_correctness' in individual_scores[0]:
                fieldnames.append('answer_correctness')
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # 개별 점수 작성
            for i, scores in enumerate(individual_scores):
                row = {'item_id': i + 1}
                row.update(scores)
                writer.writerow(row)
        
        return str(csv_path)
    
    def export_summary_csv(self, result: Dict[str, Any], filename: Optional[str] = None) -> str:
        """요약 통계를 CSV로 내보내기"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ragas_summary_{timestamp}.csv"
        
        csv_path = self.output_dir / filename
        
        summary_data = []
        
        # 메트릭별 통계 계산
        individual_scores = result.get("individual_scores", [])
        
        if individual_scores:
            # individual_scores가 있는 경우: 상세 통계 계산
            metrics = list(individual_scores[0].keys())
            
            for metric in metrics:
                scores = [item[metric] for item in individual_scores if item[metric] is not None]
                
                if scores:
                    summary_data.append({
                        'metric': metric,
                        'mean': statistics.mean(scores),
                        'median': statistics.median(scores),
                        'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                        'min': min(scores),
                        'max': max(scores),
                        'count': len(scores),
                        'q1': statistics.quantiles(scores, n=4)[0] if len(scores) >= 4 else min(scores),
                        'q3': statistics.quantiles(scores, n=4)[2] if len(scores) >= 4 else max(scores),
                    })
        else:
            # individual_scores가 없는 경우: 전체 메트릭으로 단일 값 통계 생성
            metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
            
            # answer_correctness가 있으면 추가
            if 'answer_correctness' in result:
                metrics.append('answer_correctness')
            
            for metric in metrics:
                value = result.get(metric, 0)
                if value is not None:
                    summary_data.append({
                        'metric': metric,
                        'mean': value,
                        'median': value,
                        'std_dev': 0.0,
                        'min': value,
                        'max': value,
                        'count': 1,
                        'q1': value,
                        'q3': value,
                    })
        
        # 전체 점수 추가
        ragas_score = result.get('ragas_score', 0)
        if ragas_score is not None:
            summary_data.append({
                'metric': 'ragas_score',
                'mean': ragas_score,
                'median': ragas_score,
                'std_dev': 0.0,
                'min': ragas_score,
                'max': ragas_score,
                'count': 1,
                'q1': ragas_score,
                'q3': ragas_score,
            })
        
        # CSV 작성
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['metric', 'mean', 'median', 'std_dev', 'min', 'max', 'count', 'q1', 'q3']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_data)
        
        return str(csv_path)
    
    def generate_analysis_report(self, result: Dict[str, Any], filename: Optional[str] = None) -> str:
        """상세 분석 보고서 생성"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ragas_analysis_report_{timestamp}.md"
        
        report_path = self.output_dir / filename
        
        metadata = result.get("metadata", {})
        individual_scores = result.get("individual_scores", [])
        
        # 보고서 내용 생성
        report_content = self._generate_report_content(result, metadata, individual_scores)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(report_path)
    
    def _generate_report_content(self, result: Dict[str, Any], metadata: Dict[str, Any], individual_scores: List[Dict]) -> str:
        """보고서 내용 생성"""
        
        # 기초 통계 계산
        stats = self._calculate_statistics(individual_scores)
        
        # 성능 등급 계산
        performance_grades = self._calculate_performance_grades(result)
        
        # 메타데이터 정보 추출 및 정리
        evaluation_id = self._extract_evaluation_id(metadata)
        timestamp = self._extract_timestamp(metadata)
        llm_model = self._extract_llm_model(metadata)
        dataset_size = self._extract_dataset_size(metadata, individual_scores)
        duration_info = self._extract_duration_info(metadata, individual_scores)
        
        # 보고서 템플릿
        content = f"""# RAGTrace 평가 결과 분석 보고서

## 📊 평가 개요

**평가 ID**: {evaluation_id}  
**평가 일시**: {timestamp}  
**LLM 모델**: {llm_model}  
**임베딩 모델**: {self._extract_embedding_model(metadata)}  
**데이터셋**: {metadata.get('dataset', 'N/A')}  
**데이터셋 크기**: {dataset_size}개 문항  
**총 평가 시간**: {duration_info['total_minutes']:.1f}분  
**평균 문항당 시간**: {duration_info['avg_seconds']:.1f}초  

## 🎯 전체 성능 요약

**RAGAS 종합 점수**: {result.get('ragas_score', 0):.3f} / 1.000

### 메트릭별 점수
{self._format_metric_scores(result)}

### 성능 등급 평가
{self._format_performance_grades(performance_grades)}

## 📈 기초 통계 분석

{self._format_statistics_table(stats)}

## 🔍 상세 분석

### 1. Faithfulness (답변 충실도)
- **현재 점수**: {result.get('faithfulness', 0):.3f}
- **해석**: {self._interpret_faithfulness(result.get('faithfulness', 0))}
{self._format_metric_analysis('faithfulness', stats.get('faithfulness', {}))}

### 2. Answer Relevancy (답변 관련성)
- **현재 점수**: {result.get('answer_relevancy', 0):.3f}
- **해석**: {self._interpret_answer_relevancy(result.get('answer_relevancy', 0))}
{self._format_metric_analysis('answer_relevancy', stats.get('answer_relevancy', {}))}

### 3. Context Recall (컨텍스트 재현율)
- **현재 점수**: {result.get('context_recall', 0):.3f}
- **해석**: {self._interpret_context_recall(result.get('context_recall', 0))}
{self._format_metric_analysis('context_recall', stats.get('context_recall', {}))}

### 4. Context Precision (컨텍스트 정밀도)
- **현재 점수**: {result.get('context_precision', 0):.3f}
- **해석**: {self._interpret_context_precision(result.get('context_precision', 0))}
{self._format_metric_analysis('context_precision', stats.get('context_precision', {}))}

{self._format_answer_correctness_section(result, stats)}

## 📋 개선 권장사항

{self._generate_recommendations(result, stats)}

## 📊 데이터 품질 평가

{self._evaluate_data_quality(individual_scores)}

---

*이 보고서는 RAGTrace에 의해 자동 생성되었습니다.*  
*생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _calculate_statistics(self, individual_scores: List[Dict]) -> Dict[str, Dict]:
        """메트릭별 기초 통계 계산"""
        if not individual_scores:
            return {}
        
        metrics = list(individual_scores[0].keys())
        stats = {}
        
        for metric in metrics:
            scores = [item[metric] for item in individual_scores if item[metric] is not None]
            
            if scores:
                stats[metric] = {
                    'mean': statistics.mean(scores),
                    'median': statistics.median(scores),
                    'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores),
                    'range': max(scores) - min(scores),
                    'cv': (statistics.stdev(scores) / statistics.mean(scores)) if len(scores) > 1 and statistics.mean(scores) > 0 else 0.0,
                }
                
                # 사분위수 계산
                if len(scores) >= 4:
                    quantiles = statistics.quantiles(scores, n=4)
                    stats[metric]['q1'] = quantiles[0]
                    stats[metric]['q3'] = quantiles[2]
                    stats[metric]['iqr'] = quantiles[2] - quantiles[0]
                else:
                    stats[metric]['q1'] = min(scores)
                    stats[metric]['q3'] = max(scores)
                    stats[metric]['iqr'] = stats[metric]['range']
        
        return stats
    
    def _calculate_performance_grades(self, result: Dict[str, Any]) -> Dict[str, str]:
        """성능 등급 계산"""
        grades = {}
        
        metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
        if 'answer_correctness' in result:
            metrics.append('answer_correctness')
        
        for metric in metrics:
            score = result.get(metric, 0)
            if score >= 0.9:
                grades[metric] = "A+ (우수)"
            elif score >= 0.8:
                grades[metric] = "A (좋음)"
            elif score >= 0.7:
                grades[metric] = "B (보통)"
            elif score >= 0.6:
                grades[metric] = "C (개선 필요)"
            else:
                grades[metric] = "D (크게 개선 필요)"
        
        # 전체 점수 등급
        ragas_score = result.get('ragas_score', 0)
        if ragas_score >= 0.9:
            grades['overall'] = "A+ (우수)"
        elif ragas_score >= 0.8:
            grades['overall'] = "A (좋음)"
        elif ragas_score >= 0.7:
            grades['overall'] = "B (보통)"
        elif ragas_score >= 0.6:
            grades['overall'] = "C (개선 필요)"
        else:
            grades['overall'] = "D (크게 개선 필요)"
        
        return grades
    
    def _format_metric_scores(self, result: Dict[str, Any]) -> str:
        """메트릭 점수 포맷팅"""
        lines = []
        lines.append(f"- **Faithfulness**: {result.get('faithfulness', 0):.3f}")
        lines.append(f"- **Answer Relevancy**: {result.get('answer_relevancy', 0):.3f}")
        lines.append(f"- **Context Recall**: {result.get('context_recall', 0):.3f}")
        lines.append(f"- **Context Precision**: {result.get('context_precision', 0):.3f}")
        
        if 'answer_correctness' in result:
            lines.append(f"- **Answer Correctness**: {result.get('answer_correctness', 0):.3f}")
        
        return "\n".join(lines)
    
    def _format_performance_grades(self, grades: Dict[str, str]) -> str:
        """성능 등급 포맷팅"""
        lines = []
        lines.append(f"- **전체 등급**: {grades.get('overall', 'N/A')}")
        lines.append(f"- **Faithfulness**: {grades.get('faithfulness', 'N/A')}")
        lines.append(f"- **Answer Relevancy**: {grades.get('answer_relevancy', 'N/A')}")
        lines.append(f"- **Context Recall**: {grades.get('context_recall', 'N/A')}")
        lines.append(f"- **Context Precision**: {grades.get('context_precision', 'N/A')}")
        
        if 'answer_correctness' in grades:
            lines.append(f"- **Answer Correctness**: {grades.get('answer_correctness', 'N/A')}")
        
        return "\n".join(lines)
    
    def _format_statistics_table(self, stats: Dict[str, Dict]) -> str:
        """통계 테이블 포맷팅"""
        if not stats:
            return "통계 데이터가 없습니다."
        
        lines = []
        lines.append("| 메트릭 | 평균 | 중앙값 | 표준편차 | 최소값 | 최대값 | 사분위수 범위 |")
        lines.append("|--------|------|--------|----------|--------|--------|---------------|")
        
        for metric, stat in stats.items():
            lines.append(f"| {metric} | {stat['mean']:.3f} | {stat['median']:.3f} | {stat['std_dev']:.3f} | {stat['min']:.3f} | {stat['max']:.3f} | {stat.get('iqr', 0):.3f} |")
        
        return "\n".join(lines)
    
    def _format_metric_analysis(self, metric: str, stat: Dict) -> str:
        """메트릭별 상세 분석 포맷팅"""
        if not stat:
            return "- 분석 데이터가 없습니다."
        
        lines = []
        lines.append(f"- **변동성**: 표준편차 {stat['std_dev']:.3f} (변동계수: {stat['cv']:.2f})")
        lines.append(f"- **분포**: 최소 {stat['min']:.3f} ~ 최대 {stat['max']:.3f}")
        lines.append(f"- **중앙값**: {stat['median']:.3f}")
        
        if stat.get('iqr', 0) > 0.1:
            lines.append("- **주의**: 점수 분산이 크므로 일관성 개선이 필요합니다.")
        elif stat.get('iqr', 0) < 0.05:
            lines.append("- **양호**: 점수가 일관되게 분포되어 있습니다.")
        
        return "\n".join(lines)
    
    def _format_answer_correctness_section(self, result: Dict[str, Any], stats: Dict[str, Dict]) -> str:
        """Answer Correctness 섹션 포맷팅"""
        if 'answer_correctness' not in result:
            return ""
        
        return f"""
### 5. Answer Correctness (답변 정확도)
- **현재 점수**: {result.get('answer_correctness', 0):.3f}
- **해석**: {self._interpret_answer_correctness(result.get('answer_correctness', 0))}
{self._format_metric_analysis('answer_correctness', stats.get('answer_correctness', {}))}
"""
    
    def _interpret_faithfulness(self, score: float) -> str:
        """Faithfulness 점수 해석"""
        if score >= 0.9:
            return "답변이 제공된 컨텍스트에 매우 충실하며, 환각(hallucination)이 거의 없습니다."
        elif score >= 0.8:
            return "답변이 컨텍스트에 대체로 충실하지만, 일부 개선의 여지가 있습니다."
        elif score >= 0.7:
            return "답변이 컨텍스트에 어느 정도 충실하지만, 정확성 향상이 필요합니다."
        elif score >= 0.6:
            return "답변에 컨텍스트와 일치하지 않는 내용이 포함되어 있어 개선이 필요합니다."
        else:
            return "답변에 환각이나 부정확한 내용이 많이 포함되어 있어 시급한 개선이 필요합니다."
    
    def _interpret_answer_relevancy(self, score: float) -> str:
        """Answer Relevancy 점수 해석"""
        if score >= 0.9:
            return "답변이 질문과 매우 관련성이 높고 적절합니다."
        elif score >= 0.8:
            return "답변이 질문과 관련성이 높지만 일부 개선이 가능합니다."
        elif score >= 0.7:
            return "답변이 질문과 어느 정도 관련이 있지만 더 구체적일 필요가 있습니다."
        elif score >= 0.6:
            return "답변이 질문과 부분적으로만 관련이 있어 개선이 필요합니다."
        else:
            return "답변이 질문과 관련성이 낮아 시급한 개선이 필요합니다."
    
    def _interpret_context_recall(self, score: float) -> str:
        """Context Recall 점수 해석"""
        if score >= 0.9:
            return "관련 정보가 거의 완벽하게 검색되었습니다."
        elif score >= 0.8:
            return "관련 정보가 잘 검색되었지만 일부 누락이 있을 수 있습니다."
        elif score >= 0.7:
            return "관련 정보가 어느 정도 검색되었지만 검색 성능 향상이 필요합니다."
        elif score >= 0.6:
            return "관련 정보 검색에 상당한 개선이 필요합니다."
        else:
            return "관련 정보 검색 성능이 크게 부족하여 시급한 개선이 필요합니다."
    
    def _interpret_context_precision(self, score: float) -> str:
        """Context Precision 점수 해석"""
        if score >= 0.9:
            return "검색된 컨텍스트가 매우 정확하고 관련성이 높습니다."
        elif score >= 0.8:
            return "검색된 컨텍스트가 대체로 정확하지만 일부 개선이 가능합니다."
        elif score >= 0.7:
            return "검색된 컨텍스트에 관련성이 떨어지는 내용이 일부 포함되어 있습니다."
        elif score >= 0.6:
            return "검색된 컨텍스트의 정확성 향상이 필요합니다."
        else:
            return "검색된 컨텍스트에 관련성이 낮은 내용이 많아 시급한 개선이 필요합니다."
    
    def _interpret_answer_correctness(self, score: float) -> str:
        """Answer Correctness 점수 해석"""
        if score >= 0.9:
            return "답변이 정답과 매우 일치하며 높은 정확도를 보입니다."
        elif score >= 0.8:
            return "답변이 정답과 대체로 일치하지만 일부 개선이 가능합니다."
        elif score >= 0.7:
            return "답변이 정답과 어느 정도 일치하지만 정확도 향상이 필요합니다."
        elif score >= 0.6:
            return "답변과 정답 간의 일치도가 낮아 개선이 필요합니다."
        else:
            return "답변의 정확도가 크게 부족하여 시급한 개선이 필요합니다."
    
    def _generate_recommendations(self, result: Dict[str, Any], stats: Dict[str, Dict]) -> str:
        """개선 권장사항 생성"""
        recommendations = []
        
        # 점수 기반 권장사항
        if result.get('faithfulness', 0) < 0.7:
            recommendations.append("📌 **Faithfulness 개선**: 답변 생성 시 제공된 컨텍스트에 더 충실하도록 프롬프트를 개선하세요.")
        
        if result.get('answer_relevancy', 0) < 0.7:
            recommendations.append("📌 **Answer Relevancy 개선**: 질문의 핵심 의도를 더 정확히 파악하여 관련성 높은 답변을 생성하세요.")
        
        if result.get('context_recall', 0) < 0.7:
            recommendations.append("📌 **Context Recall 개선**: 검색 알고리즘을 개선하여 관련 정보를 더 완전히 검색하세요.")
        
        if result.get('context_precision', 0) < 0.7:
            recommendations.append("📌 **Context Precision 개선**: 검색된 컨텍스트의 품질을 향상시키고 노이즈를 줄이세요.")
        
        if 'answer_correctness' in result and result.get('answer_correctness', 0) < 0.7:
            recommendations.append("📌 **Answer Correctness 개선**: 모델 훈련 데이터나 fine-tuning을 통해 답변 정확도를 향상시키세요.")
        
        # 변동성 기반 권장사항
        for metric, stat in stats.items():
            if stat.get('cv', 0) > 0.3:  # 변동계수가 30% 이상
                recommendations.append(f"📊 **{metric} 일관성 개선**: 점수 변동이 크므로 더 일관된 성능을 위한 최적화가 필요합니다.")
        
        if not recommendations:
            recommendations.append("🎉 **전반적으로 우수한 성능**: 현재 성능을 유지하며 지속적인 모니터링을 권장합니다.")
        
        return "\n".join(recommendations)
    
    def _evaluate_data_quality(self, individual_scores: List[Dict]) -> str:
        """데이터 품질 평가"""
        if not individual_scores:
            return "평가할 데이터가 없습니다."
        
        lines = []
        lines.append(f"- **총 평가 항목 수**: {len(individual_scores)}개")
        
        # 완전한 점수를 가진 항목 수 확인
        complete_items = sum(1 for item in individual_scores if all(v is not None for v in item.values()))
        lines.append(f"- **완전한 평가 항목**: {complete_items}개 ({complete_items/len(individual_scores)*100:.1f}%)")
        
        # 누락된 점수 확인
        missing_counts = {}
        for item in individual_scores:
            for metric, score in item.items():
                if score is None:
                    missing_counts[metric] = missing_counts.get(metric, 0) + 1
        
        if missing_counts:
            lines.append("- **누락된 메트릭**:")
            for metric, count in missing_counts.items():
                lines.append(f"  - {metric}: {count}개 항목 ({count/len(individual_scores)*100:.1f}%)")
        else:
            lines.append("- **데이터 완성도**: 모든 메트릭이 완전히 평가되었습니다.")
        
        return "\n".join(lines)
    
    def _extract_evaluation_id(self, metadata: Dict[str, Any]) -> str:
        """평가 ID 추출"""
        # 여러 가능한 키에서 평가 ID 찾기
        possible_keys = ['evaluation_id', 'id', 'eval_id']
        for key in possible_keys:
            if key in metadata and metadata[key]:
                return str(metadata[key])
        
        # 파일명에서 ID 추출 시도
        if 'filename' in metadata:
            filename = metadata['filename']
            if '_' in filename:
                parts = filename.split('_')
                if len(parts) >= 2:
                    return parts[1]  # eval_xxxxx_... 형태에서 추출
        
        # 생성일시 기반 ID 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"eval_{timestamp}"
    
    def _extract_timestamp(self, metadata: Dict[str, Any]) -> str:
        """평가 일시 추출"""
        # 여러 가능한 키에서 타임스탬프 찾기
        possible_keys = ['timestamp', 'created_at', 'evaluation_time', 'start_time']
        for key in possible_keys:
            if key in metadata and metadata[key]:
                # 이미 포맷된 문자열인 경우
                if isinstance(metadata[key], str):
                    return metadata[key]
                # datetime 객체인 경우
                elif hasattr(metadata[key], 'strftime'):
                    return metadata[key].strftime('%Y-%m-%d %H:%M:%S')
        
        # 현재 시간 반환
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _extract_llm_model(self, metadata: Dict[str, Any]) -> str:
        """LLM 모델 추출"""
        # 여러 가능한 키에서 LLM 모델 찾기
        possible_keys = ['llm_type', 'model', 'llm_model', 'llm']
        for key in possible_keys:
            if key in metadata and metadata[key]:
                model_name = str(metadata[key]).upper()
                # 모델 이름 정규화
                if model_name in ['GEMINI', 'GEMINI-2.5-FLASH', 'GEMINI-2.5-FLASH-PREVIEW-05-20']:
                    return 'Google Gemini 2.5 Flash'
                elif model_name in ['HCX', 'HCX-005']:
                    return 'Naver HCX-005'
                return model_name
        
        return 'N/A'
    
    def _extract_embedding_model(self, metadata: Dict[str, Any]) -> str:
        """임베딩 모델 추출"""
        # 여러 가능한 키에서 임베딩 모델 찾기
        possible_keys = ['embedding_type', 'embedding_model', 'embedding']
        for key in possible_keys:
            if key in metadata and metadata[key]:
                model_name = str(metadata[key]).upper()
                # 모델 이름 정규화
                if model_name in ['GEMINI', 'GEMINI-EMBEDDING-EXP-03-07']:
                    return 'Google Gemini Embedding'
                elif model_name in ['HCX', 'HCX-EMBEDDING']:
                    return 'Naver HCX Embedding'
                elif model_name in ['BGE_M3', 'BGE-M3']:
                    return 'BGE-M3 (로컬)'
                return model_name
        
        return 'N/A'
    
    def _extract_dataset_size(self, metadata: Dict[str, Any], individual_scores: List[Dict]) -> int:
        """데이터셋 크기 추출"""
        # 메타데이터에서 크기 정보 찾기
        possible_keys = ['dataset_size', 'total_items', 'item_count', 'size']
        for key in possible_keys:
            if key in metadata and isinstance(metadata[key], (int, float)):
                return int(metadata[key])
        
        # individual_scores에서 크기 계산
        if individual_scores:
            return len(individual_scores)
        
        # QA 데이터에서 크기 계산
        if 'qa_data' in metadata:
            qa_data = metadata['qa_data']
            if isinstance(qa_data, list):
                return len(qa_data)
        
        return 0
    
    def _extract_duration_info(self, metadata: Dict[str, Any], individual_scores: List[Dict]) -> Dict[str, float]:
        """평가 시간 정보 추출"""
        # 기본값
        duration_info = {
            'total_minutes': 0.0,
            'avg_seconds': 0.0
        }
        
        # 메타데이터에서 시간 정보 찾기
        total_duration = None
        possible_duration_keys = ['total_duration_minutes', 'duration_minutes', 'elapsed_time']
        for key in possible_duration_keys:
            if key in metadata and isinstance(metadata[key], (int, float)):
                total_duration = float(metadata[key])
                break
        
        # start_time과 end_time에서 계산
        if total_duration is None:
            start_time = metadata.get('start_time')
            end_time = metadata.get('end_time')
            if start_time and end_time:
                try:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    
                    duration = end_time - start_time
                    total_duration = duration.total_seconds() / 60.0  # 분 단위
                except:
                    pass
        
        # 개별 항목 시간에서 계산
        if total_duration is None and individual_scores:
            # 평균 추정 시간 사용 (항목당 8초 가정)
            estimated_seconds_per_item = 8.0
            total_duration = len(individual_scores) * estimated_seconds_per_item / 60.0
        
        if total_duration is not None:
            duration_info['total_minutes'] = total_duration
            dataset_size = self._extract_dataset_size(metadata, individual_scores)
            if dataset_size > 0:
                duration_info['avg_seconds'] = (total_duration * 60.0) / dataset_size
        
        return duration_info
    
    def export_full_package(self, result: Dict[str, Any], base_filename: Optional[str] = None) -> Dict[str, str]:
        """전체 패키지 내보내기 (CSV + 요약 + 보고서)"""
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"ragas_evaluation_{timestamp}"
        
        files = {}
        
        # 상세 CSV
        files['detailed_csv'] = self.export_to_csv(result, f"{base_filename}_detailed.csv")
        
        # 요약 CSV  
        files['summary_csv'] = self.export_summary_csv(result, f"{base_filename}_summary.csv")
        
        # 분석 보고서
        files['analysis_report'] = self.generate_analysis_report(result, f"{base_filename}_analysis.md")
        
        return files