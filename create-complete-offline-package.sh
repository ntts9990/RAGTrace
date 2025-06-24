#!/bin/bash

echo "RAGTrace 완전 오프라인 패키지 생성"
echo "=================================="
echo ""

# 패키지 디렉토리 생성
PACKAGE_DIR="RAGTrace-Complete-Offline"
echo "📁 패키지 디렉토리 생성: $PACKAGE_DIR"

rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"/{01_Prerequisites,02_Dependencies/{wheels,extras},03_Source,04_Scripts,05_Documentation}

# 1. 소스 코드 복사
echo "📋 소스 코드 복사 중..."
cp -r src data docs cli.py run_dashboard.py pyproject.toml uv.lock .env.example README.md "$PACKAGE_DIR/03_Source/"

# 2. 핵심 패키지 목록 (Windows 호환성 우선)
cat > "$PACKAGE_DIR/02_Dependencies/requirements-core.txt" << 'EOF'
# 핵심 평가 프레임워크
dependency-injector==4.48.1
ragas==0.2.15
google-generativeai==0.8.5
langchain-core==0.3.65
python-dotenv==1.1.0
pydantic==2.11.7
pydantic-settings==2.9.1

# 데이터 처리
pandas==2.3.0
numpy==2.3.0
openpyxl==3.1.5
xlrd==2.0.2

# 웹 UI
streamlit==1.45.1
plotly==6.1.2

# ML/AI (CPU 전용)
sentence-transformers==4.1.0
torch==2.7.1+cpu
transformers==4.52.4

# 유틸리티
requests==2.32.4
psutil==7.0.0
EOF

# 3. Windows용 wheel 다운로드 (멀티 플랫폼)
echo "🔄 Windows용 패키지 다운로드 중..."
echo "   - Windows 64비트 전용"
echo "   - Python 3.11 호환"
echo "   - CPU 전용 PyTorch"

# 기본 패키지 다운로드
pip download \
    --platform win_amd64 \
    --python-version 3.11 \
    --only-binary :all: \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r "$PACKAGE_DIR/02_Dependencies/requirements-core.txt" \
    -d "$PACKAGE_DIR/02_Dependencies/wheels/" \
    --timeout 600 \
    2>&1 | tee "$PACKAGE_DIR/02_Dependencies/download.log"

# 추가 의존성 다운로드 (recursive)
echo "🔄 의존성 패키지 다운로드 중..."
pip download \
    --platform win_amd64 \
    --python-version 3.11 \
    --only-binary :all: \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    streamlit pandas numpy torch sentence-transformers ragas dependency-injector \
    -d "$PACKAGE_DIR/02_Dependencies/wheels/" \
    --timeout 600 \
    2>&1 | tee -a "$PACKAGE_DIR/02_Dependencies/download.log"

# 4. 설치 스크립트 생성
echo "📝 설치 스크립트 생성 중..."

# Windows 설치 스크립트
cat > "$PACKAGE_DIR/04_Scripts/install.bat" << 'EOF'
@echo off
chcp 65001 >nul
cls

echo ============================================================
echo   RAGTrace 완전 오프라인 설치
echo ============================================================
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [오류] 관리자 권한이 필요합니다.
    echo        마우스 오른쪽 버튼으로 "관리자 권한으로 실행"
    pause
    exit /b 1
)

:: Python 확인
echo [1/5] Python 3.11 확인 중...
python --version 2>nul | findstr "3.11" >nul
if %errorLevel% neq 0 (
    echo       Python 3.11이 설치되어 있지 않습니다.
    echo       01_Prerequisites 폴더의 python-3.11.9-amd64.exe를 먼저 설치하세요.
    pause
    exit /b 1
)
echo       ✓ Python 3.11 확인 완료

:: VC++ 확인
echo.
echo [2/5] Visual C++ 재배포 가능 패키지 설치
echo       01_Prerequisites\vc_redist.x64.exe를 실행하세요.
pause

:: 소스 디렉토리로 이동
echo.
echo [3/5] 작업 디렉토리 설정
cd /d "03_Source"
echo       ✓ 작업 디렉토리: %CD%

:: 가상환경 생성
echo.
echo [4/5] Python 가상환경 생성 중...
if exist ".venv" (
    echo       기존 가상환경 제거 중...
    rmdir /s /q ".venv"
)
python -m venv .venv
if %errorLevel% neq 0 (
    echo       [오류] 가상환경 생성 실패
    pause
    exit /b 1
)
echo       ✓ 가상환경 생성 완료

