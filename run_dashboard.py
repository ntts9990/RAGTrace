#!/usr/bin/env python3
"""
RAGAS 대시보드 실행 스크립트
"""

import subprocess
import sys
from pathlib import Path

def main():
    """대시보드 실행"""
    dashboard_path = Path(__file__).parent / "dashboard" / "main.py"
    
    print("🚀 RAGAS 대시보드를 시작합니다...")
    print(f"📂 대시보드 경로: {dashboard_path}")
    print("🌐 브라우저에서 http://localhost:8501 으로 접속하세요")
    print("=" * 50)
    
    try:
        # Streamlit 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port=8501",
            "--server.headless=false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✅ 대시보드가 종료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 대시보드 실행 중 오류: {e}")
        print("💡 Streamlit이 설치되어 있는지 확인하세요: pip install streamlit")

if __name__ == "__main__":
    main()