"""
RAGAS 메트릭에서 실제 사용되는 프롬프트 추출 유틸리티

이 모듈은 RAGAS 라이브러리에서 실제로 사용하는 평가 프롬프트를 동적으로 가져와서
Streamlit 인터페이스에 표시할 수 있도록 합니다.
"""

from typing import Dict, Optional

from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)


def get_ragas_prompt(metric_name: str) -> Optional[str]:
    """특정 메트릭의 실제 평가 프롬프트를 가져옵니다.
    
    Args:
        metric_name: 메트릭 이름 ('faithfulness', 'answer_relevancy', 'context_recall', 'context_precision')
        
    Returns:
        해당 메트릭의 프롬프트 문자열, 찾을 수 없으면 None
    """
    metrics = {
        'faithfulness': faithfulness,
        'answer_relevancy': answer_relevancy,
        'context_recall': context_recall,
        'context_precision': context_precision,
    }
    
    metric = metrics.get(metric_name)
    if not metric:
        return None
    
    # RAGAS 버전에 따라 프롬프트 속성명이 다를 수 있음
    prompt_attributes = [
        'faithfulness_prompt',
        'question_generation', 
        'context_recall_prompt',
        'context_precision_prompt',
        'llm_prompt',
        '_evaluation_prompt',
        'prompt',
        'template',
    ]
    
    for attr in prompt_attributes:
        if hasattr(metric, attr):
            prompt_obj = getattr(metric, attr)
            if prompt_obj:
                # 프롬프트 객체에서 실제 템플릿 텍스트 추출
                if hasattr(prompt_obj, 'template'):
                    return prompt_obj.template
                elif hasattr(prompt_obj, 'format_string'):
                    return prompt_obj.format_string
                elif isinstance(prompt_obj, str):
                    return prompt_obj
                else:
                    return str(prompt_obj)
    
    return None


def get_all_ragas_prompts() -> Dict[str, str]:
    """모든 RAGAS 메트릭의 실제 프롬프트를 가져옵니다.
    
    Returns:
        메트릭명을 키로 하고 프롬프트 문자열을 값으로 하는 딕셔너리
    """
    metric_names = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    prompts = {}
    
    for metric_name in metric_names:
        prompt = get_ragas_prompt(metric_name)
        if prompt:
            prompts[metric_name] = prompt
        else:
            prompts[metric_name] = f"프롬프트를 찾을 수 없습니다 ({metric_name})"
    
    return prompts


def extract_prompt_from_metric_object(metric_obj) -> Optional[str]:
    """메트릭 객체에서 프롬프트를 추출하는 헬퍼 함수"""
    # 가능한 프롬프트 속성들을 체크
    possible_attrs = [
        'faithfulness_prompt',
        'question_generation',
        'context_recall_prompt', 
        'context_precision_prompt',
        'llm_prompt',
        '_evaluation_prompt',
        'prompt',
        'template',
    ]
    
    for attr in possible_attrs:
        if hasattr(metric_obj, attr):
            prompt_obj = getattr(metric_obj, attr)
            if prompt_obj:
                # 다양한 프롬프트 객체 타입 처리
                if hasattr(prompt_obj, 'template'):
                    return prompt_obj.template
                elif hasattr(prompt_obj, 'format_string'):
                    return prompt_obj.format_string
                elif hasattr(prompt_obj, 'prompt'):
                    return prompt_obj.prompt
                elif isinstance(prompt_obj, str):
                    return prompt_obj
                else:
                    # 객체를 문자열로 변환 시도
                    str_repr = str(prompt_obj)
                    if len(str_repr) > 50:  # 의미있는 프롬프트인지 확인
                        return str_repr
    
    return None


def format_prompt_for_display(prompt: str, metric_name: str) -> str:
    """프롬프트를 Streamlit 표시용으로 포맷팅합니다.
    
    Args:
        prompt: 원본 프롬프트 문자열
        metric_name: 메트릭 이름
        
    Returns:
        포맷팅된 프롬프트 문자열
    """
    if not prompt:
        return f"❌ {metric_name} 프롬프트를 찾을 수 없습니다."
    
    # 프롬프트 정리 및 포맷팅
    formatted = prompt.strip()
    
    # 변수 플레이스홀더 설명 추가
    variable_info = {
        'faithfulness': '변수: {question}, {answer}, {context}',
        'answer_relevancy': '변수: {question}, {answer}',
        'context_recall': '변수: {question}, {ground_truth}, {context}',
        'context_precision': '변수: {question}, {answer}, {context}',
    }
    
    if metric_name in variable_info:
        formatted += f"\n\n📝 **{variable_info[metric_name]}**"
    
    return formatted


# 메트릭별 프롬프트 캐시 (성능 최적화용)
_prompt_cache = {}


def get_cached_ragas_prompt(metric_name: str) -> str:
    """캐시된 RAGAS 프롬프트를 가져옵니다.
    
    Args:
        metric_name: 메트릭 이름
        
    Returns:
        포맷팅된 프롬프트 문자열
    """
    if metric_name not in _prompt_cache:
        raw_prompt = get_ragas_prompt(metric_name)
        _prompt_cache[metric_name] = format_prompt_for_display(raw_prompt, metric_name)
    
    return _prompt_cache[metric_name]