:: 가상환경 활성화 및 패키지 설치
echo.
echo [5/5] 패키지 설치 중... (오프라인)
call .venv\Scripts\activate

:: pip 업그레이드 (오프라인)
echo       pip 업그레이드 중...
python -m pip install --upgrade pip --no-index --find-links "..\02_Dependencies\wheels"

:: 패키지 설치 (완전 오프라인)
echo       패키지 설치 중... (5-15분 소요)
pip install --no-index --find-links "..\02_Dependencies\wheels" --no-deps -r "..\02_Dependencies\requirements-core.txt"

if %errorLevel% eq 0 (
    echo.
    echo ============================================================
    echo   설치 완료!
    echo ============================================================
    echo.
    echo   다음 단계:
    echo   1. .env.example을 .env로 복사
    echo   2. .env 파일에 API 키 입력
    echo   3. 실행: ..\04_Scripts\run-web.bat
    echo.
    echo   또는 검증: python ..\04_Scripts\verify.py
) else (
    echo.
    echo [오류] 패키지 설치 실패
    echo 02_Dependencies\download.log 파일을 확인하세요.
)

pause
EOF

# 실행 스크립트들
cat > "$PACKAGE_DIR/04_Scripts/run-web.bat" << 'EOF'
@echo off
chcp 65001 >nul
title RAGTrace Web Dashboard

echo RAGTrace 웹 대시보드 시작 중...
cd /d "03_Source"
call .venv\Scripts\activate

echo.
echo ============================================================
echo   RAGTrace 웹 대시보드
echo ============================================================
echo   URL: http://localhost:8501
echo   종료: Ctrl+C
echo ============================================================
echo.

streamlit run src/presentation/web/main.py
pause
EOF

cat > "$PACKAGE_DIR/04_Scripts/run-cli.bat" << 'EOF'
@echo off
chcp 65001 >nul
title RAGTrace CLI

cd /d "03_Source"
call .venv\Scripts\activate

echo RAGTrace CLI 모드
echo 사용법: python cli.py --help
echo.

cmd /k
EOF

# 5. 검증 스크립트
cat > "$PACKAGE_DIR/04_Scripts/verify.py" << 'EOF'
#!/usr/bin/env python3
"""RAGTrace 완전 오프라인 설치 검증"""

import sys
import os
import importlib
from pathlib import Path

