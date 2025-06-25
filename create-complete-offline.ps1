# RAGTrace 완전 오프라인 패키지 생성 스크립트
# 폐쇄망에서 아무것도 설치되지 않은 Windows PC에서 바로 실행 가능한 패키지 생성
# PowerShell 관리자 권한으로 실행 필요
# PowerShell 5.1+ 호환

param(
    [string]$OutputDir = "RAGTrace-Complete-Offline",
    [switch]$IncludeBGE = $false,
    [switch]$Verbose = $false
)

# 오류 발생 시 스크립트 중단
$ErrorActionPreference = "Stop"

# PowerShell 버전 확인
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "PowerShell 5.0 이상이 필요합니다. 현재 버전: $($PSVersionTable.PSVersion)"
    exit 1
}

function Write-SafeHost {
    param([string]$Message, [string]$Color = "White")
    try {
        Write-Host $Message -ForegroundColor $Color
    } catch {
        Write-Output $Message
    }
}

function Test-PowerShellCompatibility {
    Write-SafeHost "🔍 PowerShell 호환성 확인 중..." -Color "Cyan"
    
    $psVersion = $PSVersionTable.PSVersion
    Write-SafeHost "   PowerShell 버전: $psVersion" -Color "Yellow"
    
    if ($psVersion.Major -eq 5 -and $psVersion.Minor -eq 1) {
        Write-SafeHost "   ✓ Windows PowerShell 5.1 감지됨" -Color "Green"
        Write-SafeHost "   ℹ️ 최적의 호환성을 위해 PowerShell 7+을 권장합니다" -Color "Yellow"
        return $true
    } elseif ($psVersion.Major -ge 7) {
        Write-SafeHost "   ✓ PowerShell Core 7+ 감지됨" -Color "Green"
        return $true
    } else {
        Write-SafeHost "   ❌ 지원되지 않는 PowerShell 버전입니다" -Color "Red"
        Write-SafeHost "   💡 대안: create-offline-simple.bat 스크립트를 사용해보세요" -Color "Yellow"
        return $false
    }
}

function Test-Prerequisites {
    Write-SafeHost "============================================================" -Color "Green"
    Write-SafeHost "  RAGTrace 완전 오프라인 패키지 생성기" -Color "Green"
    Write-SafeHost "  폐쇄망 전용 - 모든 구성요소 포함" -Color "Green"
    Write-SafeHost "============================================================" -Color "Green"
    Write-SafeHost ""
    
    # 관리자 권한 확인
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-SafeHost "❌ 오류: 관리자 권한이 필요합니다." -Color "Red"
        Write-SafeHost "   PowerShell을 관리자 권한으로 실행하세요." -Color "Yellow"
        exit 1
    }
    Write-SafeHost "✅ 관리자 권한 확인 완료" -Color "Green"
    
    # PowerShell 호환성 확인
    if (-not (Test-PowerShellCompatibility)) {
        Write-SafeHost ""
        Write-SafeHost "❌ PowerShell 호환성 문제가 발견되었습니다." -Color "Red"
        Write-SafeHost "💡 해결 방법:" -Color "Yellow"
        Write-SafeHost "   1. PowerShell 7+ 설치: https://github.com/PowerShell/PowerShell/releases" -Color "Yellow"
        Write-SafeHost "   2. 또는 간단한 배치 스크립트 사용: create-offline-simple.bat" -Color "Yellow"
        exit 1
    }
    
    # Python 확인
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion -match "Python 3\.11") {
            Write-SafeHost "✅ Python 3.11 확인: $pythonVersion" -Color "Green"
        } else {
            Write-SafeHost "❌ Python 3.11이 필요합니다. 현재: $pythonVersion" -Color "Red"
            Write-SafeHost "   https://www.python.org/downloads/release/python-3119/ 에서 다운로드하세요." -Color "Yellow"
            exit 1
        }
    } catch {
        Write-SafeHost "❌ Python이 설치되어 있지 않거나 PATH에 없습니다." -Color "Red"
        Write-SafeHost "   Python 3.11을 설치하고 PATH에 추가하세요." -Color "Yellow"
        exit 1
    }
    
    # 인터넷 연결 확인
    try {
        $testConnection = Test-NetConnection -ComputerName "pypi.org" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($testConnection) {
            Write-SafeHost "✅ 인터넷 연결 확인 완료" -Color "Green"
        } else {
            Write-SafeHost "❌ PyPI 접근 불가. 인터넷 연결을 확인하세요." -Color "Red"
            exit 1
        }
    } catch {
        Write-SafeHost "⚠️ 네트워크 연결 확인 실패. 계속 진행합니다." -Color "Yellow"
    }
    
    Write-SafeHost ""
}

