#!/usr/bin/env python3
"""
Enhanced RAGTrace Dashboard Launcher

main 브랜치의 모든 기능을 통합한 완전한 대시보드를 실행합니다.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """향상된 Streamlit 대시보드 실행"""
    dashboard_path = Path("src/presentation/web/main.py")
    
    if not dashboard_path.exists():
        print(f"❌ 대시보드 파일을 찾을 수 없습니다: {dashboard_path}")
        sys.exit(1)
    
    print("🚀 RAGTrace 향상된 대시보드를 시작합니다...")
    print("📋 포함된 기능:")
    print("   - 📊 Overview: 메트릭 카드, 차트, 트렌드 분석")
    print("   - 🚀 New Evaluation: 완전한 평가 실행 (LLM/임베딩/프롬프트 선택)")
    print("   - 📈 Historical: 평가 이력 및 비교 분석")
    print("   - 📚 Detailed Analysis: 상세 분석 (컴포넌트 지연 로딩)")
    print("   - 📖 Metrics Explanation: RAGAS 메트릭 가이드")
    print("   - ⚡ Performance: 성능 모니터링")
    print()
    
    # torch 에러 방지를 위한 환경 변수 설정
    env = os.environ.copy()
    env['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
    env['STREAMLIT_LOGGER_LEVEL'] = 'error'
    env['STREAMLIT_CLIENT_SHOW_ERROR_DETAILS'] = 'false'
    
    try:
        subprocess.run([
            "streamlit", "run", str(dashboard_path),
            "--server.port=8503",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.fileWatcherType=none",  # 올바른 옵션 이름
            "--logger.level=error"
        ], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ 대시보드 실행 중 오류 발생: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ streamlit을 찾을 수 없습니다. 다음 명령으로 설치하세요:")
        print("   pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 대시보드를 종료합니다.")

if __name__ == "__main__":
    main() 