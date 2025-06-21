#!/usr/bin/env python3
"""
RAGTrace 연결 테스트 스크립트
기본 API 키 설정과 의존성을 확인합니다.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_environment():
    """환경 설정 테스트"""
    print("🔍 RAGTrace 환경 테스트")
    print("=" * 40)
    
    # Python 버전 확인
    print(f"🐍 Python 버전: {sys.version}")
    
    # 환경 변수 확인
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env 파일 존재")
    else:
        print("⚠️  .env 파일 없음")
    
    # API 키 확인
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"✅ GEMINI_API_KEY 설정됨 ({len(gemini_key)} 문자)")
    else:
        print("❌ GEMINI_API_KEY 없음")
    
    clova_key = os.getenv("CLOVA_STUDIO_API_KEY") 
    if clova_key:
        print(f"✅ CLOVA_STUDIO_API_KEY 설정됨 ({len(clova_key)} 문자)")
    else:
        print("⚠️  CLOVA_STUDIO_API_KEY 없음 (선택사항)")

def test_imports():
    """핵심 의존성 import 테스트"""
    print("\n📦 의존성 확인")
    print("=" * 40)
    
    dependencies = [
        ("python-dotenv", "dotenv"),
        ("streamlit", "streamlit"), 
        ("ragas", "ragas"),
        ("google-generativeai", "google.generativeai"),
        ("langchain-google-genai", "langchain_google_genai"),
        ("pandas", "pandas"),
        ("plotly", "plotly"),
        ("requests", "requests"),
        ("pydantic", "pydantic"),
        ("dependency-injector", "dependency_injector"),
    ]
    
    for package_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError as e:
            print(f"❌ {package_name}: {e}")

def test_container():
    """DI 컨테이너 테스트"""
    print("\n🔧 컨테이너 테스트")  
    print("=" * 40)
    
    try:
        from src.container import container
        print("✅ 컨테이너 로드 성공")
        
        # LLM 프로바이더 확인
        llm_providers = container.llm_providers()
        print(f"✅ LLM 프로바이더: {list(llm_providers.keys())}")
        
        # 임베딩 프로바이더 확인
        embedding_providers = container.embedding_providers()
        print(f"✅ 임베딩 프로바이더: {list(embedding_providers.keys())}")
        
    except Exception as e:
        print(f"❌ 컨테이너 오류: {e}")

def test_data_files():
    """데이터 파일 확인"""
    print("\n📊 데이터 파일 확인")
    print("=" * 40)
    
    data_files = [
        "data/evaluation_data.json",
        "data/evaluation_data_variant1.json", 
        "data/evaluation_data_small.json",
    ]
    
    for file_path in data_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"⚠️  {file_path} 없음")

def main():
    """메인 테스트 함수"""
    try:
        # .env 파일 로드 시도
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("⚠️  python-dotenv가 설치되지 않음")
        
        test_environment()
        test_imports()
        test_container()
        test_data_files()
        
        print("\n🎉 테스트 완료!")
        print("\n다음 단계:")
        print("1. .env 파일에 API 키 설정")
        print("2. 웹 대시보드 실행: uv run streamlit run src/presentation/web/main.py")
        print("3. CLI 평가 실행: uv run python cli.py evaluate evaluation_data")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()