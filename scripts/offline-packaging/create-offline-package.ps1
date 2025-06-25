# RAGTrace Windows 오프라인 패키지 생성 스크립트
# PowerShell 관리자 권한으로 실행 필요

param(
    [string]$OutputDir = "RAGTrace-Offline-Source"
)

Write-Host "RAGTrace Windows 오프라인 패키지 생성 시작..." -ForegroundColor Green
Write-Host "출력 디렉토리: $OutputDir" -ForegroundColor Yellow

# 기존 디렉토리 삭제
if (Test-Path $OutputDir) {
    Write-Host "기존 디렉토리 제거 중..." -ForegroundColor Yellow
    Remove-Item -Path $OutputDir -Recurse -Force
}

# 1. 디렉토리 구조 생성
Write-Host "디렉토리 구조 생성 중..." -ForegroundColor Yellow
$dirs = @(
    "$OutputDir\01_Prerequisites",
    "$OutputDir\02_Dependencies\wheels",
    "$OutputDir\03_Source",
    "$OutputDir\04_Setup_Scripts", 
    "$OutputDir\05_Documentation"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# 2. Prerequisites 다운로드 (사용자가 수동으로 다운로드 후 복사)
Write-Host "Prerequisites 준비 안내..." -ForegroundColor Yellow
@"
다음 파일들을 01_Prerequisites 폴더에 복사하세요:

1. Python 3.11.9 Windows 64비트:
   https://www.python.org/downloads/release/python-3119/
   파일명: python-3.11.9-amd64.exe

2. Visual C++ 재배포 가능 패키지:
   https://aka.ms/vs/17/release/vc_redist.x64.exe
   파일명: vc_redist.x64.exe

"@ | Out-File -FilePath "$OutputDir\01_Prerequisites\README.txt" -Encoding UTF8

# 3. Python 패키지 다운로드 (Windows 전용, CPU 전용)
Write-Host "Python 패키지 다운로드 중..." -ForegroundColor Yellow
Write-Host "  - Windows 64비트 전용" -ForegroundColor Cyan
Write-Host "  - CPU 전용 PyTorch" -ForegroundColor Cyan
Write-Host "  - 217개 패키지 처리 중..." -ForegroundColor Cyan

try {
    # requirements-frozen.txt에서 macOS 전용 패키지 제거
    $requirements = Get-Content "requirements-frozen.txt" | Where-Object { 
        $_ -notmatch "appnope" 
    }
    
    # CPU 전용 PyTorch로 교체
    $requirements = $requirements | ForEach-Object {
        if ($_ -match "torch==") {
            "torch==2.7.1+cpu"
        } else {
            $_
        }
    }
    
    $requirements | Out-File -FilePath "$OutputDir\02_Dependencies\requirements-frozen-windows.txt" -Encoding UTF8
    
    # Windows용 wheel 다운로드
    Push-Location "$OutputDir\02_Dependencies"
    
    pip download `
        --platform win_amd64 `
        --python-version 311 `
        --only-binary :all: `
        --extra-index-url https://download.pytorch.org/whl/cpu `
        --no-deps `
        -r requirements-frozen-windows.txt `
        -d wheels `
        --timeout 300
        
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 패키지 다운로드 완료" -ForegroundColor Green
    } else {
        Write-Warning "일부 패키지 다운로드 실패. 로그를 확인하세요."
    }
    
    Pop-Location
    
} catch {
    Write-Error "패키지 다운로드 중 오류: $_"
    exit 1
}

# 4. 소스 코드 복사
Write-Host "소스 코드 복사 중..." -ForegroundColor Yellow
$sourceItems = @("src", "data", "docs", "cli.py", "run_dashboard.py", "pyproject.toml", "uv.lock", ".env.example", "README.md")

foreach ($item in $sourceItems) {
    if (Test-Path $item) {
        Copy-Item -Path $item -Destination "$OutputDir\03_Source\" -Recurse -Force
        Write-Host "  ✓ $item" -ForegroundColor Green
    } else {
        Write-Warning "  ⚠ $item 파일이 없습니다"
    }
}

# 5. 설치 스크립트 생성
Write-Host "설치 스크립트 생성 중..." -ForegroundColor Yellow

# setup-environment.bat
@'
@echo off
chcp 65001 >nul
cls

echo ============================================================
echo   RAGTrace 개발 환경 설정
echo ============================================================
echo.

:: Python 설치 확인
echo [1/4] Python 3.11 확인 중...
python --version 2>nul | findstr "3.11" >nul
if %errorLevel% neq 0 (
    echo.
    echo [경고] Python 3.11이 설치되어 있지 않습니다.
    echo        01_Prerequisites\python-3.11.9-amd64.exe 를 먼저 설치하세요.
    echo.
    pause
    exit /b 1
)
echo       Python 3.11 확인 완료

:: Visual C++ 설치 안내  
echo.
echo [2/4] Visual C++ 재배포 가능 패키지
echo       일부 Python 패키지에 필요합니다.
echo       01_Prerequisites\vc_redist.x64.exe 를 실행하여 설치하세요.
echo.
pause

:: 가상환경 생성
echo.
echo [3/4] Python 가상환경 생성 중...
cd /d "%~dp003_Source"
python -m venv .venv
echo       가상환경 생성 완료

:: 의존성 설치 안내
echo.
echo [4/4] 의존성 설치
echo       다음 명령을 실행하세요:
echo.
echo       1. 가상환경 활성화:
echo          .venv\Scripts\activate
echo.
echo       2. 의존성 설치:
echo          pip install --no-index --find-links ..\02_Dependencies\wheels -r ..\02_Dependencies\requirements-frozen-windows.txt
echo.
echo       또는 02_Dependencies\install-dependencies.bat 실행
echo.
pause
'@ | Out-File -FilePath "$OutputDir\04_Setup_Scripts\setup-environment.bat" -Encoding UTF8

# install-dependencies.bat
@'
@echo off
chcp 65001 >nul

echo Python 패키지 설치를 시작합니다...
echo.

:: 03_Source 디렉토리로 이동
cd /d "%~dp0..\03_Source"

:: 가상환경 활성화
if not exist ".venv" (
    echo [오류] 가상환경이 없습니다.
    echo        먼저 setup-environment.bat을 실행하세요.
    pause
    exit /b 1
)

call .venv\Scripts\activate

:: pip 업그레이드
echo pip 업그레이드 중...
python -m pip install --upgrade pip --no-index --find-links "%~dp0wheels"

:: 패키지 설치
echo.
echo 패키지 설치 중... (5-10분 소요)
pip install --no-index --find-links "%~dp0wheels" -r "%~dp0requirements-frozen-windows.txt"

if %errorLevel% eq 0 (
    echo.
    echo ============================================================
    echo   설치 완료!
    echo ============================================================
    echo.
    echo   다음 단계:
    echo   1. .env.example을 .env로 복사
    echo   2. .env 파일에 API 키 입력  
    echo   3. 실행:
    echo      - 웹 UI: python run_dashboard.py
    echo      - CLI: python cli.py --help
) else (
    echo.
    echo [오류] 패키지 설치 실패
)

pause
'@ | Out-File -FilePath "$OutputDir\02_Dependencies\install-dependencies.bat" -Encoding UTF8

# verify-installation.py
$verifyScript = @'
#!/usr/bin/env python3
"""RAGTrace 설치 검증 스크립트"""

import sys
import os
import importlib
from pathlib import Path

def print_header():
    """헤더 출력"""
    print("=" * 60)
    print("  RAGTrace 설치 검증")
    print("=" * 60)
    print()

def check_python_version():
    """Python 버전 확인"""
    print("[1/5] Python 버전 확인")
    version = sys.version_info
    print(f"      현재 버전: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 11:
        print("      ✓ Python 3.11+ OK")
        return True
    else:
        print("      ✗ Python 3.11 이상이 필요합니다")
        return False

def check_venv():
    """가상환경 확인"""
    print("\n[2/5] 가상환경 확인")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("      ✓ 가상환경 활성화됨")
        print(f"      경로: {sys.prefix}")
        return True
    else:
        print("      ✗ 가상환경이 활성화되지 않았습니다")
        print("      .venv\\Scripts\\activate 실행 필요")
        return False

def check_dependencies():
    """주요 의존성 확인"""
    print("\n[3/5] 주요 패키지 확인")
    
    packages = {
        "streamlit": "웹 UI",
        "pandas": "데이터 처리", 
        "numpy": "수치 연산",
        "torch": "PyTorch (CPU)",
        "sentence_transformers": "임베딩 모델",
        "ragas": "RAG 평가",
        "dependency_injector": "의존성 주입",
        "plotly": "시각화",
        "openpyxl": "Excel 지원",
        "xlrd": "Excel 지원"
    }
    
    all_ok = True
    for package, desc in packages.items():
        try:
            module = importlib.import_module(package.split('.')[0])
            version = getattr(module, '__version__', 'unknown')
            print(f"      ✓ {package:<25} {version:<15} ({desc})")
            
            # PyTorch CPU 확인
            if package == "torch":
                import torch
                if torch.cuda.is_available():
                    print("        ⚠ GPU 버전이 설치됨 (CPU 전용 권장)")
                else:
                    print("        ✓ CPU 전용 버전")
        except ImportError:
            print(f"      ✗ {package:<25} {'미설치':<15} ({desc})")
            all_ok = False
    
    return all_ok

def check_source_files():
    """소스 파일 확인"""
    print("\n[4/5] 소스 파일 확인")
    
    required_files = [
        "cli.py",
        "run_dashboard.py", 
        "pyproject.toml",
        "src/container.py",
        "src/presentation/web/main.py",
        "data/evaluation_data.json"
    ]
    
    all_ok = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"      ✓ {file}")
        else:
            print(f"      ✗ {file} (없음)")
            all_ok = False
    
    return all_ok

def check_env_file():
    """환경 설정 파일 확인"""
    print("\n[5/5] 환경 설정 확인")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        if env_example_path.exists():
            print("      ⚠ .env 파일이 없습니다")
            print("      .env.example을 .env로 복사하고 API 키를 설정하세요")
            return False
        else:
            print("      ✗ .env 및 .env.example 파일이 없습니다")
            return False
    
    # .env 파일 내용 확인
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_keys = {
            "GEMINI_API_KEY": "Google Gemini API",
            "CLOVA_STUDIO_API_KEY": "Naver HCX-005 API"
        }
        
        all_ok = True
        for key, desc in api_keys.items():
            value = os.getenv(key)
            if value and value != "your_key_here":
                print(f"      ✓ {key} 설정됨 ({desc})")
            else:
                print(f"      ⚠ {key} 미설정 ({desc})")
                all_ok = False
    except ImportError:
        print("      ⚠ python-dotenv 패키지가 필요합니다")
        
    return True  # API 키는 경고만

def print_summary(results):
    """검증 결과 요약"""
    print("\n" + "=" * 60)
    print("  검증 결과")
    print("=" * 60)
    
    if all(results):
        print("\n  ✓ 모든 검증을 통과했습니다!")
        print("\n  실행 방법:")
        print("  - 웹 UI: python run_dashboard.py")
        print("  - CLI: python cli.py --help")
    else:
        print("\n  ✗ 일부 검증에 실패했습니다.")
        print("  위의 오류를 확인하고 해결하세요.")
    
    print("\n" + "=" * 60)

def main():
    """메인 실행 함수"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print_header()
    
    # 작업 디렉토리 확인
    if not Path("cli.py").exists():
        print("[오류] 03_Source 디렉토리에서 실행하세요.")
        print(f"현재 위치: {os.getcwd()}")
        return
    
    results = [
        check_python_version(),
        check_venv(),
        check_dependencies(),
        check_source_files(),
        check_env_file()
    ]
    
    print_summary(results)

if __name__ == "__main__":
    main()
    input("\nEnter 키를 눌러 종료...")
'@
$verifyScript | Out-File -FilePath "$OutputDir\04_Setup_Scripts\verify-installation.py" -Encoding UTF8

# 6. 문서 준비
Write-Host "문서 템플릿 생성 중..." -ForegroundColor Yellow

@"
RAGTrace Windows 오프라인 설치 패키지
====================================

이 패키지는 인터넷 연결이 없는 Windows 10 환경에서
RAGTrace를 설치하고 실행하기 위한 모든 파일을 포함합니다.

[패키지 구성]
- 01_Prerequisites: Python 및 Visual C++ 설치 파일
- 02_Dependencies: Python 패키지 wheel 파일 (217개)
- 03_Source: RAGTrace 소스 코드
- 04_Setup_Scripts: 설치 도우미 스크립트  
- 05_Documentation: 상세 문서

[설치 순서]
1. Python 3.11.9 설치 (01_Prerequisites/python-3.11.9-amd64.exe)
2. Visual C++ 재배포 가능 패키지 설치 (01_Prerequisites/vc_redist.x64.exe)
3. 03_Source를 원하는 위치에 복사 (예: C:\RAGTrace)
4. 04_Setup_Scripts/setup-environment.bat 실행
5. 02_Dependencies/install-dependencies.bat 실행
6. .env.example을 .env로 복사하고 API 키 설정
7. 04_Setup_Scripts/verify-installation.py로 설치 확인

[실행 방법]
1. 가상환경 활성화: .venv\Scripts\activate
2. 웹 UI: python run_dashboard.py
3. CLI: python cli.py --help

[중요 사항]
- Windows 10 64비트 전용
- Python 3.11.9 필수
- GPU 미지원 (CPU 전용)
- HCX-005와 BGE-M3는 API로만 사용
- 폐쇄망 환경에서 완전 오프라인 실행 가능

생성일: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
패키지 버전: 1.0
"@ | Out-File -FilePath "$OutputDir\README-설치전필독.txt" -Encoding UTF8

# 7. 체크섬 생성
Write-Host "체크섬 파일 생성 중..." -ForegroundColor Yellow

function Generate-Checksums {
    param($Path, $OutputFile)
    
    if (Test-Path $Path) {
        Get-ChildItem -Path $Path -File -Recurse | ForEach-Object {
            $hash = Get-FileHash $_.FullName -Algorithm SHA256
            $relativePath = $_.FullName.Replace((Resolve-Path $Path).Path, "").TrimStart('\')
            "$($hash.Hash)  $relativePath" | Out-File -Append $OutputFile -Encoding UTF8
        }
    }
}

Generate-Checksums -Path "$OutputDir\02_Dependencies\wheels" -OutputFile "$OutputDir\02_Dependencies\checksums.txt"
Generate-Checksums -Path "$OutputDir\03_Source" -OutputFile "$OutputDir\03_Source\checksums.txt"

# 8. 최종 압축
Write-Host "패키지 압축 중..." -ForegroundColor Yellow
$zipPath = "RAGTrace-Windows-Offline-v1.0.zip"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path $OutputDir -DestinationPath $zipPath -CompressionLevel Optimal

# 9. 완료 메시지
Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "  패키지 생성 완료!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "출력 파일: $zipPath" -ForegroundColor Yellow
Write-Host "크기: $((Get-Item $zipPath).Length / 1MB) MB" -ForegroundColor Yellow
Write-Host "`n다음 단계:" -ForegroundColor Cyan
Write-Host "1. 01_Prerequisites 폴더에 Python과 VC++ 설치 파일 추가" -ForegroundColor White
Write-Host "2. 패키지를 대상 시스템으로 전송" -ForegroundColor White  
Write-Host "3. README-설치전필독.txt 참고하여 설치" -ForegroundColor White
Write-Host "`n패키지 내용:" -ForegroundColor Cyan
Write-Host "- Python 패키지: 217개" -ForegroundColor White
Write-Host "- 지원 플랫폼: Windows 10 64비트" -ForegroundColor White
Write-Host "- PyTorch: CPU 전용 버전" -ForegroundColor White
Write-Host "- 완전 오프라인 설치 지원" -ForegroundColor White

Write-Host "`n패키지 생성이 완료되었습니다!" -ForegroundColor Green