function Initialize-CompletePackageStructure {
    Write-SafeHost "📁 완전 패키지 구조 초기화 중..." -Color "Cyan"
    
    # 기존 디렉토리 안전하게 제거
    if (Test-Path $OutputDir) {
        Write-SafeHost "   기존 디렉토리 제거 중..." -Color "Yellow"
        try {
            Remove-Item -Path $OutputDir -Recurse -Force -ErrorAction Stop
            Start-Sleep -Seconds 1
        } catch {
            Write-SafeHost "❌ 기존 디렉토리 제거 실패: $_" -Color "Red"
            exit 1
        }
    }
    
    # 새로운 디렉토리 구조 생성
    $dirs = @(
        "$OutputDir\00_Prerequisites",
        "$OutputDir\01_Dependencies\wheels",
        "$OutputDir\02_Source", 
        "$OutputDir\03_Models",
        "$OutputDir\04_Scripts"
    )
    
    foreach ($dir in $dirs) {
        try {
            New-Item -ItemType Directory -Force -Path $dir -ErrorAction Stop | Out-Null
            Write-SafeHost "   ✓ $dir" -Color "Green"
        } catch {
            Write-SafeHost "❌ 디렉토리 생성 실패: $dir - $_" -Color "Red"
            exit 1
        }
    }
}

function Download-PythonInstaller {
    Write-SafeHost "🐍 Python 3.11.9 설치파일 다운로드 중..." -Color "Cyan"
    
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $pythonPath = "$OutputDir\00_Prerequisites\python-3.11.9-amd64.exe"
    
    try {
        Write-SafeHost "   다운로드 중: python-3.11.9-amd64.exe (약 30MB)" -Color "Yellow"
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonPath -ErrorAction Stop
        
        $fileSize = (Get-Item $pythonPath).Length / 1MB
        Write-SafeHost "   ✓ Python 설치파일 다운로드 완료 ($([math]::Round($fileSize, 1)) MB)" -Color "Green"
    } catch {
        Write-SafeHost "❌ Python 설치파일 다운로드 실패: $_" -Color "Red"
        Write-SafeHost "   수동으로 다운로드하여 00_Prerequisites 폴더에 복사하세요." -Color "Yellow"
    }
}

function Download-VCRedist {
    Write-SafeHost "🔧 Visual C++ 재배포 패키지 다운로드 중..." -Color "Cyan"
    
    $vcUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    $vcPath = "$OutputDir\00_Prerequisites\vc_redist.x64.exe"
    
    try {
        Write-SafeHost "   다운로드 중: vc_redist.x64.exe (약 14MB)" -Color "Yellow"
        Invoke-WebRequest -Uri $vcUrl -OutFile $vcPath -ErrorAction Stop
        
        $fileSize = (Get-Item $vcPath).Length / 1MB
        Write-SafeHost "   ✓ VC++ 재배포 패키지 다운로드 완료 ($([math]::Round($fileSize, 1)) MB)" -Color "Green"
    } catch {
        Write-SafeHost "❌ VC++ 재배포 패키지 다운로드 실패: $_" -Color "Red"
        Write-SafeHost "   수동으로 다운로드하여 00_Prerequisites 폴더에 복사하세요." -Color "Yellow"
    }
}

