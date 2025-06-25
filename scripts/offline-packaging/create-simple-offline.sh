#!/bin/bash

# RAGTrace 간단 오프라인 패키지 생성 (안전 버전)
# 오류 발생 시 즉시 중단
set -e

echo "============================================================"
echo "  RAGTrace 간단 오프라인 패키지 생성 (안전 버전)"
echo "============================================================"
echo

# 색상 정의 (지원되는 경우)
if command -v tput > /dev/null 2>&1; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    CYAN=$(tput setaf 6)
    RESET=$(tput sgr0)
else
    RED="" GREEN="" YELLOW="" BLUE="" CYAN="" RESET=""
fi

# 함수 정의
log_info() {
    echo "${CYAN}📋 $1${RESET}"
}

log_success() {
    echo "${GREEN}✅ $1${RESET}"
}

log_warning() {
    echo "${YELLOW}⚠️ $1${RESET}"
}

log_error() {
    echo "${RED}❌ $1${RESET}"
}

# 사전 조건 확인
check_prerequisites() {
    log_info "사전 조건 확인 중..."
    
    # Python 3.11 확인
    if command -v python3 > /dev/null 2>&1; then
        PYTHON_VER=$(python3 --version 2>&1 | grep -o '3\.11' || true)
        if [ "$PYTHON_VER" = "3.11" ]; then
            log_success "Python 3.11 확인 완료"
        else
            log_error "Python 3.11이 필요합니다. 현재: $(python3 --version)"
            exit 1
        fi
    else
        log_error "Python 3.11이 설치되어 있지 않습니다."
        exit 1
    fi
    
    # pip 확인
    if ! command -v pip > /dev/null 2>&1; then
        log_error "pip이 설치되어 있지 않습니다."
        exit 1
    fi
    log_success "pip 확인 완료"
    
    # 필수 파일 확인
    if [ ! -f "cli.py" ] || [ ! -d "src" ]; then
        log_error "RAGTrace 프로젝트 루트에서 실행하세요."
        exit 1
    fi
    log_success "프로젝트 파일 확인 완료"
    
    echo
}

# 패키지 구조 생성
create_structure() {
    log_info "패키지 구조 생성 중..."
    
    PACKAGE_DIR="RAGTrace-Simple-Offline"
    
    # 기존 디렉토리 제거
    if [ -d "$PACKAGE_DIR" ]; then
        log_warning "기존 디렉토리 제거 중..."
        rm -rf "$PACKAGE_DIR"
    fi
    
    # 디렉토리 생성
    mkdir -p "$PACKAGE_DIR"/{01_Prerequisites,02_Dependencies,03_Source,04_Scripts,05_Documentation}
    
    log_success "패키지 구조 생성 완료"
}

# 소스 파일 복사
copy_source_files() {
    log_info "소스 파일 복사 중..."
    
    SOURCE_FILES=("src" "data" "docs" "cli.py" "run_dashboard.py" "pyproject.toml" ".env.example" "README.md")
    
    for file in "${SOURCE_FILES[@]}"; do
        if [ -e "$file" ]; then
            cp -r "$file" "$PACKAGE_DIR/03_Source/"
            echo "   ✓ $file"
        else
            log_warning "$file 파일이 없습니다."
        fi
    done
    
    log_success "소스 파일 복사 완료"
}

# requirements 파일 생성
create_requirements() {
    log_info "Requirements 파일 생성 중..."
    
    cat > "$PACKAGE_DIR/02_Dependencies/requirements-safe.txt" << 'EOF'
# 핵심 패키지 (안전 버전)
dependency-injector==4.48.1
ragas==0.2.15
google-generativeai==0.8.5
langchain-core==0.3.65
python-dotenv==1.1.0
pydantic==2.11.7
pydantic-settings==2.9.1

# 데이터 처리
pandas==2.2.2
numpy==1.26.4
openpyxl==3.1.5
xlrd==2.0.2

# 웹 UI
streamlit==1.39.0
plotly==5.24.1

# ML/AI (CPU 전용)
sentence-transformers==3.3.1
torch==2.5.1+cpu
transformers==4.46.3

# 유틸리티
requests==2.32.4
psutil==6.1.0
EOF
    
    log_success "Requirements 파일 생성 완료"
}

