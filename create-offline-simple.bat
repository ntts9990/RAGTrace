@echo off
REM RAGTrace 간단한 오프라인 패키지 생성 스크립트
REM PowerShell이 문제가 있을 경우 사용하는 백업 스크립트

setlocal enabledelayedexpansion

echo ========================================
echo RAGTrace 간단 오프라인 패키지 생성
echo ========================================

REM 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 오류: 관리자 권한으로 실행해주세요.
    echo 우클릭 후 "관리자 권한으로 실행"을 선택하세요.
    pause
    exit /b 1
)

REM 출력 디렉토리 설정
set OutputDir=RAGTrace-Simple-Offline
if exist "%OutputDir%" (
    echo 기존 디렉토리 삭제 중...
    rmdir /s /q "%OutputDir%"
)

echo 📁 출력 디렉토리 생성: %OutputDir%
mkdir "%OutputDir%"
mkdir "%OutputDir%\01_Dependencies"
mkdir "%OutputDir%\02_Source"
mkdir "%OutputDir%\03_Scripts"

REM Python 확인 및 자동 설치
echo.
echo 🐍 Python 환경 확인 중...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python이 설치되어 있지 않습니다.
    echo 자동 설치를 시도합니다...
    
    REM Python 다운로드 및 설치
    echo 📦 Python 3.11.9 다운로드 중...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
    
    if exist "%TEMP%\python-installer.exe" (
        echo 🔧 Python 설치 중 (잠시 기다려주세요...)...
        "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        
        REM 설치 완료 대기
        timeout /t 30 /nobreak >nul
        
        REM PATH 새로고침
        call refreshenv >nul 2>&1
        
        REM 재확인
        python --version >nul 2>&1
        if %errorLevel% neq 0 (
            echo ❌ Python 자동 설치에 실패했습니다.
            echo 수동으로 Python 3.11을 설치하고 다시 실행해주세요.
            echo 다운로드: https://www.python.org/downloads/
            pause
            exit /b 1
        ) else (
            echo ✅ Python 설치 완료!
        )
        
        REM 임시 파일 정리
        del "%TEMP%\python-installer.exe" >nul 2>&1
    ) else (
        echo ❌ Python 다운로드에 실패했습니다.
        echo 수동으로 Python 3.11을 설치하고 다시 실행해주세요.
        echo 다운로드: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM pip 확인
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ pip가 설치되지 않았습니다.
    echo Python 재설치가 필요할 수 있습니다.
    pause
    exit /b 1
)

REM pip 및 UV 설치
echo 📦 pip 업그레이드 중...
python -m pip install --upgrade pip

echo ⚡ UV 패키지 매니저 설치 중...
python -m pip install uv
if %errorLevel% neq 0 (
    echo ⚠️ UV 설치에 실패했지만 계속 진행합니다...
)

REM Requirements 파일 생성
echo.
echo 📝 Requirements 파일 생성 중...
echo # RAGTrace 핵심 패키지 > "%OutputDir%\01_Dependencies\requirements.txt"
echo dependency-injector==4.48.1 >> "%OutputDir%\01_Dependencies\requirements.txt"
echo ragas==0.2.15 >> "%OutputDir%\01_Dependencies\requirements.txt"
echo google-generativeai==0.8.5 >> "%OutputDir%\01_Dependencies\requirements.txt"
echo python-dotenv==1.1.0 >> "%OutputDir%\01_Dependencies\requirements.txt"
echo streamlit==1.45.1 >> "%OutputDir%\01_Dependencies\requirements.txt"
echo pandas==2.3.0 >> "%OutputDir%\01_Dependencies\requirements.txt"
echo numpy==2.3.0 >> "%OutputDir%\01_Dependencies\requirements.txt"
echo plotly==6.1.2 >> "%OutputDir%\01_Dependencies\requirements.txt"
echo requests==2.32.4 >> "%OutputDir%\01_Dependencies\requirements.txt"

REM 패키지 다운로드
echo.
echo 📦 패키지 다운로드 중...
cd "%OutputDir%\01_Dependencies"
pip download -r requirements.txt --dest . --no-deps

REM 소스 코드 복사
echo.
echo 📁 소스 코드 복사 중...
cd ..\..
xcopy "src" "%OutputDir%\02_Source\src\" /E /I /Y >nul
xcopy "data" "%OutputDir%\02_Source\data\" /E /I /Y >nul
copy "cli.py" "%OutputDir%\02_Source\" >nul
copy "run_dashboard.py" "%OutputDir%\02_Source\" >nul
copy "hello.py" "%OutputDir%\02_Source\" >nul
copy "pyproject.toml" "%OutputDir%\02_Source\" >nul
copy ".env.example" "%OutputDir%\02_Source\" >nul

REM 설치 스크립트 생성
echo.
echo 📜 설치 스크립트 생성 중...
echo @echo off > "%OutputDir%\03_Scripts\install.bat"
echo echo RAGTrace 설치 중... >> "%OutputDir%\03_Scripts\install.bat"
echo cd 01_Dependencies >> "%OutputDir%\03_Scripts\install.bat"
echo pip install --no-index --find-links . -r requirements.txt >> "%OutputDir%\03_Scripts\install.bat"
echo cd ..\02_Source >> "%OutputDir%\03_Scripts\install.bat"
echo echo 설치 완료! >> "%OutputDir%\03_Scripts\install.bat"
echo pause >> "%OutputDir%\03_Scripts\install.bat"

REM 실행 스크립트 생성
echo @echo off > "%OutputDir%\03_Scripts\run_dashboard.bat"
echo cd ..\02_Source >> "%OutputDir%\03_Scripts\run_dashboard.bat"
echo python run_dashboard.py >> "%OutputDir%\03_Scripts\run_dashboard.bat"
echo pause >> "%OutputDir%\03_Scripts\run_dashboard.bat"

echo.
echo ✅ 간단한 오프라인 패키지 생성 완료!
echo 📁 출력 위치: %OutputDir%
echo.
echo 📋 사용 방법:
echo 1. %OutputDir% 폴더를 폐쇄망 PC로 복사
echo 2. 03_Scripts\install.bat 실행 (관리자 권한)
echo 3. 03_Scripts\run_dashboard.bat 실행
echo.
pause