function Copy-SourceFiles {
    Write-SafeHost "📋 RAGTrace 소스 코드 복사 중..." -Color "Cyan"
    
    $sourceItems = @("src", "data", "cli.py", "run_dashboard.py", "pyproject.toml", "uv.lock", ".env.example", "README.md", "requirements.txt")
    $copiedCount = 0
    
    foreach ($item in $sourceItems) {
        if (Test-Path $item) {
            try {
                Copy-Item -Path $item -Destination "$OutputDir\02_Source\" -Recurse -Force -ErrorAction Stop
                Write-SafeHost "   ✓ $item" -Color "Green"
                $copiedCount++
            } catch {
                Write-SafeHost "   ⚠️ $item 복사 실패: $_" -Color "Yellow"
            }
        } else {
            Write-SafeHost "   ⚠️ $item 파일이 없습니다" -Color "Yellow"
        }
    }
    
    if ($copiedCount -lt 5) {
        Write-SafeHost "❌ 필수 소스 파일이 부족합니다. RAGTrace 프로젝트 루트에서 실행하세요." -Color "Red"
        exit 1
    }
    
    Write-SafeHost "   📊 총 $copiedCount 개 파일/폴더 복사 완료" -Color "Green"
}

function Create-CompleteRequirements {
    Write-SafeHost "📝 완전한 Requirements 파일 생성 중..." -Color "Cyan"
    
    # 안정적이고 완전한 버전으로 고정
    $completeRequirements = @"
# 핵심 평가 프레임워크
dependency-injector==4.48.1
ragas==0.2.15
google-generativeai==0.8.5
langchain-core==0.3.65
python-dotenv==1.1.0
pydantic==2.11.7
pydantic-settings==2.9.1

# 데이터 처리 및 분석
pandas==2.3.0
numpy==2.3.0
openpyxl==3.1.5
xlrd==2.0.2
datasets==3.6.0
scipy==1.15.0
scikit-learn==1.6.0

# 웹 UI 및 시각화
streamlit==1.45.1
plotly==6.1.2

# 머신러닝 및 임베딩 (CPU 전용)
sentence-transformers==4.1.0
torch==2.7.1+cpu
transformers==4.47.0

# 유틸리티
requests==2.32.4
psutil==7.0.0
chardet==5.2.0

# 개발 도구 (선택사항)
pytest==8.1.1
black==24.3.0
"@

    try {
        $completeRequirements | Out-File -FilePath "$OutputDir\01_Dependencies\requirements.txt" -Encoding UTF8 -ErrorAction Stop
        Write-SafeHost "   ✓ 완전한 requirements.txt 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ Requirements 파일 생성 실패: $_" -Color "Red"
        exit 1
    }
}

