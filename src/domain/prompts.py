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
    KOREAN_TECH = "korean_tech"
    MULTILINGUAL_TECH = "multilingual_tech"
    KOREAN_FORMAL = "korean_formal"


class CustomPromptConfig:
    """커스텀 프롬프트 설정 클래스"""
    
    def __init__(self, prompt_type: PromptType = PromptType.DEFAULT):
        self.prompt_type = prompt_type
        
    def get_faithfulness_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Faithfulness 메트릭용 커스텀 프롬프트"""
        if self.prompt_type == PromptType.KOREAN_TECH:
            return {
                "statement_generator": {
                    "instruction": """주어진 질문과 답변을 바탕으로, 답변의 각 문장의 복잡도를 분석하세요. 
각 문장을 하나 이상의 완전히 이해 가능한 진술문으로 분해하세요. 
진술문에서는 대명사를 사용하지 마세요. JSON 형식으로 출력하세요.

**기술 문서 특화 고려사항:**
- 기술 용어의 정확한 정의와 사용법
- 버전 정보, 호환성, 제약사항  
- 단계별 절차나 설정 방법
- 코드 예시나 명령어의 정확성""",
                    "examples": [
                        {
                            "question": "Docker 컨테이너를 생성하는 방법은?",
                            "answer": "docker run -d --name myapp nginx:latest 명령으로 nginx 컨테이너를 백그라운드에서 실행할 수 있습니다.",
                            "statements": [
                                "docker run 명령어로 컨테이너를 생성할 수 있다",
                                "-d 플래그는 백그라운드 실행을 의미한다", 
                                "--name 옵션으로 컨테이너 이름을 지정할 수 있다",
                                "nginx:latest는 최신 nginx 이미지를 사용한다"
                            ]
                        }
                    ],
                    "language": "korean"
                },
                "nli_statement": {
                    "instruction": """기술 문서 컨텍스트와 진술문들을 바탕으로, 각 진술문이 주어진 컨텍스트에서 지원되는지 확인하세요.

**기술 문서 평가 기준:**
- 명령어나 코드의 정확한 문법
- 버전별 차이점이나 deprecated 기능 여부
- 전제 조건이나 환경 요구사항
- 부작용이나 주의사항

각 진술문에 대해 컨텍스트에서 직접 추론 가능하면 1, 불가능하면 0으로 판정하세요.""",
                    "examples": [
                        {
                            "context": "Docker run 명령어는 새로운 컨테이너를 생성하고 실행합니다. -d 옵션은 detached 모드로 백그라운드에서 실행을 의미합니다.",
                            "statements": [
                                {
                                    "statement": "docker run 명령어로 컨테이너를 생성할 수 있다",
                                    "reason": "컨텍스트에서 docker run이 새로운 컨테이너를 생성한다고 명시되어 있음",
                                    "verdict": 1
                                },
                                {
                                    "statement": "-d 플래그는 백그라운드 실행을 의미한다",
                                    "reason": "컨텍스트에서 -d 옵션이 detached 모드로 백그라운드 실행을 의미한다고 설명되어 있음",
                                    "verdict": 1
                                }
                            ]
                        }
                    ],
                    "language": "korean"
                }
            }
        elif self.prompt_type == PromptType.MULTILINGUAL_TECH:
            return {
                "statement_generator": {
                    "instruction": """Given a question and answer in Korean/English technical documentation context, 
analyze each sentence complexity and break down into fully understandable statements. 
Ensure no pronouns are used. Format in JSON.

**Technical Documentation Considerations:**
- Accurate definition and usage of technical terms
- Version information, compatibility, constraints
- Step-by-step procedures or configuration methods
- Accuracy of code examples or commands
- Language consistency (Korean/English mixed environment)""",
                    "examples": [
                        {
                            "question": "How to install Python packages using pip?", 
                            "answer": "pip install package_name을 사용하여 패키지를 설치할 수 있습니다. Python 3.4 이상에서는 pip가 기본 포함됩니다.",
                            "statements": [
                                "pip install command can be used to install Python packages",
                                "pip install package_name is the syntax for installing packages",
                                "pip is included by default in Python 3.4 and above"
                            ]
                        }
                    ],
                    "language": "multilingual"
                },
                "nli_statement": {
                    "instruction": """Verify if each statement can be supported by the given technical documentation context.

**Technical Evaluation Criteria:**
- Accuracy of command syntax and code
- Version differences or deprecated features
- Prerequisites or environment requirements  
- Side effects or warnings
- Language consistency in mixed Korean/English environment

Return 1 if statement can be directly inferred from context, 0 if not.""",
                    "examples": [
                        {
                            "context": "pip is the package installer for Python. It is included with Python 3.4 and later versions.",
                            "statements": [
                                {
                                    "statement": "pip is included by default in Python 3.4 and above",
                                    "reason": "The context explicitly states pip is included with Python 3.4 and later versions",
                                    "verdict": 1
                                }
                            ]
                        }
                    ],
                    "language": "multilingual"
                }
            }
        
        # DEFAULT 타입은 빈 딕셔너리 반환 (RAGAS 기본 프롬프트 사용)
        return {}
    
    def get_answer_relevancy_prompts(self) -> Dict[str, Any]:
        """Answer Relevancy 메트릭용 커스텀 프롬프트"""
        if self.prompt_type == PromptType.KOREAN_TECH:
            return {
                "instruction": """기술 문서 도메인에서 주어진 답변의 연관성을 평가하세요. 
답변으로부터 역질문을 생성하고 비확정성을 판단하세요.

