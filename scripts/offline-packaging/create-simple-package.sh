#!/bin/bash

echo "RAGTrace 폐쇄망 패키지 생성 스크립트"
echo "====================================="

# 패키지 디렉토리 생성
PACKAGE_DIR="RAGTrace-Offline-Package"
echo "1. 패키지 디렉토리 생성: $PACKAGE_DIR"

rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"/{01_Prerequisites,02_Dependencies,03_Source,04_Scripts,05_Documentation}

# 소스 코드 복사
echo "2. 소스 코드 복사 중..."
cp -r src data docs cli.py run_dashboard.py pyproject.toml uv.lock .env.example README.md "$PACKAGE_DIR/03_Source/"

# 필수 Windows 라이브러리만 포함한 requirements 생성
echo "3. Windows용 requirements 파일 생성..."
cp requirements-windows.txt "$PACKAGE_DIR/02_Dependencies/"

# Windows 설치 스크립트 생성
echo "4. 설치 스크립트 생성..."

cat > "$PACKAGE_DIR/04_Scripts/install.bat" << 'EOF'
@echo off
chcp 65001 >nul
echo RAGTrace 설치를 시작합니다...

:: Python 확인
python --version 2>nul | findstr "3.11" >nul
if %errorLevel% neq 0 (
    echo Python 3.11을 먼저 설치하세요.
    echo 01_Prerequisites/python-3.11.9-amd64.exe 실행
    pause
    exit /b 1
)

:: 03_Source로 이동
cd 03_Source

:: 가상환경 생성
python -m venv .venv
call .venv\Scripts\activate

:: CPU 전용 PyTorch와 함께 패키지 설치
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r ..\02_Dependencies\requirements-windows.txt

echo 설치 완료!
echo .env.example을 .env로 복사하고 API 키를 설정하세요.
pause
EOF

# 실행 스크립트 생성
cat > "$PACKAGE_DIR/04_Scripts/run-web.bat" << 'EOF'
@echo off
cd 03_Source
call .venv\Scripts\activate
echo 웹 브라우저에서 http://localhost:8501 로 접속하세요.
streamlit run src/presentation/web/main.py
EOF

cat > "$PACKAGE_DIR/04_Scripts/run-cli.bat" << 'EOF'
@echo off
cd 03_Source
call .venv\Scripts\activate
python cli.py %*
EOF

# README 생성
cat > "$PACKAGE_DIR/README-설치가이드.txt" << 'EOF'
RAGTrace 폐쇄망 설치 패키지
===========================

[설치 순서]
1. Python 3.11.9 설치 (인터넷 연결 필요)
   - https://www.python.org/downloads/release/python-3119/
   - python-3.11.9-amd64.exe 다운로드 후 설치

2. Visual C++ 재배포 가능 패키지 설치 (인터넷 연결 필요)
   - https://aka.ms/vs/17/release/vc_redist.x64.exe
   - 다운로드 후 설치

3. 이 패키지를 폐쇄망 PC로 복사

4. 04_Scripts/install.bat 실행
   - 가상환경 생성 및 패키지 설치
   - 인터넷 연결 필요 (PyPI에서 패키지 다운로드)

5. API 키 설정
   - 03_Source/.env.example을 .env로 복사
   - API 키 입력

6. 실행
   - 웹 UI: 04_Scripts/run-web.bat
   - CLI: 04_Scripts/run-cli.bat

[주의사항]
- Windows 10 64비트 전용
- 최초 설치 시 인터넷 연결 필요
- 설치 후에는 오프라인 실행 가능
EOF

# 압축
echo "5. 패키지 압축 중..."
tar -czf RAGTrace-Offline-Package.tar.gz "$PACKAGE_DIR"

echo "완료!"
echo "생성된 파일: RAGTrace-Offline-Package.tar.gz"
echo ""
echo "패키지 내용:"
echo "- 03_Source: RAGTrace 소스 코드"
echo "- 04_Scripts: 설치/실행 스크립트"
echo "- 02_Dependencies: 핵심 패키지 목록"
echo ""
echo "주의: 최초 설치 시 인터넷 연결이 필요합니다."