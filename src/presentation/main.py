import logging
import sys

from src.container import container


def main():
    """
    애플리케이션의 메인 실행 함수.
    의존성 주입 컨테이너를 사용하여 평가 서비스를 실행합니다.
    """
    print("RAGTrace 평가를 시작합니다...")

    try:
        # 1. 컨테이너에서 유스케이스 가져오기 (기본 LLM 사용)
        evaluation_use_case = container.run_evaluation_use_case()

        # 2. 평가 실행 (기본 데이터셋 사용)
        print("평가를 진행 중입니다. 잠시만 기다려주세요...")
        evaluation_result = evaluation_use_case.execute(
            dataset_name="evaluation_data",
            prompt_type=None  # 기본 프롬프트 사용
        )

        # 3. 결과 출력
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
