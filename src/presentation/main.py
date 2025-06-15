import os
import sys

from src.application.use_cases import RunEvaluationUseCase
from src.infrastructure.evaluation import RagasEvalAdapter
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.repository.file_adapter import FileRepositoryAdapter

# 프로젝트의 루트 디렉토리를 Python 경로에 추가하여,
# 'src' 모듈을 찾을 수 있도록 설정합니다.
# 이 스크립트를 직접 실행할 때 필요합니다.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def main():
    """
    애플리케이션의 메인 실행 함수.
    의존성을 주입하고 평가 서비스를 실행합니다.
    """
    print("RAGAS 평가를 시작합니다...")

    try:
        # 1. 의존성 객체 생성 (Adapters)
        # 무료 티어는 분당 10 요청으로 제한 - 안전하게 분당 8 요청으로 설정
        llm_adapter = GeminiAdapter(
            model_name="gemini-2.5-flash-preview-05-20",
            requests_per_minute=1000,  # Tier 1: 1000 RPM
        )

        # Repository 어댑터: 로컬 파일 사용
        repository_adapter = FileRepositoryAdapter(
            file_path="data/evaluation_data.json"
        )

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
        print(f"\n예기치 않은 오류가 발생했습니다: {e}")
        print(f"오류 타입: {type(e).__name__}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
