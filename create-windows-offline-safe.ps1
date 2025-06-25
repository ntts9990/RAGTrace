# RAGTrace Windows 완전 오프라인 패키지 생성 스크립트 (안전 버전)
# PowerShell 관리자 권한으로 실행 필요

param(
    [string]$OutputDir = "RAGTrace-Windows-Offline",
    [switch]$SkipDownload = $false,
    [switch]$Verbose = $false
)

# 오류 발생 시 스크립트 중단
$ErrorActionPreference = "Stop"

function Write-SafeHost {
    param([string]$Message, [string]$Color = "White")
    try {
        Write-Host $Message -ForegroundColor $Color
    } catch {
        Write-Output $Message
    }
}

function Test-Prerequisites {
    Write-SafeHost "============================================================" -Color "Green"
    Write-SafeHost "  RAGTrace Windows 완전 오프라인 패키지 생성 (안전 버전)" -Color "Green"
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
    
    # pip 확인
    try {
        $pipVersion = pip --version 2>$null
        Write-SafeHost "✅ pip 확인 완료: $pipVersion" -Color "Green"
    } catch {
        Write-SafeHost "❌ pip이 설치되어 있지 않습니다." -Color "Red"
        Write-SafeHost "   python -m ensurepip --upgrade 를 실행하세요." -Color "Yellow"
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

function Initialize-PackageStructure {
    Write-SafeHost "📁 패키지 구조 초기화 중..." -Color "Cyan"
    
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
    
    # 디렉토리 구조 생성
    $dirs = @(
        "$OutputDir\01_Prerequisites",
        "$OutputDir\02_Dependencies\wheels",
        "$OutputDir\03_Source", 
        "$OutputDir\04_Scripts",
        "$OutputDir\05_Documentation"
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

function Copy-SourceFiles {
    Write-SafeHost "📋 소스 코드 복사 중..." -Color "Cyan"
    
    $sourceItems = @("src", "data", "docs", "cli.py", "run_dashboard.py", "pyproject.toml", "uv.lock", ".env.example", "README.md")
    $copiedCount = 0
    
    foreach ($item in $sourceItems) {
        if (Test-Path $item) {
            try {
                Copy-Item -Path $item -Destination "$OutputDir\03_Source\" -Recurse -Force -ErrorAction Stop
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

function Create-Requirements {
    Write-SafeHost "📝 Requirements 파일 생성 중..." -Color "Cyan"
    
    # 안전한 버전으로 고정된 requirements
    $safeRequirements = @"
# 핵심 평가 프레임워크 (안전 버전)
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
datasets==3.6.0

# 웹 UI
streamlit==1.39.0
plotly==5.24.1

# ML/AI (CPU 전용 - 안전 버전)
sentence-transformers==3.3.1
torch==2.5.1+cpu
transformers==4.46.3

# 유틸리티
requests==2.32.4
psutil==6.1.0
"@

    try {
        $safeRequirements | Out-File -FilePath "$OutputDir\02_Dependencies\requirements.txt" -Encoding UTF8 -ErrorAction Stop
        Write-SafeHost "   ✓ requirements.txt 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ Requirements 파일 생성 실패: $_" -Color "Red"
        exit 1
    }
}

function Download-Packages {
    if ($SkipDownload) {
        Write-SafeHost "📦 패키지 다운로드 생략됨 (-SkipDownload 옵션)" -Color "Yellow"
        return
    }
    
    Write-SafeHost "📦 Python 패키지 다운로드 시작..." -Color "Cyan"
    Write-SafeHost "   - 플랫폼: Windows 64비트" -Color "White"
    Write-SafeHost "   - Python: 3.11" -Color "White"
    Write-SafeHost "   - PyTorch: CPU 전용" -Color "White"
    Write-SafeHost "   - 예상 시간: 15-45분" -Color "White"
    Write-SafeHost ""
    
    $originalLocation = Get-Location
    
    try {
        Set-Location "$OutputDir\02_Dependencies"
        
        # pip 업그레이드
        Write-SafeHost "🔧 pip 업그레이드 중..." -Color "Yellow"
        python -m pip install --upgrade pip --quiet
        
        # 단계별 안전한 다운로드
        Write-SafeHost "📥 1단계: 핵심 패키지 다운로드..." -Color "Yellow"
        
        $downloadCmd = @"
pip download --platform win_amd64 --python-version 3.11 --only-binary :all: --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt -d wheels --timeout 900 --retries 5 --no-deps
"@
        
        if ($Verbose) {
            Write-SafeHost "   실행 명령: $downloadCmd" -Color "Gray"
        }
        
        Invoke-Expression $downloadCmd
        
        if ($LASTEXITCODE -ne 0) {
            Write-SafeHost "⚠️ 일부 패키지 다운로드 실패. 개별 다운로드를 시도합니다..." -Color "Yellow"
            
            # 개별 패키지 다운로드 (실패 허용)
            $corePackages = @(
                "dependency-injector==4.48.1",
                "streamlit==1.39.0", 
                "pandas==2.2.2",
                "numpy==1.26.4",
                "requests==2.32.4"
            )
            
            foreach ($pkg in $corePackages) {
                try {
                    Write-SafeHost "   → $pkg" -Color "Gray"
                    pip download --platform win_amd64 --python-version 3.11 --only-binary :all: $pkg -d wheels --timeout 300 --quiet --no-deps
                } catch {
                    Write-SafeHost "   ⚠️ $pkg 다운로드 실패" -Color "Yellow"
                }
            }
        }
        
        # 다운로드된 패키지 수 확인
        $wheelCount = (Get-ChildItem "wheels" -Filter "*.whl" -ErrorAction SilentlyContinue).Count
        Write-SafeHost "   ✅ 다운로드 완료: $wheelCount 개 wheel 파일" -Color "Green"
        
        if ($wheelCount -lt 10) {
            Write-SafeHost "⚠️ 다운로드된 패키지가 적습니다. 네트워크 상태를 확인하세요." -Color "Yellow"
        }
        
    } catch {
        Write-SafeHost "❌ 패키지 다운로드 중 오류: $_" -Color "Red"
        Write-SafeHost "   계속 진행하지만 일부 패키지가 누락될 수 있습니다." -Color "Yellow"
    } finally {
        Set-Location $originalLocation
    }
}

function Create-InstallationScripts {
    Write-SafeHost "📝 설치 스크립트 생성 중..." -Color "Cyan"
    
    # 안전한 설치 스크립트
    $safeInstallScript = @'
@echo off
chcp 65001 >nul
cls

echo ============================================================
echo   RAGTrace 완전 오프라인 설치 (안전 버전)
echo ============================================================
echo.

:: 오류 발생 시 중단
setlocal EnableDelayedExpansion

:: 관리자 권한 확인
echo [1/6] 관리자 권한 확인 중...
net session >nul 2>&1
if !errorLevel! neq 0 (
    echo       [오류] 관리자 권한이 필요합니다.
    echo       마우스 우클릭 후 "관리자 권한으로 실행"을 선택하세요.
    pause
    exit /b 1
)
echo       ✓ 관리자 권한 확인 완료

:: Python 확인
echo.
echo [2/6] Python 3.11 확인 중...
python --version >nul 2>&1
if !errorLevel! neq 0 (
    echo       [오류] Python이 설치되어 있지 않습니다.
    echo       01_Prerequisites\python-3.11.9-amd64.exe를 먼저 설치하세요.
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

:: VC++ 재배포 가능 패키지 안내
echo.
echo [3/6] Visual C++ 재배포 가능 패키지 확인
echo       01_Prerequisites\vc_redist.x64.exe를 실행했는지 확인하세요.
echo       (설치하지 않았다면 Ctrl+C로 중단 후 먼저 설치)
pause

:: 작업 디렉토리 설정
echo.
echo [4/6] 작업 디렉토리 설정 중...
if not exist "03_Source" (
    echo       [오류] 03_Source 디렉토리를 찾을 수 없습니다.
    pause
    exit /b 1
)
cd /d "03_Source"
echo       ✓ 작업 디렉토리: %CD%

:: 가상환경 생성
echo.
echo [5/6] Python 가상환경 생성 중...
if exist ".venv" (
    echo       기존 가상환경 제거 중...
    rmdir /s /q ".venv" 2>nul
    timeout /t 2 /nobreak >nul
)

python -m venv .venv
if !errorLevel! neq 0 (
    echo       [오류] 가상환경 생성 실패
    pause
    exit /b 1
)
echo       ✓ 가상환경 생성 완료

:: 가상환경 활성화
call .venv\Scripts\activate
if !errorLevel! neq 0 (
    echo       [오류] 가상환경 활성화 실패
    pause
    exit /b 1
)
echo       ✓ 가상환경 활성화 완료

:: 패키지 설치
echo.
echo [6/6] 패키지 설치 중... (완전 오프라인)
echo       설치 중... 10-30분 소요 예상

:: pip 업그레이드 (오프라인)
echo       → pip 업그레이드 중...
python -m pip install --upgrade pip --no-index --find-links "..\02_Dependencies\wheels" --quiet

:: 메인 패키지 설치 (의존성 포함)
echo       → 패키지 설치 중...
pip install --no-index --find-links "..\02_Dependencies\wheels" -r "..\02_Dependencies\requirements.txt" --no-deps --force-reinstall

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
    echo   검증: ..\04_Scripts\verify.bat
    echo.
) else (
    echo.
    echo [오류] 패키지 설치 실패
    echo       ..\02_Dependencies\wheels 폴더에 필요한 패키지가 있는지 확인하세요.
)

pause
'@

    try {
        $safeInstallScript | Out-File -FilePath "$OutputDir\04_Scripts\install.bat" -Encoding UTF8 -ErrorAction Stop
        Write-SafeHost "   ✓ install.bat 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ 설치 스크립트 생성 실패: $_" -Color "Red"
        exit 1
    }
    
    # 실행 스크립트들
    Create-RunScripts
}

function Create-RunScripts {
    # 웹 UI 실행 스크립트
    $runWebScript = @'
@echo off
chcp 65001 >nul
title RAGTrace Web Dashboard

echo ============================================================
echo   RAGTrace 웹 대시보드
echo ============================================================
echo.

if not exist "03_Source\.venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 설치되어 있지 않습니다.
    echo        install.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

cd /d "03_Source"
call .venv\Scripts\activate

echo   시작 중... 잠시만 기다려주세요.
echo   URL: http://localhost:8501
echo   종료: Ctrl+C
echo.
echo ============================================================

streamlit run src/presentation/web/main.py
if %errorLevel% neq 0 (
    echo.
    echo [오류] 웹 대시보드 실행 실패
    echo        verify.bat으로 설치 상태를 확인하세요.
)
pause
'@
    
    # CLI 실행 스크립트
    $runCliScript = @'
@echo off
chcp 65001 >nul
title RAGTrace CLI

if not exist "03_Source\.venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 설치되어 있지 않습니다.
    echo        install.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

cd /d "03_Source"
call .venv\Scripts\activate

echo RAGTrace CLI 모드
echo.
echo 사용법:
echo   python cli.py --help
echo   python cli.py evaluate evaluation_data
echo.

cmd /k
'@
    
    # 검증 스크립트
    $verifyScript = @'
@echo off
chcp 65001 >nul

if not exist "03_Source\.venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 설치되어 있지 않습니다.
    echo        install.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

cd /d "03_Source"
call .venv\Scripts\activate
python ..\04_Scripts\verify.py
pause
'@
    
    try {
        $runWebScript | Out-File -FilePath "$OutputDir\04_Scripts\run-web.bat" -Encoding UTF8 -ErrorAction Stop
        $runCliScript | Out-File -FilePath "$OutputDir\04_Scripts\run-cli.bat" -Encoding UTF8 -ErrorAction Stop  
        $verifyScript | Out-File -FilePath "$OutputDir\04_Scripts\verify.bat" -Encoding UTF8 -ErrorAction Stop
        
        Write-SafeHost "   ✓ 실행 스크립트 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ 실행 스크립트 생성 실패: $_" -Color "Red"
        exit 1
    }
}

function Create-VerificationScript {
    Write-SafeHost "🔍 검증 스크립트 생성 중..." -Color "Cyan"
    
    $verifyPython = @'
#!/usr/bin/env python3
"""RAGTrace 완전 오프라인 설치 검증 (안전 버전)"""

import sys
import os
import importlib
from pathlib import Path
import subprocess

def check_python_version():
    """Python 버전 확인"""
    print(f"🐍 Python: {sys.version}")
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 이상 필요")
        return False
    else:
        print("✅ Python 버전 OK")
        return True

def check_virtual_environment():
    """가상환경 활성화 상태 확인"""
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"🔧 가상환경: {'✅ 활성화됨' if venv_active else '❌ 미활성화'}")
    
    if not venv_active:
        print("   .venv\\Scripts\\activate.bat 를 먼저 실행하세요.")
    
    return venv_active

def check_core_packages():
    """핵심 패키지 설치 확인"""
    core_packages = [
        ('streamlit', 'streamlit'),
        ('pandas', 'pandas'), 
        ('numpy', 'numpy'),
        ('torch', 'torch'),
        ('sentence_transformers', 'sentence_transformers'),
        ('ragas', 'ragas'),
        ('dependency_injector', 'dependency_injector'),
        ('plotly', 'plotly'),
        ('openpyxl', 'openpyxl'),
        ('requests', 'requests'),
        ('google.generativeai', 'google.generativeai')
    ]
    
    print("\n📦 핵심 패키지 확인:")
    all_ok = True
    installed_count = 0
    
    for display_name, import_name in core_packages:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"   ✅ {display_name}: {version}")
            installed_count += 1
        except ImportError as e:
            print(f"   ❌ {display_name}: 미설치 ({str(e)[:50]}...)")
            all_ok = False
        except Exception as e:
            print(f"   ⚠️ {display_name}: 확인 실패 ({str(e)[:30]}...)")
    
    print(f"\n📊 설치 현황: {installed_count}/{len(core_packages)} 패키지")
    return all_ok and installed_count >= 8  # 최소 8개 패키지 필요

def check_pytorch_cpu():
    """PyTorch CPU 버전 확인"""
    try:
        import torch
        is_cpu = not torch.cuda.is_available()
        print(f"\n🔥 PyTorch: {'✅ CPU 전용' if is_cpu else '⚠️ GPU 감지됨'}")
        if is_cpu:
            print(f"   버전: {torch.__version__}")
        return True
    except ImportError:
        print("\n🔥 PyTorch: ❌ 미설치")
        return False
    except Exception as e:
        print(f"\n🔥 PyTorch: ⚠️ 확인 실패 ({e})")
        return False

def check_environment_files():
    """환경 설정 파일 확인"""
    env_exists = Path(".env").exists()
    env_example_exists = Path(".env.example").exists()
    
    print(f"\n⚙️ 환경 설정:")
    if env_exists:
        print("   ✅ .env 파일 존재")
        return True
    elif env_example_exists:
        print("   ⚠️ .env.example만 존재 (.env로 복사 필요)")
        return False
    else:
        print("   ❌ 환경 설정 파일 없음")
        return False

def check_data_files():
    """데이터 파일 확인"""
    data_dir = Path("data")
    if data_dir.exists():
        data_files = list(data_dir.glob("*.json"))
        print(f"\n📁 데이터 파일: {len(data_files)}개 발견")
        return True
    else:
        print("\n📁 데이터 파일: data 디렉토리 없음")
        return False

def main():
    print("=" * 60)
    print("  RAGTrace 오프라인 설치 검증 (안전 버전)")
    print("=" * 60)
    print()
    
    # 경로 확인
    if not Path("cli.py").exists():
        print("❌ 03_Source 디렉토리에서 실행하세요.")
        return False
    
    # 각 항목 검사
    checks = [
        ("Python 버전", check_python_version),
        ("가상환경", check_virtual_environment), 
        ("핵심 패키지", check_core_packages),
        ("PyTorch", check_pytorch_cpu),
        ("환경 설정", check_environment_files),
        ("데이터 파일", check_data_files)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"   ❌ {name} 확인 중 오류: {e}")
            results.append(False)
    
    # 전체 결과
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    if passed >= 4:  # 최소 4개 항목 통과 필요
        print("✅ 설치 검증 통과! RAGTrace 사용 가능")
        print("=" * 60)
        print(f"\n통과 항목: {passed}/{total}")
        print("\n실행 방법:")
        print("  웹 UI: ..\\04_Scripts\\run-web.bat")
        print("  CLI: ..\\04_Scripts\\run-cli.bat")
        
        if not results[4]:  # 환경 설정 실패
            print("\n⚠️ 다음 단계:")
            print("  1. .env.example을 .env로 복사")
            print("  2. 메모장으로 .env 편집")
            print("  3. API 키 입력")
    else:
        print("❌ 설치가 완료되지 않았습니다.")
        print("=" * 60)
        print(f"\n통과 항목: {passed}/{total}")
        print("\n문제 해결:")
        if not results[1]:
            print("  - 가상환경 활성화: .venv\\Scripts\\activate.bat")
        if not results[2]:
            print("  - 패키지 재설치: ..\\04_Scripts\\install.bat")
    
    return passed >= 4

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n예기치 않은 오류: {e}")
    finally:
        input("\nEnter 키를 눌러 종료...")
'@

    try {
        $verifyPython | Out-File -FilePath "$OutputDir\04_Scripts\verify.py" -Encoding UTF8 -ErrorAction Stop
        Write-SafeHost "   ✓ verify.py 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ 검증 스크립트 생성 실패: $_" -Color "Red"
        exit 1
    }
}

function Create-Documentation {
    Write-SafeHost "📚 문서 생성 중..." -Color "Cyan"
    
    $safeReadme = @"
RAGTrace 완전 오프라인 패키지 (Windows 전용 - 안전 버전)
========================================================

이 패키지는 인터넷이 완전히 차단된 폐쇄망 환경에서
RAGTrace를 안전하게 설치하고 실행하기 위한 모든 파일을 포함합니다.

[사전 준비 - 인터넷 연결된 PC에서]
==================================
1. Python 3.11.9 Windows 64비트 다운로드
   https://www.python.org/downloads/release/python-3119/
   → python-3.11.9-amd64.exe
   ⚠️ 설치 시 "Add Python to PATH" 체크 필수

2. Visual C++ 재배포 가능 패키지 다운로드
   https://aka.ms/vs/17/release/vc_redist.x64.exe
   → vc_redist.x64.exe

3. 두 파일을 01_Prerequisites 폴더에 복사

[폐쇄망 설치 순서]
==================
1. 전체 패키지를 폐쇄망 PC로 복사
2. 01_Prerequisites/python-3.11.9-amd64.exe 설치
   - "Add Python to PATH" 반드시 체크
   - 설치 완료 후 재부팅 권장
3. 01_Prerequisites/vc_redist.x64.exe 설치
4. PowerShell을 관리자 권한으로 실행
5. 04_Scripts/install.bat을 관리자 권한으로 실행
6. .env.example을 .env로 복사하고 API 키 설정
7. 04_Scripts/verify.bat으로 설치 검증

[실행 방법]
===========
- 웹 UI: 04_Scripts/run-web.bat (추천)
- CLI: 04_Scripts/run-cli.bat

[API 키 설정]
=============
1. 03_Source/.env.example을 .env로 복사
2. 메모장으로 .env 파일 편집
3. API 키 입력:
   GEMINI_API_KEY=your_gemini_key_here
   CLOVA_STUDIO_API_KEY=your_hcx_key_here

[패키지 구성]
=============
- 01_Prerequisites: Python 및 VC++ 설치 파일 (사용자가 추가)
- 02_Dependencies: Python 패키지 wheel 파일 (완전 오프라인)
- 03_Source: RAGTrace 소스 코드
- 04_Scripts: 설치/실행/검증 스크립트 (안전 버전)
- 05_Documentation: 추가 문서

[시스템 요구사항]
=================
✅ Windows 10 64비트 이상
✅ Python 3.11.9 (필수)
✅ 관리자 권한
✅ 10GB 이상 디스크 공간
✅ 8GB 이상 RAM
❌ GPU 불필요 (CPU 전용)
❌ 인터넷 연결 불필요 (설치 후)

[주요 개선사항 - 안전 버전]
==========================
✅ 사전 조건 검사 강화
✅ 오류 처리 및 복구 로직
✅ 단계별 검증 및 피드백
✅ 안전한 패키지 버전 고정
✅ 상세한 오류 메시지
✅ 설치 상태 검증 도구

[문제 해결]
===========
설치 실패 시:
- install.bat을 관리자 권한으로 재실행
- Python PATH 설정 확인
- 02_Dependencies/wheels 폴더 확인

실행 실패 시:
- verify.bat으로 설치 상태 확인
- .env 파일의 API 키 확인
- 가상환경 활성화 상태 확인

웹 UI 접속 불가 시:
- 방화벽 설정 확인
- 브라우저에서 http://localhost:8501 접속
- 다른 Streamlit 프로세스 종료

[지원]
======
- 설치 검증: 04_Scripts/verify.bat
- 상세 로그: 02_Dependencies/download.log
- 패키지 정보: $(Get-ChildItem "$OutputDir\02_Dependencies\wheels" -File 2>/dev/null | Measure-Object).Count 개 wheel 파일

생성일: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
패키지 버전: 2.0 (안전 버전)
"@

    try {
        $safeReadme | Out-File -FilePath "$OutputDir\README-안전설치가이드.txt" -Encoding UTF8 -ErrorAction Stop
        Write-SafeHost "   ✓ README-안전설치가이드.txt 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ 문서 생성 실패: $_" -Color "Red"
        exit 1
    }
    
    # Prerequisites 안내
    $prereqGuide = @"
필수 설치 파일 다운로드 안내 (안전 버전)
====================================

폐쇄망 설치를 위해 다음 파일들을 이 폴더에 복사하세요:

1. python-3.11.9-amd64.exe
   다운로드: https://www.python.org/downloads/release/python-3119/
   크기: 약 30MB
   
   ⚠️ 중요: 설치 시 "Add Python to PATH" 옵션 체크 필수
   설치 후 명령 프롬프트에서 'python --version' 명령으로 확인

2. vc_redist.x64.exe
   다운로드: https://aka.ms/vs/17/release/vc_redist.x64.exe
   크기: 약 14MB
   목적: C++ 확장 모듈 실행에 필요

파일 복사 후 폴더 구조:
01_Prerequisites/
├── python-3.11.9-amd64.exe ← 이 파일을 추가하세요
├── vc_redist.x64.exe ← 이 파일을 추가하세요
└── README.txt (이 파일)

⚠️ 주의사항:
- 두 파일 모두 인터넷이 연결된 PC에서 다운로드 후 복사해야 합니다
- 파일명이 정확히 일치해야 합니다
- 다른 Python 버전은 호환되지 않습니다
"@

    try {
        $prereqGuide | Out-File -FilePath "$OutputDir\01_Prerequisites\README.txt" -Encoding UTF8 -ErrorAction Stop
        Write-SafeHost "   ✓ Prerequisites README.txt 생성 완료" -Color "Green"
    } catch {
        Write-SafeHost "❌ Prerequisites 문서 생성 실패: $_" -Color "Red"
        exit 1
    }
}

function Create-FinalPackage {
    Write-SafeHost "📦 최종 패키지 생성 중..." -Color "Cyan"
    
    # 패키지 정보
    $wheelCount = (Get-ChildItem "$OutputDir\02_Dependencies\wheels" -File -ErrorAction SilentlyContinue).Count
    $packageSize = if (Test-Path $OutputDir) {
        (Get-ChildItem $OutputDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    } else { 0 }
    
    Write-SafeHost ""
    Write-SafeHost "📊 패키지 생성 결과:" -Color "Green"
    Write-SafeHost "   디렉토리: $OutputDir" -Color "White"
    Write-SafeHost "   wheel 파일: $wheelCount 개" -Color "White"
    Write-SafeHost "   크기: $([math]::Round($packageSize, 1)) MB" -Color "White"
    
    # 압축
    Write-SafeHost ""
    Write-SafeHost "📦 패키지 압축 중..." -Color "Cyan"
    $zipPath = "RAGTrace-Windows-Offline-Safe.zip"
    
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
        Initialize-PackageStructure
        Copy-SourceFiles
        Create-Requirements
        Download-Packages
        Create-InstallationScripts
        Create-VerificationScript
        Create-Documentation
        
        $zipPath, $zipSize = Create-FinalPackage
        
        # 완료 메시지
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        Write-SafeHost ""
        Write-SafeHost "============================================================" -Color "Green"
        Write-SafeHost "  안전한 패키지 생성 완료!" -Color "Green"
        Write-SafeHost "============================================================" -Color "Green"
        Write-SafeHost ""
        Write-SafeHost "📄 출력 파일: $zipPath" -Color "Yellow"
        Write-SafeHost "📏 압축 크기: $([math]::Round($zipSize, 1)) MB" -Color "Yellow"
        Write-SafeHost "⏱️ 소요 시간: $($duration.ToString('hh\:mm\:ss'))" -Color "Yellow"
        Write-SafeHost ""
        Write-SafeHost "📋 다음 단계:" -Color "Cyan"
        Write-SafeHost "1. 압축 해제 후 01_Prerequisites에 Python/VC++ 파일 추가" -Color "White"
        Write-SafeHost "2. 전체 패키지를 폐쇄망 PC로 복사" -Color "White"
        Write-SafeHost "3. README-안전설치가이드.txt 참고하여 설치" -Color "White"
        Write-SafeHost ""
        Write-SafeHost "🎯 안전한 폐쇄망 설치 준비 완료!" -Color "Green"
        
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