function Download-AllPythonPackages {
    Write-SafeHost "📦 모든 Python 패키지 다운로드 시작..." -Color "Cyan"
    Write-SafeHost "   - 플랫폼: Windows 64비트" -Color "White"
    Write-SafeHost "   - Python: 3.11" -Color "White"
    Write-SafeHost "   - PyTorch: CPU 전용" -Color "White"
    Write-SafeHost "   - 예상 시간: 30-60분" -Color "White"
    Write-SafeHost ""
    
    $originalLocation = Get-Location
    
    try {
        Set-Location "$OutputDir\01_Dependencies"
        
        # pip 업그레이드
        Write-SafeHost "🔧 pip 업그레이드 중..." -Color "Yellow"
        python -m pip install --upgrade pip --quiet
        
        # 메인 패키지들 다운로드
        Write-SafeHost "📥 1단계: 핵심 패키지 다운로드..." -Color "Yellow"
        
        $downloadCmd = "pip download --platform win_amd64 --python-version 3.11 --only-binary :all: --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt -d wheels --timeout 1800 --retries 10"
        
        if ($Verbose) {
            Write-SafeHost "   실행 명령: $downloadCmd" -Color "Gray"
        }
        
        Invoke-Expression $downloadCmd
        
        # 추가 의존성 다운로드
        Write-SafeHost "📥 2단계: 의존성 패키지 다운로드..." -Color "Yellow"
        
        $additionalPackages = @(
            "setuptools",
            "wheel", 
            "pip",
            "certifi",
            "urllib3",
            "charset-normalizer",
            "idna"
        )
        
        foreach ($pkg in $additionalPackages) {
            try {
                Write-SafeHost "   → $pkg" -Color "Gray"
                pip download --platform win_amd64 --python-version 3.11 --only-binary :all: $pkg -d wheels --timeout 300 --quiet
            } catch {
                Write-SafeHost "   ⚠️ $pkg 다운로드 실패" -Color "Yellow"
            }
        }
        
        # 다운로드된 패키지 수 확인
        $wheelCount = (Get-ChildItem "wheels" -Filter "*.whl" -ErrorAction SilentlyContinue).Count
        Write-SafeHost "   ✅ 다운로드 완료: $wheelCount 개 wheel 파일" -Color "Green"
        
        if ($wheelCount -lt 50) {
            Write-SafeHost "⚠️ 다운로드된 패키지가 적습니다. 네트워크 상태를 확인하세요." -Color "Yellow"
        }
        
        # 체크섬 파일 생성
        Write-SafeHost "🔒 패키지 무결성 체크섬 생성 중..." -Color "Yellow"
        $checksumContent = ""
        Get-ChildItem "wheels" -Filter "*.whl" | ForEach-Object {
            $hash = Get-FileHash $_.FullName -Algorithm SHA256
            $checksumContent += "$($_.Name): $($hash.Hash)`n"
        }
        $checksumContent | Out-File -FilePath "checksums.txt" -Encoding UTF8
        
        Write-SafeHost "   ✓ 체크섬 파일 생성 완료" -Color "Green"
        
    } catch {
        Write-SafeHost "❌ 패키지 다운로드 중 오류: $_" -Color "Red"
        Write-SafeHost "   일부 패키지가 누락될 수 있습니다." -Color "Yellow"
    } finally {
        Set-Location $originalLocation
    }
}

function Download-BGEModel {
    if (-not $IncludeBGE) {
        Write-SafeHost "🤖 BGE-M3 모델 다운로드 생략됨 (-IncludeBGE 플래그 사용 시 포함)" -Color "Yellow"
        return
    }
    
    Write-SafeHost "🤖 BGE-M3 모델 다운로드 중..." -Color "Cyan"
    Write-SafeHost "   경고: 약 2GB 크기입니다." -Color "Yellow"
    
    try {
        $modelPath = "$OutputDir\03_Models\bge-m3"
        
        # Python으로 BGE-M3 모델 다운로드 - 임시 파일 생성 방식
        $tempPyFile = "$env:TEMP\download_bge_m3.py"
        $modelPathEscaped = $modelPath -replace '\\', '\\'
        $pythonCode = @(
            "import os",
            "from sentence_transformers import SentenceTransformer",
            "",
            "print('BGE-M3 모델 다운로드 시작...')",
            "model = SentenceTransformer('BAAI/bge-m3')",
            "model.save(r'$modelPathEscaped')",
            "print('BGE-M3 모델 다운로드 완료')"
        )
        
        # Python 파일 생성
        $pythonCode | Out-File -FilePath $tempPyFile -Encoding UTF8
        
        # Python 실행
        python $tempPyFile
        
        # 임시 파일 삭제
        Remove-Item $tempPyFile -ErrorAction SilentlyContinue
        
        if (Test-Path "$modelPath\config.json") {
            Write-SafeHost "   ✓ BGE-M3 모델 다운로드 완료" -Color "Green"
        } else {
            Write-SafeHost "   ⚠️ BGE-M3 모델 다운로드 확인 실패" -Color "Yellow"
        }
        
    } catch {
        Write-SafeHost "❌ BGE-M3 모델 다운로드 실패: $_" -Color "Red"
        Write-SafeHost "   폐쇄망에서 수동으로 복사할 수 있습니다." -Color "Yellow"
    }
}

