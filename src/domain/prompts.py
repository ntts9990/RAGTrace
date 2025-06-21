"""
도메인 특화 RAGAS 프롬프트 정의

이 모듈은 한국어/영어 기반 도메인 기술 문서 평가에 특화된
커스텀 RAGAS 프롬프트들을 정의합니다.
"""

from enum import Enum
from typing import Dict, List, Optional, Any


class PromptType(Enum):
    """프롬프트 타입 열거형"""
    DEFAULT = "default"
    NUCLEAR_HYDRO_TECH = "nuclear_hydro_tech"
    KOREAN_FORMAL = "korean_formal"


class CustomPromptConfig:
    """커스텀 프롬프트 설정 클래스"""
    
    def __init__(self, prompt_type: PromptType = PromptType.DEFAULT):
        self.prompt_type = prompt_type
        
    def get_faithfulness_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Faithfulness 메트릭용 커스텀 프롬프트"""
        if self.prompt_type == PromptType.NUCLEAR_HYDRO_TECH:
            return {
                "statement_generator": {
                    "instruction": """주어진 질문과 답변을 바탕으로, 답변의 각 문장의 복잡도를 분석하세요. 
각 문장을 하나 이상의 완전히 이해 가능한 진술문으로 분해하세요. 
진술문에서는 대명사를 사용하지 마세요. JSON 형식으로 출력하세요.

**원자력/수력 기술 문서 특화 고려사항:**
- 안전 관련 절차와 규정의 정확성
- 물리적/화학적 수식과 단위의 정확성
- 시스템 구성요소와 운영 매개변수
- 한영 혼용 전문 용어의 일관성
- 측정값, 허용 범위, 임계값의 정밀성
- 안전 등급, 품질 보증 요구사항""",
                    "examples": [
                        {
                            "question": "원자로 냉각재 온도 측정 시 주의사항은?",
                            "answer": "RTD (Resistance Temperature Detector) 센서를 사용하여 측정하며, 허용 오차는 ±0.5°C 이내여야 합니다. Safety Class 1E 등급이 요구됩니다.",
                            "statements": [
                                "RTD 센서를 사용하여 원자로 냉각재 온도를 측정한다",
                                "온도 측정의 허용 오차는 ±0.5°C 이내이다", 
                                "Safety Class 1E 등급 센서가 요구된다",
                                "Resistance Temperature Detector는 RTD의 완전한 명칭이다"
                            ]
                        }
                    ],
                    "language": "korean"
                },
                "nli_statement": {
                    "instruction": """원자력/수력 기술 문서 컨텍스트와 진술문들을 바탕으로, 각 진술문이 주어진 컨텍스트에서 지원되는지 확인하세요.

**원자력/수력 기술 문서 평가 기준:**
- 안전 규정과 절차의 정확성
- 물리량, 수식, 단위의 정밀성
- 시스템 사양과 운영 매개변수의 일치성
- 한영 혼용 전문 용어의 올바른 사용
- 허용 범위, 임계값, 품질 기준의 정확성
- IEEE, ASME, NRC 등 표준 규격 준수

각 진술문에 대해 컨텍스트에서 직접 추론 가능하면 1, 불가능하면 0으로 판정하세요.""",
                    "examples": [
                        {
                            "context": "원자로 압력용기 내부 온도는 RTD 센서로 측정되며, 허용 오차는 ±0.5°C입니다. Safety Class 1E 등급 장비만 사용 가능합니다.",
                            "statements": [
                                {
                                    "statement": "RTD 센서를 사용하여 원자로 압력용기 내부 온도를 측정한다",
                                    "reason": "컨텍스트에서 RTD 센서로 온도를 측정한다고 명시되어 있음",
                                    "verdict": 1
                                },
                                {
                                    "statement": "온도 측정의 허용 오차는 ±0.5°C이다",
                                    "reason": "컨텍스트에서 허용 오차가 ±0.5°C라고 명시되어 있음",
                                    "verdict": 1
                                }
                            ]
                        }
                    ],
                    "language": "korean"
                }
            }
        
        # DEFAULT 타입은 빈 딕셔너리 반환 (RAGAS 기본 프롬프트 사용)
        return {}
    
    def get_answer_relevancy_prompts(self) -> Dict[str, Any]:
        """Answer Relevancy 메트릭용 커스텀 프롬프트"""
        if self.prompt_type == PromptType.NUCLEAR_HYDRO_TECH:
            return {
                "instruction": """원자력/수력 기술 문서에서 주어진 답변의 연관성을 평가하세요. 
답변으로부터 역질문을 생성하고 비확정성을 판단하세요.

**원자력/수력 기술 문서 특화 평가 요소:**
- 안전성 관련 질문과 답변의 명확성
- 정량적 데이터 (압력, 온도, 유량 등)의 정확성
- 시스템 운영 절차의 구체성과 완전성
- 한영 혼용 전문 용어의 정확한 사용
- 규제 요구사항과 표준 규격의 준수
- 수식, 계산, 단위 변환의 정확성

**비확정적 답변 판단 기준:**
- "대략", "approximately", "around" (정밀 측정값에서)
- "조건에 따라 다름" (구체적 조건 명시 없음)
- "추가 분석 필요", "further study required"
- "일반적으로", "typically" (안전 관련 절차에서)""",
                "examples": [
                    {
                        "response": "원자로 압력은 대략 15.5 MPa 정도이며, 운전 조건에 따라 다를 수 있습니다.",
                        "question": "원자로 운전 압력은?",
                        "noncommittal": 1
                    },
                    {
                        "response": "Safety Injection System은 RCS 압력이 12.4 MPa 이하로 떨어질 때 자동으로 작동합니다.",
                        "question": "비상노심냉각계통은 언제 작동하나요?", 
                        "noncommittal": 0
                    }
                ],
                "language": "korean"
            }
        elif self.prompt_type == PromptType.KOREAN_FORMAL:
            return {
                "instruction": """공식 문서 답변의 연관성을 평가하세요. 
