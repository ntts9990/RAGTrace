"""
RAGAS 커스텀 프롬프트 구현체

이 모듈은 RAGAS 프롬프트 클래스들을 상속받아
도메인 특화 프롬프트를 구현합니다.
"""

from typing import List, Dict, Any, Optional

from ragas.metrics._faithfulness import StatementGeneratorPrompt, NLIStatementPrompt
from ragas.metrics._answer_relevance import ResponseRelevancePrompt  
from ragas.metrics._context_recall import ContextRecallClassificationPrompt
from ragas.metrics._context_precision import ContextPrecisionPrompt

from src.domain.prompts import CustomPromptConfig, PromptType


class CustomStatementGeneratorPrompt(StatementGeneratorPrompt):
    """커스텀 Statement Generator 프롬프트"""
    
    def __init__(self, prompt_config: CustomPromptConfig):
        super().__init__()
        
        prompts = prompt_config.get_faithfulness_prompts()
        if 'statement_generator' in prompts:
            config = prompts['statement_generator']
            self.instruction = config['instruction']
            self.language = config.get('language', 'english')
            
            # 예시 데이터 변환
            if 'examples' in config:
                self.examples = self._convert_examples(config['examples'])
    
    def _convert_examples(self, examples_data: List[Dict]) -> List:
        """예시 데이터를 RAGAS 형식으로 변환"""
        from ragas.metrics._faithfulness import StatementGeneratorInput, StatementGeneratorOutput
        
        converted = []
        for example in examples_data:
            input_obj = StatementGeneratorInput(
                question=example['question'],
                answer=example['answer']
            )
            output_obj = StatementGeneratorOutput(
                statements=example['statements']
            )
            converted.append((input_obj, output_obj))
        
        return converted


class CustomNLIStatementPrompt(NLIStatementPrompt):
    """커스텀 NLI Statement 프롬프트"""
    
    def __init__(self, prompt_config: CustomPromptConfig):
        super().__init__()
        
        prompts = prompt_config.get_faithfulness_prompts()
        if 'nli_statement' in prompts:
            config = prompts['nli_statement']
            self.instruction = config['instruction']
            self.language = config.get('language', 'english')
            
            # 예시 데이터 변환
            if 'examples' in config:
                self.examples = self._convert_examples(config['examples'])
    
    def _convert_examples(self, examples_data: List[Dict]) -> List:
        """예시 데이터를 RAGAS 형식으로 변환"""
        from ragas.metrics._faithfulness import NLIStatementInput, NLIStatementOutput, StatementFaithfulnessAnswer
        
        converted = []
        for example in examples_data:
            input_obj = NLIStatementInput(
                context=example['context'],
                statements=[stmt['statement'] for stmt in example['statements']]
            )
            
            output_statements = []
            for stmt in example['statements']:
                output_statements.append(StatementFaithfulnessAnswer(
                    statement=stmt['statement'],
                    reason=stmt['reason'],
                    verdict=stmt['verdict']
                ))
            
            output_obj = NLIStatementOutput(statements=output_statements)
            converted.append((input_obj, output_obj))
        
        return converted


class CustomResponseRelevancePrompt(ResponseRelevancePrompt):
    """커스텀 Response Relevance 프롬프트"""
    
    def __init__(self, prompt_config: CustomPromptConfig):
        super().__init__()
        
        prompts = prompt_config.get_answer_relevancy_prompts()
        if prompts:
            self.instruction = prompts['instruction']
            self.language = prompts.get('language', 'english')
            
            # 예시 데이터 변환
            if 'examples' in prompts:
                self.examples = self._convert_examples(prompts['examples'])
    
    def _convert_examples(self, examples_data: List[Dict]) -> List:
        """예시 데이터를 RAGAS 형식으로 변환"""
        from ragas.metrics._answer_relevance import ResponseRelevanceInput, ResponseRelevanceOutput
        
        converted = []
        for example in examples_data:
            input_obj = ResponseRelevanceInput(response=example['response'])
            output_obj = ResponseRelevanceOutput(
                question=example['question'],
                noncommittal=example['noncommittal']
            )
            converted.append((input_obj, output_obj))
        
        return converted


