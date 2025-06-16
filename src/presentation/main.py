import logging
import sys

from src.application.use_cases import RunEvaluationUseCase
from src.infrastructure.evaluation import RagasEvalAdapter
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.repository.file_adapter import FileRepositoryAdapter
from src.utils.paths import DEFAULT_EVALUATION_DATA


def main():
    """
    애플리케이션의 메인 실행 함수.
    의존성을 주입하고 평가 서비스를 실행합니다.
    """
    print("RAGTrace 평가를 시작합니다...")

    try:
        # 1. 의존성 객체 생성 (Adapters)
        # 무료 티어는 분당 10 요청으로 제한 - 안전하게 분당 8 요청으로 설정
        llm_adapter = GeminiAdapter(
            model_name="gemini-2.5-flash-preview-05-20",
            requests_per_minute=1000,  # Tier 1: 1000 RPM
        )

        # Repository 어댑터: 중앙 경로 관리 사용
        repository_adapter = FileRepositoryAdapter(file_path=str(DEFAULT_EVALUATION_DATA))

        ragas_eval_adapter = RagasEvalAdapter()

        # 2. 유스케이스에 의존성 주입
        evaluation_use_case = RunEvaluationUseCase(
            llm_port=llm_adapter,
            repository_port=repository_adapter,
            evaluation_runner=ragas_eval_adapter,
        )

        # 3. 평가 실행
        print("평가를 진행 중입니다. 잠시만 기다려주세요...")
        evaluation_result = evaluation_use_case.execute()

        # 4. 결과 출력
        print("\n--- 평가 결과 ---")
        print(f"- faithfulness: {evaluation_result.faithfulness:.4f}")
        print(f"- answer_relevancy: {evaluation_result.answer_relevancy:.4f}")
        print(f"- context_recall: {evaluation_result.context_recall:.4f}")
        print(f"- context_precision: {evaluation_result.context_precision:.4f}")
        print("--------------------")
        print(f"** 종합 점수 (ragas_score): {evaluation_result.ragas_score:.4f} **")
        print("--------------------")

    except Exception as e:
        logging.error(f"평가 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