def main():
    print("=" * 60)
    print("  RAGTrace 오프라인 설치 검증")
    print("=" * 60)
    print()
    
    # 경로 확인
    if not Path("cli.py").exists():
        print("❌ 03_Source 디렉토리에서 실행하세요.")
        return False
    
    # Python 버전
    print(f"🐍 Python: {sys.version}")
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 이상 필요")
        return False
    
    # 가상환경 확인
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"🔧 가상환경: {'✅ 활성화됨' if venv_active else '❌ 미활성화'}")
    
    # 핵심 패키지 확인
    core_packages = [
        'streamlit', 'pandas', 'numpy', 'torch', 
        'sentence_transformers', 'ragas', 'dependency_injector',
        'plotly', 'openpyxl', 'requests'
    ]
    
    print("\n📦 핵심 패키지 확인:")
    all_ok = True
    for pkg in core_packages:
        try:
            module = importlib.import_module(pkg.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            print(f"   ✅ {pkg}: {version}")
        except ImportError:
            print(f"   ❌ {pkg}: 미설치")
            all_ok = False
    
    # PyTorch CPU 확인
    try:
        import torch
        is_cpu = not torch.cuda.is_available()
        print(f"\n🔥 PyTorch: {'✅ CPU 전용' if is_cpu else '⚠️ GPU 감지됨'}")
    except:
        print("\n🔥 PyTorch: ❌ 미설치")
        all_ok = False
    
    # 환경 파일 확인
    env_exists = Path(".env").exists()
    env_example_exists = Path(".env.example").exists()
    print(f"\n⚙️ 환경 설정: {'.env' if env_exists else '.env.example' if env_example_exists else '❌ 없음'}")
    
    if all_ok:
        print("\n" + "=" * 60)
        print("✅ 모든 검증 통과! RAGTrace 사용 준비 완료")
        print("=" * 60)
        print("\n실행 방법:")
        print("  웹 UI: run-web.bat")
        print("  CLI: run-cli.bat")
    else:
        print("\n❌ 일부 패키지가 누락되었습니다.")
        print("install.bat을 다시 실행하세요.")
    
    return all_ok

if __name__ == "__main__":
    main()
    input("\nEnter 키를 눌러 종료...")
EOF

# 6. 문서 생성
echo "📚 문서 생성 중..."

cat > "$PACKAGE_DIR/README-완전오프라인설치.txt" << 'EOF'
RAGTrace 완전 오프라인 패키지
============================

이 패키지는 인터넷이 완전히 차단된 폐쇄망 환경에서
RAGTrace를 설치하고 실행하기 위한 모든 파일을 포함합니다.

[사전 준비 - 인터넷 연결된 PC에서]
1. Python 3.11.9 Windows 64비트 다운로드
   https://www.python.org/downloads/release/python-3119/
   → python-3.11.9-amd64.exe

2. Visual C++ 재배포 가능 패키지 다운로드  
   https://aka.ms/vs/17/release/vc_redist.x64.exe
   → vc_redist.x64.exe

3. 두 파일을 01_Prerequisites 폴더에 복사

[폐쇄망 설치 순서]
1. 전체 패키지를 폐쇄망 PC로 복사
2. 01_Prerequisites/python-3.11.9-amd64.exe 설치
3. 01_Prerequisites/vc_redist.x64.exe 설치  
4. 04_Scripts/install.bat을 관리자 권한으로 실행
5. .env.example을 .env로 복사하고 API 키 설정
6. 04_Scripts/verify.py로 설치 검증

[실행]
- 웹 UI: 04_Scripts/run-web.bat
- CLI: 04_Scripts/run-cli.bat

[패키지 구성]
- 01_Prerequisites: Python 및 VC++ 설치 파일 (사용자가 추가)
- 02_Dependencies: Python 패키지 wheel 파일 (완전 오프라인)
- 03_Source: RAGTrace 소스 코드
- 04_Scripts: 설치/실행/검증 스크립트
- 05_Documentation: 상세 문서

[특징]
✅ 완전 오프라인 설치 (인터넷 연결 불필요)
✅ Windows 10 64비트 전용
✅ CPU 전용 (GPU 불필요)
✅ 모든 의존성 사전 포함
✅ HCX-005 + BGE-M3 API 지원

[주의사항]
- Python 3.11.9 필수
- 관리자 권한으로 설치 필요
- 약 10GB 디스크 공간 필요
- API 키는 별도 설정 필요

생성일: $(date '+%Y-%m-%d %H:%M:%S')
EOF

# 7. Prerequisites 안내 파일
cat > "$PACKAGE_DIR/01_Prerequisites/README.txt" << 'EOF'
필수 설치 파일 다운로드 안내
==========================

폐쇄망 설치를 위해 다음 파일들을 이 폴더에 복사하세요:

1. python-3.11.9-amd64.exe
   다운로드: https://www.python.org/downloads/release/python-3119/
   크기: 약 30MB

2. vc_redist.x64.exe  
   다운로드: https://aka.ms/vs/17/release/vc_redist.x64.exe
   크기: 약 14MB

두 파일 모두 인터넷이 연결된 PC에서 다운로드 후
이 폴더에 복사해야 합니다.
EOF

# 8. 패키지 정보 출력
echo ""
echo "📊 패키지 생성 결과:"
echo "   디렉토리: $PACKAGE_DIR"
echo "   wheel 파일: $(ls -1 "$PACKAGE_DIR/02_Dependencies/wheels/" 2>/dev/null | wc -l | tr -d ' ') 개"
echo "   크기: $(du -sh "$PACKAGE_DIR" 2>/dev/null | cut -f1)"

# 9. 압축
echo ""
echo "📦 패키지 압축 중..."
tar -czf "RAGTrace-Complete-Offline.tar.gz" "$PACKAGE_DIR"

echo ""
echo "✅ 완전 오프라인 패키지 생성 완료!"
echo "   파일: RAGTrace-Complete-Offline.tar.gz"
echo "   크기: $(ls -lh RAGTrace-Complete-Offline.tar.gz | awk '{print $5}')"

echo ""
echo "📋 다음 단계:"
echo "1. 01_Prerequisites 폴더에 Python과 VC++ 파일 추가"
echo "2. 패키지를 폐쇄망 PC로 전송"  
echo "3. README-완전오프라인설치.txt 참고하여 설치"