# RAGTrace Windows 패키지 생성 테스트 스크립트
# PowerShell 관리자 권한으로 실행

param(
    [switch]$QuickTest = $false,
    [switch]$FullTest = $false,
    [switch]$CleanUp = $false
)

$ErrorActionPreference = "Continue"

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Result,
        [string]$Details = ""
    )
    
    $status = if ($Result) { "✅ PASS" } else { "❌ FAIL" }
    $color = if ($Result) { "Green" } else { "Red" }
    
    Write-Host "$status $TestName" -ForegroundColor $color
    if ($Details) {
        Write-Host "   $Details" -ForegroundColor Gray
    }
}

function Test-Prerequisites {
    Write-Host "`n🔍 사전 조건 테스트" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    $results = @{}
    
    # 관리자 권한 확인
    try {
        $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
        $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        $results["AdminRights"] = $isAdmin
        Write-TestResult "관리자 권한" $isAdmin $(if (-not $isAdmin) { "PowerShell을 관리자 권한으로 실행하세요" })
    } catch {
        $results["AdminRights"] = $false
        Write-TestResult "관리자 권한" $false "권한 확인 실패: $_"
    }
    
    # Python 3.11 확인
    try {
        $pythonVersion = python --version 2>$null
        $hasPython311 = $pythonVersion -match "Python 3\.11"
        $results["Python311"] = $hasPython311
        Write-TestResult "Python 3.11" $hasPython311 $pythonVersion
    } catch {
        $results["Python311"] = $false
        Write-TestResult "Python 3.11" $false "Python이 설치되어 있지 않음"
    }
    
    # pip 확인
    try {
        $pipVersion = pip --version 2>$null
        $hasPip = $pipVersion -ne $null
        $results["Pip"] = $hasPip
        Write-TestResult "pip" $hasPip $(if ($hasPip) { $pipVersion } else { "pip 없음" })
    } catch {
        $results["Pip"] = $false
        Write-TestResult "pip" $false "pip 확인 실패"
    }
    
    # 프로젝트 파일 확인
    $requiredFiles = @("cli.py", "src", "pyproject.toml", "README.md")
    $fileResults = @()
    
    foreach ($file in $requiredFiles) {
        $exists = Test-Path $file
        $fileResults += $exists
        Write-TestResult "파일: $file" $exists
    }
    
    $results["ProjectFiles"] = $fileResults -notcontains $false
    
    # 인터넷 연결 확인
    try {
        $testConnection = Test-NetConnection -ComputerName "pypi.org" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
        $results["Internet"] = $testConnection
        Write-TestResult "인터넷 연결 (PyPI)" $testConnection
    } catch {
        $results["Internet"] = $false
        Write-TestResult "인터넷 연결 (PyPI)" $false "연결 테스트 실패"
    }
    
    # 디스크 공간 확인 (10GB 이상)
    try {
        $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        $freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
        $hasSpace = $freeSpaceGB -gt 10
        $results["DiskSpace"] = $hasSpace
        Write-TestResult "디스크 공간 (10GB+)" $hasSpace "$freeSpaceGB GB 사용 가능"
    } catch {
        $results["DiskSpace"] = $false
        Write-TestResult "디스크 공간 (10GB+)" $false "디스크 공간 확인 실패"
    }
    
    return $results
}

function Test-ScriptGeneration {
    Write-Host "`n📝 스크립트 생성 테스트" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    $results = @{}
    $scripts = @{
        "create-windows-offline-safe.ps1" = "완전 오프라인 스크립트"
        "create-simple-offline.sh" = "간단 설치 스크립트"
        "WINDOWS_오류해결가이드.md" = "오류 해결 가이드"
    }
    
    foreach ($script in $scripts.Keys) {
        $exists = Test-Path $script
        $results[$script] = $exists
        Write-TestResult $scripts[$script] $exists $(if (-not $exists) { "파일이 없습니다: $script" })
        
        if ($exists) {
            # 파일 크기 확인 (최소 1KB)
            $size = (Get-Item $script).Length
            $validSize = $size -gt 1024
            Write-TestResult "  파일 크기 확인" $validSize "$([math]::Round($size/1024, 2)) KB"
        }
    }
    
    return $results
}