function Create-InstallationScripts {
    Write-SafeHost "📝 설치 스크립트 생성 중..." -Color "Cyan"
    
    # 1. 전체 자동 설치 스크립트
    $masterInstallScript = @'
@echo off
chcp 65001 >nul
cls

echo ============================================================
echo   RAGTrace 완전 오프라인 설치 (폐쇄망 전용)
echo   아무것도 설치되지 않은 Windows에서 바로 실행
echo ============================================================
echo.

setlocal EnableDelayedExpansion

:: 관리자 권한 확인
echo [1/4] 관리자 권한 확인 중...
net session >nul 2>&1
if !errorLevel! neq 0 (
    echo       [오류] 관리자 권한이 필요합니다.
    echo       이 파일을 우클릭 후 "관리자 권한으로 실행"을 선택하세요.
    pause
    exit /b 1
)
echo       ✓ 관리자 권한 확인 완료

:: Python 설치
echo.
echo [2/4] Python 3.11 설치 중...
if exist "C:\Program Files\Python311\python.exe" (
    echo       ✓ Python 3.11이 이미 설치되어 있습니다.
) else (
    echo       Python 3.11 설치 시작...
    call 01-install-python.bat
    if !errorLevel! neq 0 (
        echo       [오류] Python 설치 실패
        pause
        exit /b 1
    )
)

:: 환경변수 새로고침
echo.
echo [3/4] 환경변수 새로고침 중...
call refreshenv 2>nul || (
    echo       PATH 환경변수 수동 설정...
    set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
)

:: RAGTrace 설치
echo.
echo [4/4] RAGTrace 설치 중...
call 02-install-ragtrace.bat
if !errorLevel! neq 0 (
    echo       [오류] RAGTrace 설치 실패
    pause
    exit /b 1
)

:: 설치 검증
echo.
echo ============================================================
echo   설치 검증 중...
echo ============================================================
call 03-verify.bat

echo.
echo ============================================================
echo   설치 완료!
echo ============================================================
echo.
echo   다음 단계:
echo   1. .env.example을 .env로 복사
echo   2. .env 파일에 API 키 입력
echo   3. run-web.bat 실행하여 웹 대시보드 시작
echo.

pause
'@

    # 2. Python 설치 스크립트
    $pythonInstallScript = @'
@echo off
chcp 65001 >nul

echo Python 3.11.9 설치 중...

if not exist "..\00_Prerequisites\python-3.11.9-amd64.exe" (
    echo [오류] Python 설치파일을 찾을 수 없습니다.
    echo        00_Prerequisites\python-3.11.9-amd64.exe가 있는지 확인하세요.
    exit /b 1
)

echo 자동 설치 시작... (잠시만 기다려주세요)
"..\00_Prerequisites\python-3.11.9-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: 설치 완료 대기
timeout /t 30 /nobreak >nul

:: 설치 확인
"C:\Program Files\Python311\python.exe" --version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Python 3.11 설치 완료
) else (
    echo [오류] Python 설치 실패 또는 PATH 설정 문제
    exit /b 1
)

:: VC++ 재배포 패키지 설치
if exist "..\00_Prerequisites\vc_redist.x64.exe" (
    echo Visual C++ 재배포 패키지 설치 중...
    "..\00_Prerequisites\vc_redist.x64.exe" /quiet /norestart
    timeout /t 10 /nobreak >nul
    echo ✓ VC++ 재배포 패키지 설치 완료
) else (
    echo [경고] VC++ 재배포 패키지 파일이 없습니다.
)

exit /b 0
'@

    # 3. RAGTrace 설치 스크립트
    $ragtraceInstallScript = @'
@echo off
chcp 65001 >nul

echo RAGTrace 설치 중...

:: Python 경로 설정
set "PYTHON_PATH=C:\Program Files\Python311\python.exe"
if not exist "%PYTHON_PATH%" (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo        먼저 01-install-python.bat을 실행하세요.
    exit /b 1
)

:: 작업 디렉토리로 이동
cd /d "..\02_Source"

:: 가상환경 생성
echo 가상환경 생성 중...
if exist ".venv" (
    rmdir /s /q ".venv"
    timeout /t 2 /nobreak >nul
)

