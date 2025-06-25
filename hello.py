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
        if gemini_key == "mock_key_for_testing":
            print("🧪 GEMINI_API_KEY: 테스트용 모키 키 사용")
        else:
            print(f"✅ GEMINI_API_KEY 설정됨 ({len(gemini_key)} 문자)")
    else:
        print("❌ GEMINI_API_KEY 없음")
    
    clova_key = os.getenv("CLOVA_STUDIO_API_KEY") 
    if clova_key:
        if clova_key == "mock_key_for_testing":
            print("🧪 CLOVA_STUDIO_API_KEY: 테스트용 모키 키 사용")
        else:
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
    
    # 테스트 환경에서는 컨테이너 테스트 스킵
    if os.getenv("TESTING") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        print("🧪 테스트 환경에서 컨테이너 테스트 스킵")
        return
    
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
        print(f"⚠️  컨테이너 오류 (API 키 없음으로 추정): {e}")

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

def prepare_bge_m3_model(force_download=False):
    """BGE-M3 모델 사전 다운로드"""
    print("\n🤖 BGE-M3 모델 준비")
    print("=" * 40)
    
    models_dir = Path("models")
    bge_m3_dir = models_dir / "bge-m3"
    
    # 모델이 이미 존재하고 강제 다운로드가 아닌 경우
    if bge_m3_dir.exists() and not force_download:
        print(f"✅ BGE-M3 모델이 이미 존재: {bge_m3_dir}")
        return True
    
    print("📥 BGE-M3 모델 다운로드 중...")
    
    try:
        # sentence-transformers 확인
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            print("❌ sentence-transformers가 설치되지 않음")
            print("💡 설치 명령어: uv pip install sentence-transformers")
            return False
        
        # 모델 디렉토리 생성
        models_dir.mkdir(exist_ok=True)
        
        # 디바이스 자동 감지
        device = detect_best_device()
        print(f"🔧 사용할 디바이스: {device}")
        
        # BGE-M3 모델 다운로드
        print("⏳ Hugging Face에서 BGE-M3 모델 다운로드 중... (약 2GB)")
        print("   첫 다운로드는 시간이 오래 걸릴 수 있습니다.")
        
        model = SentenceTransformer("BAAI/bge-m3", device=device)
        
        # 로컬 경로에 저장
        if bge_m3_dir.exists():
            import shutil
            shutil.rmtree(bge_m3_dir)
        
        model.save(str(bge_m3_dir))
        
        print(f"✅ BGE-M3 모델 다운로드 완료: {bge_m3_dir}")
        print(f"📊 모델 정보:")
        print(f"   - 최대 시퀀스 길이: {model.max_seq_length}")
        print(f"   - 디바이스: {device}")
        
        # 간단한 테스트
        test_texts = ["Test embedding"]
        embeddings = model.encode(test_texts)
        print(f"   - 임베딩 차원: {len(embeddings[0])}")
        print("✅ BGE-M3 모델 테스트 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ BGE-M3 모델 다운로드 실패: {e}")
        print("💡 해결 방법:")
        print("   1. 인터넷 연결 확인")
        print("   2. 디스크 공간 확인 (최소 3GB 필요)")
        print("   3. sentence-transformers 설치: uv pip install sentence-transformers")
        return False

def detect_best_device():
    """최적의 디바이스 자동 감지"""
    try:
        import torch
        
        # CUDA 지원 확인
        if torch.cuda.is_available():
            return "cuda"
        
        # Apple MPS 지원 확인 
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
            
    except ImportError:
        pass
    
    # 기본값은 CPU
    return "cpu"

def main():
    """메인 테스트 함수"""
    import argparse
    
    # 명령행 인수 처리
    parser = argparse.ArgumentParser(description="RAGTrace 환경 테스트 및 모델 준비")
    parser.add_argument("--prepare-models", action="store_true", 
                       help="BGE-M3 모델 자동 다운로드")
    parser.add_argument("--force-download", action="store_true",
                       help="기존 모델이 있어도 강제로 다시 다운로드")
    parser.add_argument("--skip-tests", action="store_true",
                       help="환경 테스트 건너뛰고 모델만 다운로드")
    
    args = parser.parse_args()
    
    try:
        # .env 파일 로드 시도
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("⚠️  python-dotenv가 설치되지 않음")
        
        # 환경 테스트 (건너뛰기 옵션이 없는 경우에만)
        if not args.skip_tests:
            test_environment()
            test_imports()
            test_container()
            test_data_files()
        
        # BGE-M3 모델 준비
        if args.prepare_models:
            success = prepare_bge_m3_model(force_download=args.force_download)
            if success:
                # .env 파일 업데이트
                update_env_for_local_bge_m3()
            else:
                print("❌ BGE-M3 모델 준비 실패")
                sys.exit(1)
        
        if not args.skip_tests:
            print("\n🎉 테스트 완료!")
        
        print("\n📋 다음 단계:")
        if not args.prepare_models:
            print("• BGE-M3 모델 준비: python hello.py --prepare-models")
        print("• .env 파일에 API 키 설정")
        print("• 웹 대시보드 실행: uv run streamlit run src/presentation/web/main.py")
        print("• CLI 평가 실행: uv run python cli.py evaluate evaluation_data --embedding bge_m3")
        
    except Exception as e:
        print(f"\n❌ 실행 중 오류: {e}")
        sys.exit(1)

def update_env_for_local_bge_m3():
    """BGE-M3 로컬 모델 사용을 위한 .env 파일 업데이트"""
    print("\n⚙️  .env 파일 업데이트")
    print("=" * 40)
    
    env_path = Path(".env")
    models_path = "./models/bge-m3"
    
    if not env_path.exists():
        print("❌ .env 파일이 없습니다. 먼저 .env 파일을 생성하세요.")
        return
    
    # .env 파일 읽기
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # BGE-M3 설정 업데이트
    updated = False
    new_lines = []
    
    for line in lines:
        if line.startswith('# BGE_M3_MODEL_PATH=') or line.startswith('BGE_M3_MODEL_PATH='):
            new_lines.append(f'BGE_M3_MODEL_PATH="{models_path}"\n')
            updated = True
        elif line.startswith('DEFAULT_EMBEDDING='):
            new_lines.append('DEFAULT_EMBEDDING="bge_m3"\n')
        else:
            new_lines.append(line)
    
    # BGE-M3 설정이 없으면 추가
    if not updated:
        new_lines.append(f'\n# BGE-M3 로컬 모델 경로\n')
        new_lines.append(f'BGE_M3_MODEL_PATH="{models_path}"\n')
    
    # .env 파일 쓰기
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ .env 파일 업데이트 완료")
    print(f"   BGE_M3_MODEL_PATH='{models_path}'")
    print(f"   DEFAULT_EMBEDDING='bge_m3'")
    print("💡 이제 BGE-M3 로컬 모델을 사용할 수 있습니다!")

if __name__ == "__main__":
    main()