**기술 문서 특화 평가 요소:**
- 질문의 기술적 구체성과 답변의 상세도 일치
- 실행 가능한 솔루션 제공 여부
- 트러블슈팅이나 대안 방법 포함 여부
- 전문 용어 사용의 적절성

**비확정적 답변 판단 기준:**
- "아마도", "probably", "might work"
- "버전에 따라 다름" (구체적 버전 명시 없음)
- "환경에 따라 다름" (구체적 환경 명시 없음)
- "추가 확인 필요", "공식 문서 참조" """,
                "examples": [
                    {
                        "response": "npm install로 패키지를 설치할 수 있지만, Node.js 버전에 따라 다를 수 있습니다.",
                        "question": "npm으로 패키지를 어떻게 설치하나요?",
                        "noncommittal": 1
                    },
                    {
                        "response": "docker run -p 8080:80 nginx 명령으로 nginx 컨테이너를 포트 8080에서 실행할 수 있습니다.",
                        "question": "Docker로 nginx를 어떻게 실행하나요?", 
                        "noncommittal": 0
                    }
                ],
                "language": "korean"
            }
        elif self.prompt_type == PromptType.MULTILINGUAL_TECH:
            return {
                "instruction": """Evaluate answer relevancy in technical documentation domain. 
Generate reverse questions from answers and identify non-committal responses.

**Technical Documentation Evaluation Elements:**
- Match between technical specificity of question and answer detail
- Provision of executable solutions
- Inclusion of troubleshooting or alternative methods
- Appropriate use of technical terminology
- Language consistency in Korean/English mixed environment

**Non-committal Answer Criteria:**
- "maybe", "probably", "might work", "아마도"
- "depends on version" (without specific version)
- "depends on environment" (without specific environment)  
- "needs further verification", "참고 공식 문서" """,
                "examples": [
                    {
                        "response": "You can install packages using npm install, but it depends on your Node.js version.",
                        "question": "How to install packages with npm?",
                        "noncommittal": 1
                    }
                ],
                "language": "multilingual"
            }
        
        return {}
    
    def get_context_recall_prompts(self) -> Dict[str, Any]:
        """Context Recall 메트릭용 커스텀 프롬프트"""
        if self.prompt_type == PromptType.KOREAN_TECH:
            return {
                "instruction": """기술 문서에서 Ground Truth 답변의 각 핵심 정보가 검색된 컨텍스트에서 찾을 수 있는지 분석하세요.

**기술 문서 특화 분석 요소:**
- 코드 스니펫이나 명령어의 완전성
- 설정 파일이나 구성 옵션
- 에러 메시지나 해결 방법
- 버전 정보나 호환성 데이터
- 전제 조건이나 의존성

각 진술문이 컨텍스트에서 귀속 가능하면 'Yes'(1), 불가능하면 'No'(0)로 분류하고 JSON으로 출력하세요.""",
                "examples": [
                    {
                        "question": "React에서 useEffect 사용법은?",
                        "context": "React의 useEffect Hook은 함수형 컴포넌트에서 side effect를 수행할 때 사용합니다. 의존성 배열을 생략하면 매 렌더링마다 실행됩니다.",
                        "answer": "useEffect는 side effect 수행에 사용되며, 의존성 배열 생략 시 매 렌더링마다 실행됩니다.",
                        "classifications": [
                            {
                                "statement": "useEffect는 side effect 수행에 사용된다",
                                "reason": "컨텍스트에서 useEffect가 side effect 수행을 위해 사용된다고 명시됨",
                                "attributed": 1
                            },
                            {
                                "statement": "의존성 배열 생략 시 매 렌더링마다 실행된다",
                                "reason": "컨텍스트에서 의존성 배열을 생략하면 매 렌더링마다 실행된다고 설명됨",
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
        if self.prompt_type == PromptType.KOREAN_TECH:
            return {
                "instruction": """기술 문서 컨텍스트가 질문에 대한 답변 도출에 얼마나 유용했는지 평가하세요.

**기술 문서 유용성 평가 기준:**
- 직접적 해결책 포함 (high precision)
- 관련 배경 지식 제공 (medium precision)
- 간접적 힌트만 제공 (low precision)  
- 관련 없는 정보 (no precision)

**추가 평가 요소:**
- 최신성: 현재 버전/표준과의 일치도
- 완전성: 실행에 필요한 모든 정보 포함 여부
- 정확성: 기술적 오류나 deprecated 정보 여부

유용하면 "1", 그렇지 않으면 "0"으로 판정하고 JSON으로 출력하세요.""",
                "examples": [
                    {
                        "question": "Python 가상환경을 어떻게 만드나요?",
                        "context": "python -m venv myenv 명령으로 가상환경을 생성할 수 있습니다. Python 3.3+에서 지원됩니다.",
                        "answer": "python -m venv 명령을 사용합니다.",
                        "verdict": 1,
                        "reason": "컨텍스트가 질문에 대한 직접적인 답변과 지원 버전 정보를 포함하고 있음"
                    }
                ],
                "language": "korean"
            }
        
        return {}


# 프롬프트 타입별 설명
PROMPT_TYPE_DESCRIPTIONS = {
    PromptType.DEFAULT: "RAGAS 기본 프롬프트 (영어)",
    PromptType.KOREAN_TECH: "한국어 기술 문서 특화 프롬프트",  
    PromptType.MULTILINGUAL_TECH: "한영 혼용 기술 문서 프롬프트",
    PromptType.KOREAN_FORMAL: "한국어 공식 문서 프롬프트"
}

# 사용 가능한 프롬프트 타입 목록
AVAILABLE_PROMPT_TYPES = list(PromptType)