class CustomContextRecallPrompt(ContextRecallClassificationPrompt):
    """커스텀 Context Recall 프롬프트"""
    
    def __init__(self, prompt_config: CustomPromptConfig):
        super().__init__()
        
        prompts = prompt_config.get_context_recall_prompts()
        if prompts:
            self.instruction = prompts['instruction']
            self.language = prompts.get('language', 'english')
            
            # 예시 데이터 변환
            if 'examples' in prompts:
                self.examples = self._convert_examples(prompts['examples'])
    
    def _convert_examples(self, examples_data: List[Dict]) -> List:
        """예시 데이터를 RAGAS 형식으로 변환"""
        from ragas.metrics._context_recall import QCA, ContextRecallClassifications, ContextRecallClassification
        
        converted = []
        for example in examples_data:
            input_obj = QCA(
                question=example['question'],
                context=example['context'],
                answer=example['answer']
            )
            
            classifications = []
            for cls in example['classifications']:
                classifications.append(ContextRecallClassification(
                    statement=cls['statement'],
                    reason=cls['reason'],
                    attributed=cls['attributed']
                ))
            
            output_obj = ContextRecallClassifications(classifications=classifications)
            converted.append((input_obj, output_obj))
        
        return converted


class CustomContextPrecisionPrompt(ContextPrecisionPrompt):
    """커스텀 Context Precision 프롬프트"""
    
    def __init__(self, prompt_config: CustomPromptConfig):
        super().__init__()
        
        prompts = prompt_config.get_context_precision_prompts()
        if prompts:
            self.instruction = prompts['instruction']
            self.language = prompts.get('language', 'english')
            
            # 예시 데이터 변환
            if 'examples' in prompts:
                self.examples = self._convert_examples(prompts['examples'])
    
    def _convert_examples(self, examples_data: List[Dict]) -> List:
        """예시 데이터를 RAGAS 형식으로 변환"""
        from ragas.metrics._context_precision import QAC, Verification
        
        converted = []
        for example in examples_data:
            input_obj = QAC(
                question=example['question'],
                context=example['context'],
                answer=example['answer']
            )
            
            output_obj = Verification(
                reason=example['reason'],
                verdict=example['verdict']
            )
            
            converted.append((input_obj, output_obj))
        
        return converted


class CustomPromptFactory:
    """커스텀 프롬프트 생성 팩토리"""
    
    @staticmethod
    def create_custom_metrics(prompt_type: PromptType) -> Dict[str, Any]:
        """지정된 프롬프트 타입으로 커스텀 메트릭 생성"""
        from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
        import copy
        
        # 기본 메트릭 복사
        custom_faithfulness = copy.deepcopy(faithfulness)
        custom_answer_relevancy = copy.deepcopy(answer_relevancy)
        custom_context_recall = copy.deepcopy(context_recall)
        custom_context_precision = copy.deepcopy(context_precision)
        
        # 프롬프트 타입이 DEFAULT가 아닌 경우만 커스터마이징
        if prompt_type != PromptType.DEFAULT:
            config = CustomPromptConfig(prompt_type)
            
            # Faithfulness 커스터마이징
            faithfulness_prompts = config.get_faithfulness_prompts()
            if faithfulness_prompts:
                if 'statement_generator' in faithfulness_prompts:
                    custom_faithfulness.statement_generator_prompt = CustomStatementGeneratorPrompt(config)
                if 'nli_statement' in faithfulness_prompts:
                    custom_faithfulness.nli_statements_prompt = CustomNLIStatementPrompt(config)
            
            # Answer Relevancy 커스터마이징
            answer_relevancy_prompts = config.get_answer_relevancy_prompts()
            if answer_relevancy_prompts:
                # Answer Relevancy는 question_generation_prompt 속성이 있는지 확인
                if hasattr(custom_answer_relevancy, 'question_generation_prompt'):
                    custom_answer_relevancy.question_generation_prompt = CustomResponseRelevancePrompt(config)
                elif hasattr(custom_answer_relevancy, 'question_generation'):
                    custom_answer_relevancy.question_generation = CustomResponseRelevancePrompt(config)
            
            # Context Recall 커스터마이징
            context_recall_prompts = config.get_context_recall_prompts()
            if context_recall_prompts:
                custom_context_recall.context_recall_prompt = CustomContextRecallPrompt(config)
            
            # Context Precision 커스터마이징
            context_precision_prompts = config.get_context_precision_prompts()
            if context_precision_prompts:
                custom_context_precision.context_precision_prompt = CustomContextPrecisionPrompt(config)
        
        return {
            'faithfulness': custom_faithfulness,
            'answer_relevancy': custom_answer_relevancy,
            'context_recall': custom_context_recall,
            'context_precision': custom_context_precision
        }
    
    @staticmethod
    def get_available_prompt_types() -> List[PromptType]:
        """사용 가능한 프롬프트 타입 목록 반환"""
        return [PromptType.DEFAULT, PromptType.KOREAN_TECH, PromptType.MULTILINGUAL_TECH]
    
    @staticmethod
    def get_prompt_type_description(prompt_type: PromptType) -> str:
        """프롬프트 타입 설명 반환"""
        from src.domain.prompts import PROMPT_TYPE_DESCRIPTIONS
        return PROMPT_TYPE_DESCRIPTIONS.get(prompt_type, "알 수 없는 프롬프트 타입")