function Test-QuickPackageGeneration {
    Write-Host "`n⚡ 빠른 패키지 생성 테스트" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    $results = @{}
    
    try {
        # 간단한 테스트 패키지 생성
        Write-Host "테스트 패키지 생성 중..." -ForegroundColor Yellow
        
        $testDir = "RAGTrace-Test-Package"
        if (Test-Path $testDir) {
            Remove-Item -Path $testDir -Recurse -Force
        }
        
        # 기본 구조 생성
        $dirs = @(
            "$testDir\01_Prerequisites",
            "$testDir\02_Dependencies",
            "$testDir\03_Source",
            "$testDir\04_Scripts"
        )
        
        foreach ($dir in $dirs) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
        }
        
        # 테스트 파일 생성
        "Test requirements file" | Out-File -FilePath "$testDir\02_Dependencies\requirements.txt"
        "@echo off`necho Test install script" | Out-File -FilePath "$testDir\04_Scripts\install.bat"
        
        $results["StructureCreation"] = $true
        Write-TestResult "디렉토리 구조 생성" $true
        
        # 소스 파일 복사 테스트
        if (Test-Path "cli.py") {
            Copy-Item "cli.py" "$testDir\03_Source\" -ErrorAction SilentlyContinue
            $results["FileCopy"] = Test-Path "$testDir\03_Source\cli.py"
            Write-TestResult "파일 복사" $results["FileCopy"]
        }
        
        # 압축 테스트
        $zipPath = "$testDir.zip"
        Compress-Archive -Path $testDir -DestinationPath $zipPath -ErrorAction SilentlyContinue
        $results["Compression"] = Test-Path $zipPath
        Write-TestResult "압축 생성" $results["Compression"]
        
        if ($CleanUp) {
            Remove-Item -Path $testDir -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue
        }
        
    } catch {
        $results["OverallTest"] = $false
        Write-TestResult "전체 테스트" $false "오류: $_"
    }
    
    return $results
}

function Test-FullPackageGeneration {
    Write-Host "`n🔄 전체 패키지 생성 테스트" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    $results = @{}
    
    if (-not $FullTest) {
        Write-Host "⏭️ 전체 테스트 생략 (-FullTest 옵션으로 실행)" -ForegroundColor Yellow
        return @{"Skipped" = $true}
    }
    
    try {
        Write-Host "완전 오프라인 스크립트 실행 중... (시간이 오래 걸릴 수 있습니다)" -ForegroundColor Yellow
        
        # 안전 스크립트 실행
        if (Test-Path "create-windows-offline-safe.ps1") {
            $process = Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File create-windows-offline-safe.ps1 -SkipDownload" -Wait -PassThru -WindowStyle Hidden
            
            $results["ScriptExecution"] = $process.ExitCode -eq 0
            Write-TestResult "스크립트 실행" $results["ScriptExecution"] "Exit Code: $($process.ExitCode)"
            
            # 결과 확인
            $packageExists = Test-Path "RAGTrace-Windows-Offline-Safe.zip"
            $results["PackageGeneration"] = $packageExists
            Write-TestResult "패키지 생성" $packageExists
            
        } else {
            $results["ScriptExecution"] = $false
            Write-TestResult "스크립트 실행" $false "create-windows-offline-safe.ps1 파일이 없음"
        }
        
    } catch {
        $results["OverallTest"] = $false
        Write-TestResult "전체 생성 테스트" $false "오류: $_"
    }
    
    return $results
}

function Test-ValidationScripts {
    Write-Host "`n🔍 검증 스크립트 테스트" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    $results = @{}
    
    # Python 검증 스크립트 기본 테스트
    try {
        $verifyScript = @'
import sys
import platform
print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print("Basic validation: OK")
'@
        
        $verifyScript | Out-File -FilePath "test_verify.py" -Encoding UTF8
        
        $output = python test_verify.py 2>&1
        $results["PythonValidation"] = $output -match "Basic validation: OK"
        Write-TestResult "Python 검증 스크립트" $results["PythonValidation"]
        
        Remove-Item "test_verify.py" -ErrorAction SilentlyContinue
        
    } catch {
        $results["PythonValidation"] = $false
        Write-TestResult "Python 검증 스크립트" $false "테스트 실패: $_"
    }
    
    return $results
}