# 설치 스크립트 생성
create_install_scripts() {
    log_info "설치 스크립트 생성 중..."
    
    # Windows 설치 스크립트 (안전 버전)
    cat > "$PACKAGE_DIR/04_Scripts/install-safe.bat" << 'EOF'
@echo off
chcp 65001 >nul
cls

echo ============================================================
echo   RAGTrace 간단 오프라인 설치 (안전 버전)
echo ============================================================
echo.

:: 오류 발생 시 중단
setlocal EnableDelayedExpansion

:: Python 확인
echo [1/4] Python 확인 중...
python --version >nul 2>&1
if !errorLevel! neq 0 (
    echo       [오류] Python이 설치되어 있지 않습니다.
    echo       https://www.python.org/downloads/ 에서 Python 3.11을 설치하세요.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo !PYTHON_VER! | findstr "3.11" >nul
if !errorLevel! neq 0 (
    echo       [오류] Python 3.11이 필요합니다. 현재: !PYTHON_VER!
    pause
    exit /b 1
)
echo       ✓ Python 확인: !PYTHON_VER!

:: 작업 디렉토리 설정
echo.
echo [2/4] 작업 디렉토리 설정...
cd /d "03_Source"
echo       ✓ 작업 디렉토리: %CD%

:: 가상환경 생성
echo.
echo [3/4] 가상환경 생성 중...
if exist ".venv" (
    echo       기존 가상환경 제거...
    rmdir /s /q ".venv" 2>nul
    timeout /t 2 /nobreak >nul
)

python -m venv .venv
if !errorLevel! neq 0 (
    echo       [오류] 가상환경 생성 실패
    pause
    exit /b 1
)

call .venv\Scripts\activate
echo       ✓ 가상환경 생성 및 활성화 완료

:: 패키지 설치
echo.
echo [4/4] 패키지 설치 중...
echo       CPU 전용 PyTorch와 함께 설치 중... (5-15분 소요)

:: pip 업그레이드
python -m pip install --upgrade pip --quiet

:: 패키지 설치 (인터넷 연결 필요)
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r "..\02_Dependencies\requirements-safe.txt" --timeout 600

if !errorLevel! eq 0 (
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
) else (
    echo.
    echo [오류] 패키지 설치 실패
    echo 인터넷 연결 상태를 확인하고 다시 시도하세요.
)

pause
EOF

    # 실행 스크립트들
    cat > "$PACKAGE_DIR/04_Scripts/run-web.bat" << 'EOF'
@echo off
chcp 65001 >nul
title RAGTrace Web Dashboard

echo RAGTrace 웹 대시보드 시작 중...

if not exist "03_Source\.venv\Scripts\activate.bat" (
    echo [오류] 설치가 완료되지 않았습니다.
    echo        install-safe.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

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

if not exist "03_Source\.venv\Scripts\activate.bat" (
    echo [오류] 설치가 완료되지 않았습니다.
    echo        install-safe.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

cd /d "03_Source"
call .venv\Scripts\activate

echo RAGTrace CLI 모드
echo 사용법: python cli.py --help
echo.

cmd /k
EOF

    log_success "설치 스크립트 생성 완료"
}

# 문서 생성
create_documentation() {
    log_info "문서 생성 중..."
    
    cat > "$PACKAGE_DIR/README-간단설치.txt" << 'EOF'
RAGTrace 간단 오프라인 패키지 (안전 버전)
=====================================

이 패키지는 최소한의 설정으로 RAGTrace를 설치할 수 있도록 구성되었습니다.
인터넷 연결이 필요하지만 설치 과정이 간단합니다.

[시스템 요구사항]
===============
✅ Windows 10 64비트 이상
✅ Python 3.11 (필수)
✅ 인터넷 연결 (설치 시에만)
✅ 5GB 이상 디스크 공간

[설치 순서]
==========
1. Python 3.11 설치
   - https://www.python.org/downloads/release/python-3119/
   - python-3.11.9-amd64.exe 다운로드 후 설치
   - "Add Python to PATH" 체크 필수

2. 이 패키지를 원하는 위치에 압축 해제

3. 04_Scripts/install-safe.bat 실행
   - 가상환경 자동 생성
   - 필요한 패키지 자동 설치 (인터넷 연결 필요)

4. API 키 설정
   - 03_Source/.env.example을 .env로 복사
   - 메모장으로 .env 편집하여 API 키 입력

5. 실행
   - 웹 UI: 04_Scripts/run-web.bat
   - CLI: 04_Scripts/run-cli.bat

[장점]
=====
✅ 간단한 설치 과정
✅ 자동 의존성 해결
✅ 최신 패키지 버전 사용
✅ 오류 처리 강화

[주의사항]
=========
- 최초 설치 시 인터넷 연결 필요
- 설치 완료 후에는 오프라인 실행 가능
- Python 3.11 버전만 지원
- 관리자 권한 불필요

[문제 해결]
==========
설치 실패 시:
- Python 3.11 설치 확인
- 인터넷 연결 상태 확인
- install-safe.bat을 다시 실행

실행 실패 시:
- .env 파일의 API 키 확인
- 가상환경 활성화 확인

생성일: $(date '+%Y-%m-%d %H:%M:%S')
EOF

    # Prerequisites 안내
    cat > "$PACKAGE_DIR/01_Prerequisites/README.txt" << 'EOF'
사전 준비 사항
=============

이 간단 설치 버전은 인터넷 연결을 통해 자동으로 필요한 파일들을 다운로드합니다.

필요한 것:
1. Python 3.11.9 Windows 64비트
   다운로드: https://www.python.org/downloads/release/python-3119/
   
   ⚠️ 중요: 설치 시 "Add Python to PATH" 옵션 체크 필수

2. 인터넷 연결 (설치 시에만)

설치 과정에서 Visual C++ 재배포 가능 패키지가 필요한 경우
자동으로 안내 메시지가 표시됩니다.

간단 설치의 장점:
- 복잡한 사전 다운로드 불필요
- 최신 패키지 버전 자동 설치
- 의존성 충돌 자동 해결
EOF

    log_success "문서 생성 완료"
}

# 패키지 압축
create_package() {
    log_info "패키지 압축 중..."
    
    PACKAGE_SIZE=$(du -sh "$PACKAGE_DIR" 2>/dev/null | cut -f1 || echo "unknown")
    
    # tar.gz 압축
    tar -czf "RAGTrace-Simple-Offline.tar.gz" "$PACKAGE_DIR"
    
    if [ $? -eq 0 ]; then
        ARCHIVE_SIZE=$(ls -lh "RAGTrace-Simple-Offline.tar.gz" | awk '{print $5}')
        log_success "패키지 압축 완료: RAGTrace-Simple-Offline.tar.gz ($ARCHIVE_SIZE)"
    else
        log_error "패키지 압축 실패"
        exit 1
    fi
}

# 메인 실행
main() {
    local start_time=$(date +%s)
    
    echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo
    
    check_prerequisites
    create_structure
    copy_source_files
    create_requirements
    create_install_scripts
    create_documentation
    create_package
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo
    echo "============================================================"
    log_success "간단 오프라인 패키지 생성 완료!"
    echo "============================================================"
    echo
    echo "${YELLOW}📄 출력 파일: RAGTrace-Simple-Offline.tar.gz${RESET}"
    echo "${YELLOW}📏 패키지 크기: $PACKAGE_SIZE${RESET}"
    echo "${YELLOW}⏱️ 소요 시간: ${duration}초${RESET}"
    echo
    echo "${CYAN}📋 다음 단계:${RESET}"
    echo "1. 압축 해제"
    echo "2. Python 3.11 설치"
    echo "3. 04_Scripts/install-safe.bat 실행"
    echo "4. README-간단설치.txt 참고"
    echo
    log_success "간단 설치용 패키지 준비 완료!"
}

# 스크립트 실행
main "$@"