답변으로부터 역질문을 생성하고 비확정성을 판단하세요.

**한국어 공식 문서 특화 평가 요소:**
- 정책 및 규정의 명확한 제시
- 공식적이고 정확한 용어 사용
- 절차와 기준의 구체적 명시
- 법적 근거 및 규정 인용의 정확성
- 권한과 책임의 명확한 구분

**비확정적 답변 판단 기준:**
- "검토 예정", "추후 결정" (구체적 일정 없음)
- "관련 부서와 협의" (명확한 담당자 없음)
- "상황에 따라", "경우에 따라" (구체적 조건 없음)
- "원칙적으로", "일반적으로" (공식 문서에서)""",
                "examples": [
                    {
                        "response": "관련 부서와 협의하여 추후 결정할 예정입니다.",
                        "question": "신청 승인 기준은 무엇인가요?",
                        "noncommittal": 1
                    },
                    {
                        "response": "행정절차법 제20조에 따라 30일 이내 처리됩니다.",
                        "question": "처리 기간은 얼마나 걸리나요?", 
                        "noncommittal": 0
                    }
                ],
                "language": "korean"
            }
        
        return {}
    
    def get_context_recall_prompts(self) -> Dict[str, Any]:
        """Context Recall 메트릭용 커스텀 프롬프트"""
        if self.prompt_type == PromptType.NUCLEAR_HYDRO_TECH:
            return {
                "instruction": """원자력/수력 기술 문서에서 Ground Truth 답변의 각 핵심 정보가 검색된 컨텍스트에서 찾을 수 있는지 분석하세요.

**원자력/수력 기술 문서 특화 분석 요소:**
- 시스템 사양과 운영 매개변수 (압력, 온도, 유량 등)
- 안전 관련 절차와 규제 요구사항
- 물리적/화학적 수식과 계산 방법
- 한영 혼용 전문 용어와 약어 정의
- 품질 보증 등급과 표준 규격
- 임계값, 허용 범위, 설정점 (setpoint)

각 진술문이 컨텍스트에서 귀속 가능하면 'Yes'(1), 불가능하면 'No'(0)로 분류하고 JSON으로 출력하세요.""",
                "examples": [
                    {
                        "question": "원자로 안전 정지를 위한 제어봉 삽입 시간은?",
                        "context": "제어봉은 원자로 trip 신호 발생 시 중력에 의해 노심에 삽입됩니다. 전체 삽입 시간은 2.7초 이내여야 하며, 이는 10 CFR 50 Appendix A의 요구사항입니다.",
                        "answer": "제어봉 삽입 시간은 2.7초 이내이며, 10 CFR 50 규정을 준수해야 합니다.",
                        "classifications": [
                            {
                                "statement": "제어봉 삽입 시간은 2.7초 이내이다",
                                "reason": "컨텍스트에서 전체 삽입 시간이 2.7초 이내라고 명시됨",
                                "attributed": 1
                            },
                            {
                                "statement": "10 CFR 50 규정을 준수해야 한다",
                                "reason": "컨텍스트에서 10 CFR 50 Appendix A 요구사항이라고 설명됨",
                                "attributed": 1
                            }
                        ]
                    }
                ],
                "language": "korean"
            }
        
        return {}
    
    def get_context_precision_prompts(self) -> Dict[str, Any]:
        """Context Precision 메트릭용 커스텀 프롬프트"""
        if self.prompt_type == PromptType.NUCLEAR_HYDRO_TECH:
            return {
                "instruction": """원자력/수력 기술 문서 컨텍스트가 질문에 대한 답변 도출에 얼마나 유용했는지 평가하세요.

**원자력/수력 기술 문서 유용성 평가 기준:**
- 직접적 안전 정보 제공 (high precision)
- 시스템 운영 매개변수 명시 (high precision)
- 관련 규제 요구사항 포함 (medium precision)
- 일반적 배경 지식만 제공 (low precision)  
- 관련 없는 시스템 정보 (no precision)

**추가 평가 요소:**
- 정확성: 현행 규제 및 표준과의 일치도
- 완전성: 안전 운영에 필요한 모든 정보 포함
- 정밀성: 수치, 단위, 수식의 정확성
- 일관성: 한영 혼용 용어의 표준 사용

유용하면 "1", 그렇지 않으면 "0"으로 판정하고 JSON으로 출력하세요.""",
                "examples": [
                    {
                        "question": "ECCS 작동 압력 설정점은?",
                        "context": "Emergency Core Cooling System (ECCS)는 RCS 압력이 12.4 MPa 이하로 떨어질 때 자동으로 작동합니다. 이는 FSAR Chapter 6.3에 명시된 설계 기준입니다.",
                        "answer": "ECCS는 RCS 압력 12.4 MPa에서 작동합니다.",
                        "verdict": 1,
                        "reason": "컨텍스트가 질문에 대한 정확한 압력값과 규제 근거를 포함하고 있음"
                    }
                ],
                "language": "korean"
            }
        
        return {}


# 프롬프트 타입별 설명
PROMPT_TYPE_DESCRIPTIONS = {
    PromptType.DEFAULT: "RAGAS 기본 프롬프트 (영어)",
    PromptType.NUCLEAR_HYDRO_TECH: "원자력/수력 기술 문서 특화 프롬프트 (한영 혼용)",  
    PromptType.KOREAN_FORMAL: "한국어 공식 문서 프롬프트"
}

# 사용 가능한 프롬프트 타입 목록
AVAILABLE_PROMPT_TYPES = list(PromptType)