function Show-TestSummary {
    param(
        [hashtable]$PrereqResults,
        [hashtable]$ScriptResults,
        [hashtable]$QuickResults,
        [hashtable]$FullResults,
        [hashtable]$ValidationResults
    )
    
    Write-Host "`n📊 테스트 결과 요약" -ForegroundColor Cyan
    Write-Host "=" * 60
    
    $allResults = @()
    $allResults += $PrereqResults.Values
    $allResults += $ScriptResults.Values
    $allResults += $QuickResults.Values
    if ($FullResults.Count -gt 0 -and -not $FullResults.ContainsKey("Skipped")) {
        $allResults += $FullResults.Values
    }
    $allResults += $ValidationResults.Values
    
    $passCount = ($allResults | Where-Object { $_ -eq $true }).Count
    $totalCount = $allResults.Count
    $passRate = if ($totalCount -gt 0) { [math]::Round(($passCount / $totalCount) * 100, 1) } else { 0 }
    
    Write-Host ""
    Write-Host "통과: $passCount / $totalCount ($passRate%)" -ForegroundColor $(if ($passRate -ge 80) { "Green" } elseif ($passRate -ge 60) { "Yellow" } else { "Red" })
    
    Write-Host ""
    Write-Host "📋 권장 사항:" -ForegroundColor Yellow
    
    if (-not $PrereqResults["AdminRights"]) {
        Write-Host "• PowerShell을 관리자 권한으로 실행하세요" -ForegroundColor White
    }
    
    if (-not $PrereqResults["Python311"]) {
        Write-Host "• Python 3.11을 설치하고 PATH에 추가하세요" -ForegroundColor White
    }
    
    if (-not $PrereqResults["Internet"]) {
        Write-Host "• 인터넷 연결을 확인하세요 (완전 오프라인 모드에서는 필요 없음)" -ForegroundColor White
    }
    
    if (-not $PrereqResults["DiskSpace"]) {
        Write-Host "• 디스크 공간을 확보하세요 (10GB 이상 권장)" -ForegroundColor White
    }
    
    if ($passRate -ge 80) {
        Write-Host "`n✅ 패키지 생성 준비가 완료되었습니다!" -ForegroundColor Green
        Write-Host "   다음 명령으로 패키지를 생성하세요:" -ForegroundColor Green
        Write-Host "   .\create-windows-offline-safe.ps1" -ForegroundColor Cyan
    } else {
        Write-Host "`n❌ 일부 문제를 해결한 후 다시 시도하세요." -ForegroundColor Red
        Write-Host "   자세한 도움말: WINDOWS_오류해결가이드.md" -ForegroundColor Yellow
    }
}

# 메인 실행
function Main {
    Write-Host "============================================================" -ForegroundColor Blue
    Write-Host "  RAGTrace Windows 패키지 생성 테스트" -ForegroundColor Blue
    Write-Host "============================================================" -ForegroundColor Blue
    Write-Host ""
    
    $startTime = Get-Date
    
    # 테스트 실행
    $prereqResults = Test-Prerequisites
    $scriptResults = Test-ScriptGeneration
    $quickResults = if ($QuickTest -or -not $FullTest) { Test-QuickPackageGeneration } else { @{} }
    $fullResults = if ($FullTest) { Test-FullPackageGeneration } else { @{} }
    $validationResults = Test-ValidationScripts
    
    # 결과 요약
    Show-TestSummary $prereqResults $scriptResults $quickResults $fullResults $validationResults
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "⏱️ 테스트 완료 시간: $($duration.ToString('mm\:ss'))" -ForegroundColor Gray
}

# 도움말
if ($args -contains "-h" -or $args -contains "--help") {
    Write-Host "RAGTrace Windows 패키지 테스트 스크립트" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "사용법:" -ForegroundColor Yellow
    Write-Host "  .\test-windows-package.ps1                # 기본 테스트"
    Write-Host "  .\test-windows-package.ps1 -QuickTest     # 빠른 테스트만"
    Write-Host "  .\test-windows-package.ps1 -FullTest      # 전체 테스트"
    Write-Host "  .\test-windows-package.ps1 -CleanUp       # 테스트 후 임시 파일 삭제"
    Write-Host ""
    Write-Host "옵션:" -ForegroundColor Yellow
    Write-Host "  -QuickTest  : 빠른 패키지 생성 테스트만 실행"
    Write-Host "  -FullTest   : 실제 패키지 생성 테스트 포함 (시간 오래 걸림)"
    Write-Host "  -CleanUp    : 테스트 완료 후 임시 파일 삭제"
    Write-Host ""
    exit 0
}

# 스크립트 실행
Main