"%PYTHON_PATH%" -m venv .venv
if %errorLevel% neq 0 (
    echo [오류] 가상환경 생성 실패
    exit /b 1
)

:: 가상환경 활성화
call .venv\Scripts\activate.bat

:: pip 업그레이드 (오프라인)
echo pip 업그레이드 중...
python -m pip install --upgrade pip --no-index --find-links "..\01_Dependencies\wheels" --quiet

:: 패키지 설치 (완전 오프라인)
echo 패키지 설치 중... (10-30분 소요)
pip install --no-index --find-links "..\01_Dependencies\wheels" -r "..\01_Dependencies\requirements.txt" --no-deps --force-reinstall

if %errorLevel% equ 0 (
    echo ✓ RAGTrace 설치 완료
) else (
    echo [오류] 패키지 설치 실패
    echo        ..\01_Dependencies\wheels 폴더에 필요한 패키지가 있는지 확인하세요.
    exit /b 1
)

:: .env 파일 생성 (example에서 복사)
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ✓ .env 파일 생성됨 (API 키를 설정하세요)
    )
)

exit /b 0
'@

    # 4. 검증 스크립트
    $verifyScript = @'
@echo off
chcp 65001 >nul

echo ============================================================
echo   RAGTrace 설치 검증
echo ============================================================

cd /d "..\02_Source"

if not exist ".venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 설치되어 있지 않습니다.
    echo        02-install-ragtrace.bat을 먼저 실행하세요.
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Python 버전 확인:
python --version

echo.
echo 핵심 패키지 확인:
python -c "
packages = ['streamlit', 'pandas', 'numpy', 'torch', 'ragas', 'sentence_transformers']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✓ {pkg}')
    except ImportError:
        print(f'✗ {pkg}')
"

echo.
echo RAGTrace CLI 테스트:
python cli.py --help | findstr "Usage" >nul
if %errorLevel% equ 0 (
    echo ✓ RAGTrace CLI 정상 작동
) else (
    echo ✗ RAGTrace CLI 오류
)

echo.
echo ============================================================
echo   검증 완료
echo ============================================================
'@

    # 5. 웹 실행 스크립트
    $runWebScript = @'
@echo off
chcp 65001 >nul
title RAGTrace Web Dashboard

echo ============================================================
echo   RAGTrace 웹 대시보드 시작
echo ============================================================

cd /d "..\02_Source"

