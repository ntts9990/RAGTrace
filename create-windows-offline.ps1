# RAGTrace Windows 완전 오프라인 패키지 생성 스크립트
# PowerShell 관리자 권한으로 실행 필요

param(
    [string]$OutputDir = "RAGTrace-Windows-Offline",
    [switch]$SkipDownload = $false
)

Write-Host "============================================================" -ForegroundColor Green
Write-Host "  RAGTrace Windows 완전 오프라인 패키지 생성" -ForegroundColor Green  
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# 시작 시간 기록
$startTime = Get-Date
Write-Host "시작 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow

# 기존 디렉토리 삭제 및 생성
if (Test-Path $OutputDir) {
    Write-Host "기존 디렉토리 제거 중..." -ForegroundColor Yellow
    Remove-Item -Path $OutputDir -Recurse -Force
}

Write-Host "패키지 디렉토리 생성 중..." -ForegroundColor Yellow
$dirs = @(
    "$OutputDir\01_Prerequisites",
    "$OutputDir\02_Dependencies\wheels",  
    "$OutputDir\03_Source",
    "$OutputDir\04_Scripts",
    "$OutputDir\05_Documentation"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# 1. 소스 코드 복사
Write-Host "소스 코드 복사 중..." -ForegroundColor Cyan
$sourceItems = @("src", "data", "docs", "cli.py", "run_dashboard.py", "pyproject.toml", "uv.lock", ".env.example", "README.md")

foreach ($item in $sourceItems) {
    if (Test-Path $item) {
        Copy-Item -Path $item -Destination "$OutputDir\03_Source\" -Recurse -Force
        Write-Host "  ✓ $item" -ForegroundColor Green
    } else {
        Write-Warning "  ⚠ $item 파일이 없습니다"
    }
}

# 2. requirements 파일 생성 (Windows 최적화)
Write-Host "Windows용 requirements 파일 생성 중..." -ForegroundColor Cyan

$coreRequirements = @"
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
datasets==3.6.0

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
"@

$coreRequirements | Out-File -FilePath "$OutputDir\02_Dependencies\requirements.txt" -Encoding UTF8

# 3. Python 패키지 다운로드 (Windows 전용)
if (-not $SkipDownload) {
    Write-Host "Python 패키지 다운로드 시작..." -ForegroundColor Cyan
    Write-Host "  - 플랫폼: Windows 64비트" -ForegroundColor White
    Write-Host "  - Python: 3.11" -ForegroundColor White
    Write-Host "  - PyTorch: CPU 전용" -ForegroundColor White
    Write-Host "  - 예상 시간: 10-30분" -ForegroundColor White
    Write-Host ""

    Push-Location "$OutputDir\02_Dependencies"
    
    try {
        # 핵심 패키지 다운로드
        Write-Host "핵심 패키지 다운로드 중..." -ForegroundColor Yellow
        pip download `
            --platform win_amd64 `
            --python-version 3.11 `
            --only-binary :all: `
            --extra-index-url https://download.pytorch.org/whl/cpu `
            -r requirements.txt `
            -d wheels `
            --timeout 600 `
            --retries 3
            
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ 핵심 패키지 다운로드 완료" -ForegroundColor Green
        } else {
            Write-Warning "  ⚠ 일부 핵심 패키지 다운로드 실패"
        }

        # 추가 의존성 다운로드 (recursive)
        Write-Host "의존성 패키지 다운로드 중..." -ForegroundColor Yellow
        $additionalPackages = @(
            "streamlit", "pandas", "numpy", "torch", "sentence-transformers", 
            "ragas", "dependency-injector", "plotly", "openpyxl", "requests",
            "google-generativeai", "langchain-core", "pydantic", "transformers"
        )
        
        foreach ($package in $additionalPackages) {
            Write-Host "  → $package" -ForegroundColor Gray
            pip download `
                --platform win_amd64 `
                --python-version 3.11 `
                --only-binary :all: `
                --extra-index-url https://download.pytorch.org/whl/cpu `
                $package `
                -d wheels `
                --timeout 300 `
                --quiet
        }
        
        Write-Host "  ✓ 의존성 패키지 다운로드 완료" -ForegroundColor Green
        
    } catch {
        Write-Error "패키지 다운로드 중 오류: $_"
    } finally {
        Pop-Location
    }
} else {
    Write-Host "패키지 다운로드 생략됨 (-SkipDownload 옵션)" -ForegroundColor Yellow
}

# 4. 설치 스크립트 생성
Write-Host "설치 스크립트 생성 중..." -ForegroundColor Cyan

# install.bat
$installScript = @'
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
    echo        우클릭 → "관리자 권한으로 실행"을 선택하세요.
    pause
    exit /b 1
)

:: Python 확인
echo [1/5] Python 3.11 확인 중...
python --version 2>nul | findstr "3.11" >nul
if %errorLevel% neq 0 (
    echo       Python 3.11이 설치되어 있지 않습니다.
    echo       01_Prerequisites\python-3.11.9-amd64.exe를 실행하세요.
    pause
    exit /b 1
)
echo       ✓ Python 3.11 확인 완료

:: VC++ 설치 확인
echo.
echo [2/5] Visual C++ 재배포 가능 패키지 설치
echo       01_Prerequisites\vc_redist.x64.exe를 실행하세요.
pause

:: 작업 디렉토리 설정
echo.
echo [3/5] 작업 디렉토리 설정 중...
cd /d "03_Source"
if %errorLevel% neq 0 (
    echo [오류] 03_Source 디렉토리를 찾을 수 없습니다.
    pause
    exit /b 1
)
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
    echo [오류] 가상환경 생성 실패
    pause
    exit /b 1
)
call .venv\Scripts\activate
echo       ✓ 가상환경 생성 및 활성화 완료

:: 패키지 설치 (완전 오프라인)
echo.
echo [5/5] 패키지 설치 중... (오프라인)
echo       설치 중... 10-20분 소요 예상

:: pip 업그레이드
python -m pip install --upgrade pip --no-index --find-links "..\02_Dependencies\wheels" --quiet

:: 메인 패키지 설치
pip install --no-index --find-links "..\02_Dependencies\wheels" -r "..\02_Dependencies\requirements.txt" --quiet

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
    echo   검증: ..\04_Scripts\verify.bat
) else (
    echo.
    echo [오류] 패키지 설치 실패
    echo       로그를 확인하고 다시 시도하세요.
)

pause
'@

$installScript | Out-File -FilePath "$OutputDir\04_Scripts\install.bat" -Encoding UTF8

# run-web.bat
$runWebScript = @'
@echo off
chcp 65001 >nul
title RAGTrace Web Dashboard

echo ============================================================
echo   RAGTrace 웹 대시보드
echo ============================================================
echo.

cd /d "03_Source"
call .venv\Scripts\activate

echo   URL: http://localhost:8501
echo   종료: Ctrl+C를 누르세요
echo.
echo ============================================================

streamlit run src/presentation/web/main.py
pause
'@

$runWebScript | Out-File -FilePath "$OutputDir\04_Scripts\run-web.bat" -Encoding UTF8

# run-cli.bat  
$runCliScript = @'
@echo off
chcp 65001 >nul
title RAGTrace CLI

cd /d "03_Source"  
call .venv\Scripts\activate

echo RAGTrace CLI 모드
echo.
echo 사용법:
echo   python cli.py --help
echo   python cli.py quick-eval evaluation_data
echo.

cmd /k
'@

$runCliScript | Out-File -FilePath "$OutputDir\04_Scripts\run-cli.bat" -Encoding UTF8

# verify.bat
$verifyScript = @'
@echo off
chcp 65001 >nul
cd /d "03_Source"
call .venv\Scripts\activate
python ..\04_Scripts\verify.py
pause
'@

$verifyScript | Out-File -FilePath "$OutputDir\04_Scripts\verify.bat" -Encoding UTF8

# 5. 검증 스크립트 생성
Write-Host "검증 스크립트 생성 중..." -ForegroundColor Cyan

$verifyPython = @'
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
    else:
        print("✅ Python 버전 OK")
    
    # 가상환경 확인
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"🔧 가상환경: {'✅ 활성화됨' if venv_active else '❌ 미활성화'}")
    
    if not venv_active:
        print("   .venv\\Scripts\\activate 를 먼저 실행하세요.")
    
    # 핵심 패키지 확인
    core_packages = [
        'streamlit', 'pandas', 'numpy', 'torch', 
        'sentence_transformers', 'ragas', 'dependency_injector',
        'plotly', 'openpyxl', 'requests', 'google.generativeai'
    ]
    
    print("\n📦 핵심 패키지 확인:")
    all_ok = True
    for pkg in core_packages:
        try:
            pkg_import = pkg.replace('-', '_').replace('.', '_')
            module = importlib.import_module(pkg_import)
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
        if is_cpu:
            print(f"   버전: {torch.__version__}")
    except:
        print("\n🔥 PyTorch: ❌ 미설치")
        all_ok = False
    
    # 환경 파일 확인
    env_exists = Path(".env").exists()
    env_example_exists = Path(".env.example").exists()
    print(f"\n⚙️ 환경 설정:")
    if env_exists:
        print("   ✅ .env 파일 존재")
    elif env_example_exists:
        print("   ⚠️ .env.example만 존재 (.env로 복사 필요)")
    else:
        print("   ❌ 환경 설정 파일 없음")
    
    # 결과 출력
    if all_ok and venv_active:
        print("\n" + "=" * 60)
        print("✅ 모든 검증 통과! RAGTrace 사용 준비 완료")
        print("=" * 60)
        print("\n실행 방법:")
        print("  웹 UI: ..\\04_Scripts\\run-web.bat")
        print("  CLI: ..\\04_Scripts\\run-cli.bat")
        print("\nAPI 키 설정:")
        print("  1. .env.example을 .env로 복사")
        print("  2. 메모장으로 .env 편집")
        print("  3. API 키 입력")
    else:
        print("\n❌ 설치가 완료되지 않았습니다.")
        if not venv_active:
            print("  가상환경을 활성화하고 다시 실행하세요.")
        if not all_ok:
            print("  누락된 패키지를 설치하세요.")
    
    return all_ok and venv_active

if __name__ == "__main__":
    main()
    input("\nEnter 키를 눌러 종료...")
'@

$verifyPython | Out-File -FilePath "$OutputDir\04_Scripts\verify.py" -Encoding UTF8

# 6. 문서 생성
Write-Host "문서 생성 중..." -ForegroundColor Cyan

$readme = @"
RAGTrace 완전 오프라인 설치 패키지 (Windows 전용)
==============================================

이 패키지는 인터넷이 완전히 차단된 폐쇄망 환경에서
RAGTrace를 설치하고 실행하기 위한 모든 파일을 포함합니다.

[사전 준비 - 인터넷 연결된 PC에서]
================================
1. Python 3.11.9 Windows 64비트 다운로드
   https://www.python.org/downloads/release/python-3119/
   → python-3.11.9-amd64.exe

2. Visual C++ 재배포 가능 패키지 다운로드  
   https://aka.ms/vs/17/release/vc_redist.x64.exe
   → vc_redist.x64.exe

3. 두 파일을 01_Prerequisites 폴더에 복사

[폐쇄망 설치 순서]
================
1. 전체 패키지를 폐쇄망 PC로 복사
2. 01_Prerequisites/python-3.11.9-amd64.exe 설치
   - "Add Python to PATH" 체크 필수
3. 01_Prerequisites/vc_redist.x64.exe 설치  
4. 04_Scripts/install.bat을 관리자 권한으로 실행
5. .env.example을 .env로 복사하고 API 키 설정
6. 04_Scripts/verify.bat으로 설치 검증

[실행 방법]
==========
- 웹 UI: 04_Scripts/run-web.bat
- CLI: 04_Scripts/run-cli.bat

[API 키 설정]
============
1. 03_Source/.env.example을 .env로 복사
2. 메모장으로 .env 파일 편집
3. API 키 입력:
   GEMINI_API_KEY=your_gemini_key_here
   CLOVA_STUDIO_API_KEY=your_hcx_key_here

[패키지 구성]
===========
- 01_Prerequisites: Python 및 VC++ 설치 파일
- 02_Dependencies: Python 패키지 wheel 파일 (완전 오프라인)
- 03_Source: RAGTrace 소스 코드
- 04_Scripts: 설치/실행/검증 스크립트
- 05_Documentation: 추가 문서

[시스템 요구사항]
===============
✅ Windows 10 64비트 이상
✅ Python 3.11.9
✅ 10GB 이상 디스크 공간
✅ 8GB 이상 RAM
❌ GPU 불필요 (CPU 전용)
❌ 인터넷 연결 불필요 (설치 후)

[특징]
=====
✅ 완전 오프라인 설치 및 실행
✅ 모든 의존성 사전 포함 ($(Get-ChildItem "$OutputDir\02_Dependencies\wheels" -File 2>/dev/null | Measure-Object).Count 개 패키지)
✅ HCX-005 + BGE-M3 API 지원  
✅ Excel/CSV 데이터 import 지원
✅ 웹 UI 및 CLI 지원
✅ 체크포인트 기능 (대용량 데이터셋)

[문제 해결]
==========
- 설치 실패 시: install.bat을 관리자 권한으로 재실행
- 실행 실패 시: verify.bat으로 문제 확인
- API 오류 시: .env 파일의 API 키 확인
- 웹 UI 접속 불가 시: 방화벽 및 브라우저 확인

생성일: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
패키지 버전: 1.0
"@

$readme | Out-File -FilePath "$OutputDir\README-설치가이드.txt" -Encoding UTF8

# Prerequisites 안내
$prereqReadme = @"
필수 설치 파일 다운로드 안내
==========================

폐쇄망 설치를 위해 다음 파일들을 이 폴더에 복사하세요:

1. python-3.11.9-amd64.exe
   다운로드: https://www.python.org/downloads/release/python-3119/
   크기: 약 30MB
   중요: 설치 시 "Add Python to PATH" 옵션 체크 필수

2. vc_redist.x64.exe  
   다운로드: https://aka.ms/vs/17/release/vc_redist.x64.exe
   크기: 약 14MB
   목적: C++ 확장 모듈 실행에 필요

파일 복사 후 폴더 구조:
01_Prerequisites/
├── python-3.11.9-amd64.exe
├── vc_redist.x64.exe
└── README.txt (이 파일)

주의: 두 파일 모두 인터넷이 연결된 PC에서 다운로드 후 복사해야 합니다.
"@

$prereqReadme | Out-File -FilePath "$OutputDir\01_Prerequisites\README.txt" -Encoding UTF8

# 7. 체크섬 생성
Write-Host "체크섬 파일 생성 중..." -ForegroundColor Cyan

function Generate-Checksums {
    param($Path, $OutputFile)
    
    if (Test-Path $Path) {
        Get-ChildItem -Path $Path -File | ForEach-Object {
            $hash = Get-FileHash $_.FullName -Algorithm SHA256
            "$($hash.Hash)  $($_.Name)" | Out-File -Append $OutputFile -Encoding UTF8
        }
    }
}

Generate-Checksums -Path "$OutputDir\02_Dependencies\wheels" -OutputFile "$OutputDir\02_Dependencies\checksums.txt"
Generate-Checksums -Path "$OutputDir\03_Source" -OutputFile "$OutputDir\03_Source\checksums.txt"

# 8. 패키지 정보 출력
Write-Host ""
Write-Host "📊 패키지 생성 결과:" -ForegroundColor Green
$wheelCount = (Get-ChildItem "$OutputDir\02_Dependencies\wheels" -File 2>/dev/null | Measure-Object).Count
$packageSize = if (Test-Path $OutputDir) { (Get-ChildItem $OutputDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB } else { 0 }

Write-Host "   디렉토리: $OutputDir" -ForegroundColor White
Write-Host "   wheel 파일: $wheelCount 개" -ForegroundColor White  
Write-Host "   크기: $([math]::Round($packageSize, 1)) MB" -ForegroundColor White

# 9. 압축
Write-Host ""
Write-Host "📦 패키지 압축 중..." -ForegroundColor Cyan
$zipPath = "RAGTrace-Windows-Offline.zip"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path $OutputDir -DestinationPath $zipPath -CompressionLevel Optimal
$zipSize = (Get-Item $zipPath).Length / 1MB

# 10. 완료 메시지
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  패키지 생성 완료!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📄 출력 파일: $zipPath" -ForegroundColor Yellow
Write-Host "📏 압축 크기: $([math]::Round($zipSize, 1)) MB" -ForegroundColor Yellow
Write-Host "⏱️ 소요 시간: $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 다음 단계:" -ForegroundColor Cyan
Write-Host "1. 압축 해제 후 01_Prerequisites에 Python/VC++ 파일 추가" -ForegroundColor White
Write-Host "2. 전체 패키지를 폐쇄망 PC로 복사" -ForegroundColor White
Write-Host "3. README-설치가이드.txt 참고하여 설치" -ForegroundColor White
Write-Host ""
Write-Host "🎯 폐쇄망 설치 준비 완료!" -ForegroundColor Green