if not exist ".venv\Scripts\activate.bat" (
    echo [오류] RAGTrace가 설치되어 있지 않습니다.
    echo        00-install-all.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo   웹 대시보드 시작 중...
echo   URL: http://localhost:8501
echo   종료: Ctrl+C
echo.

streamlit run src/presentation/web/main.py
pause
'@

    # 6. CLI 실행 스크립트
    $runCliScript = @'
@echo off
chcp 65001 >nul
title RAGTrace CLI

cd /d "..\02_Source"

if not exist ".venv\Scripts\activate.bat" (
    echo [오류] RAGTrace가 설치되어 있지 않습니다.
    echo        00-install-all.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo RAGTrace CLI 모드
echo.
echo 사용법:
echo   python cli.py --help
echo   python cli.py evaluate evaluation_data
echo.

cmd /k
'@

    # 모든 스크립트 파일 생성
    try {
        $masterInstallScript | Out-File -FilePath "$OutputDir\04_Scripts\00-install-all.bat" -Encoding UTF8 -ErrorAction Stop
        $pythonInstallScript | Out-File -FilePath "$OutputDir\04_Scripts\01-install-python.bat" -Encoding UTF8 -ErrorAction Stop
        $ragtraceInstallScript | Out-File -FilePath "$OutputDir\04_Scripts\02-install-ragtrace.bat" -Encoding UTF8 -ErrorAction Stop
        $verifyScript | Out-File -FilePath "$OutputDir\04_Scripts\03-verify.bat" -Encoding UTF8 -ErrorAction Stop
        $runWebScript | Out-File -FilePath "$OutputDir\04_Scripts\run-web.bat" -Encoding UTF8 -ErrorAction Stop
        $runCliScript | Out-File -FilePath "$OutputDir\04_Scripts\run-cli.bat" -Encoding UTF8 -ErrorAction Stop
        
        Write-SafeHost "   ✓ 모든 설치 스크립트 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ 스크립트 생성 실패: $_" -Color "Red"
        exit 1
    }
}

function Create-Documentation {
    Write-SafeHost "📚 설치 가이드 문서 생성 중..." -Color "Cyan"
    
    $installGuide = @"
RAGTrace 완전 오프라인 패키지 설치 가이드
===========================================

🎯 이 패키지는 인터넷이 완전히 차단된 폐쇄망 환경에서
   아무것도 설치되지 않은 깨끗한 Windows PC에서 바로 실행할 수 있도록
   모든 구성요소를 포함합니다.

📋 포함된 구성요소:
   ✅ Python 3.11.9 설치파일 (30MB)
   ✅ Visual C++ 재배포 패키지 (14MB)
   ✅ RAGTrace 전체 소스코드
   ✅ 모든 Python 패키지 wheel 파일 (200+ 개)
   ✅ 자동 설치 스크립트
   ✅ BGE-M3 로컬 모델 (선택사항, 2GB)

🚀 설치 방법 (폐쇄망 PC에서):

   1단계: 압축 해제
   ================
   - RAGTrace-Complete-Offline.zip을 C:\에 압축 해제
   - 폴더 구조: C:\RAGTrace-Complete-Offline\

   2단계: 자동 설치 실행
   ===================
   - 04_Scripts 폴더로 이동
   - 00-install-all.bat을 우클릭
   - "관리자 권한으로 실행" 선택
   - 설치 완료까지 30-60분 대기

   3단계: API 키 설정
   ================
   - 02_Source 폴더로 이동
   - .env 파일을 메모장으로 열기
   - GEMINI_API_KEY=your_key_here 입력
   - 파일 저장

   4단계: 실행
   ==========
   - 04_Scripts\run-web.bat 실행 (웹 대시보드)
   - 또는 04_Scripts\run-cli.bat 실행 (CLI 모드)
   - 웹: http://localhost:8501 접속

🔧 수동 설치 (자동 설치 실패 시):

   1. 04_Scripts\01-install-python.bat 실행
   2. PC 재부팅
   3. 04_Scripts\02-install-ragtrace.bat 실행
   4. 04_Scripts\03-verify.bat으로 설치 확인

📁 패키지 구조:
   00_Prerequisites: Python 및 VC++ 설치파일
   01_Dependencies: Python 패키지 wheel 파일들
   02_Source: RAGTrace 소스코드 및 가상환경
   03_Models: BGE-M3 로컬 모델 (있는 경우)
   04_Scripts: 설치 및 실행 스크립트

⚠️ 시스템 요구사항:
   ✅ Windows 10/11 64비트
   ✅ 관리자 권한
   ✅ 10GB 이상 디스크 공간
   ✅ 8GB 이상 RAM
   ❌ 인터넷 연결 불필요

🆘 문제 해결:
   - 설치 실패: 04_Scripts\03-verify.bat 실행하여 상태 확인
   - 실행 오류: .env 파일의 API 키 확인
   - 웹 접속 불가: Windows 방화벽에서 Python 허용

📞 지원:
   - GitHub: https://github.com/ntts9990/RAGTrace/issues
   - 자세한 문서: 02_Source\docs\ 폴더 참조

생성일: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
패키지 버전: v2.1 (완전 오프라인)
"@

    try {
        $installGuide | Out-File -FilePath "$OutputDir\README-설치가이드.txt" -Encoding UTF8 -ErrorAction Stop
        Write-SafeHost "   ✓ 설치 가이드 문서 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ 문서 생성 실패: $_" -Color "Red"
        exit 1
    }
}

function Create-FinalPackage {
    Write-SafeHost "📦 최종 패키지 생성 중..." -Color "Cyan"
    
    # 패키지 정보 수집
    $wheelCount = (Get-ChildItem "$OutputDir\01_Dependencies\wheels" -File -ErrorAction SilentlyContinue).Count
    $packageSize = if (Test-Path $OutputDir) {
        (Get-ChildItem $OutputDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    } else { 0 }
    
    # BGE-M3 모델 크기 확인
    $bgeSize = 0
    if (Test-Path "$OutputDir\03_Models\bge-m3") {
        $bgeSize = (Get-ChildItem "$OutputDir\03_Models\bge-m3" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    }
    
    Write-SafeHost ""
    Write-SafeHost "📊 패키지 생성 결과:" -Color "Green"
    Write-SafeHost "   디렉토리: $OutputDir" -Color "White"
    Write-SafeHost "   Python 패키지: $wheelCount 개" -Color "White"
    Write-SafeHost "   BGE-M3 모델: $($bgeSize -gt 0 ? '포함됨' : '미포함')" -Color "White"
    Write-SafeHost "   총 크기: $([math]::Round($packageSize, 1)) MB" -Color "White"
    
    # 압축 생성
    Write-SafeHost ""
    Write-SafeHost "📦 패키지 압축 중..." -Color "Cyan"
    $zipPath = "RAGTrace-Complete-Offline.zip"
    
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    try {
        Compress-Archive -Path $OutputDir -DestinationPath $zipPath -CompressionLevel Optimal -ErrorAction Stop
        $zipSize = (Get-Item $zipPath).Length / 1MB
        Write-SafeHost "   ✓ 압축 완료: $zipPath ($([math]::Round($zipSize, 1)) MB)" -Color "Green"
    } catch {
        Write-SafeHost "❌ 압축 실패: $_" -Color "Red"
        exit 1
    }
    
    return $zipPath, $zipSize
}

# 메인 실행 함수
function Main {
    $startTime = Get-Date
    
    try {
        Test-Prerequisites
        Initialize-CompletePackageStructure
        Download-PythonInstaller
        Download-VCRedist
        Copy-SourceFiles
        Create-CompleteRequirements
        Download-AllPythonPackages
        Download-BGEModel
        Create-InstallationScripts
        Create-Documentation
        
        $zipPath, $zipSize = Create-FinalPackage
        
        # 완료 메시지
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        Write-SafeHost ""
        Write-SafeHost "============================================================" -Color "Green"
        Write-SafeHost "  완전 오프라인 패키지 생성 완료!" -Color "Green"
        Write-SafeHost "============================================================" -Color "Green"
        Write-SafeHost ""
        Write-SafeHost "📄 출력 파일: $zipPath" -Color "Yellow"
        Write-SafeHost "📏 압축 크기: $([math]::Round($zipSize, 1)) MB" -Color "Yellow"
        Write-SafeHost "⏱️ 소요 시간: $($duration.ToString('hh\:mm\:ss'))" -Color "Yellow"
        Write-SafeHost ""
        Write-SafeHost "📋 다음 단계:" -Color "Cyan"
        Write-SafeHost "1. $zipPath 파일을 폐쇄망 PC로 복사" -Color "White"
        Write-SafeHost "2. C:\ 드라이브에 압축 해제" -Color "White"
        Write-SafeHost "3. 04_Scripts\00-install-all.bat을 관리자 권한으로 실행" -Color "White"
        Write-SafeHost "4. API 키 설정 후 run-web.bat으로 실행" -Color "White"
        Write-SafeHost ""
        Write-SafeHost "🎯 폐쇄망에서 바로 실행 가능한 완전 패키지입니다!" -Color "Green"
        
    } catch {
        Write-SafeHost ""
        Write-SafeHost "❌ 패키지 생성 실패: $_" -Color "Red"
        Write-SafeHost "   자세한 오류 정보는 PowerShell 출력을 확인하세요." -Color "Yellow"
        exit 1
    }
}

# 스크립트 실행
if ($MyInvocation.InvocationName -ne '.') {
    Main
}