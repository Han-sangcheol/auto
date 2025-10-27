# CleonAI 자동매매 스케줄러 설치 스크립트
# Windows 작업 스케줄러에 자동 시작/종료 작업 등록

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CleonAI 자동매매 스케줄러 설치" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ 오류: 이 스크립트는 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "PowerShell을 '관리자 권한으로 실행'한 후 다시 시도하세요." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

# 현재 스크립트 경로
$scriptPath = $PSScriptRoot
$projectPath = $scriptPath
$pythonExe = Join-Path $projectPath ".venv\Scripts\python.exe"
$mainScript = Join-Path $projectPath "main.py"

# Python 가상환경 확인
if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ 오류: Python 가상환경을 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "경로: $pythonExe" -ForegroundColor Gray
    Write-Host ""
    Write-Host "setup.ps1을 먼저 실행하여 가상환경을 설정하세요." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

# main.py 확인
if (-not (Test-Path $mainScript)) {
    Write-Host "❌ 오류: main.py를 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "경로: $mainScript" -ForegroundColor Gray
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

Write-Host "✅ Python 가상환경 확인 완료" -ForegroundColor Green
Write-Host "   경로: $pythonExe" -ForegroundColor Gray
Write-Host ""

# 사용자 정보
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

Write-Host "설정 정보:" -ForegroundColor Cyan
Write-Host "  - 작업 이름: CleonAI_AutoTrading" -ForegroundColor White
Write-Host "  - 시작 시간: 평일 08:30" -ForegroundColor White
Write-Host "  - 종료 시간: 평일 16:00" -ForegroundColor White
Write-Host "  - 사용자: $currentUser" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "스케줄러를 설치하시겠습니까? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "설치가 취소되었습니다." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "스케줄러 설치 중..." -ForegroundColor Cyan

# 기존 작업 삭제 (있다면)
$existingTask = Get-ScheduledTask -TaskName "CleonAI_AutoTrading" -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "기존 작업 제거 중..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName "CleonAI_AutoTrading" -Confirm:$false
}

# 작업 동작 정의
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument $mainScript -WorkingDirectory $projectPath

# 트리거 정의 (평일 08:30)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "08:30"

# 설정 정의
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 주체 정의 (현재 사용자)
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Highest

# 작업 등록
try {
    Register-ScheduledTask -TaskName "CleonAI_AutoTrading" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "CleonAI 자동매매 프로그램 자동 시작 (평일 08:30)" | Out-Null
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ 스케줄러 설치 완료!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "설정된 작업:" -ForegroundColor Cyan
    Write-Host "  - 이름: CleonAI_AutoTrading" -ForegroundColor White
    Write-Host "  - 실행 시간: 평일 08:30" -ForegroundColor White
    Write-Host "  - 실행 파일: $pythonExe" -ForegroundColor Gray
    Write-Host "  - 스크립트: $mainScript" -ForegroundColor Gray
    Write-Host ""
    Write-Host "확인 방법:" -ForegroundColor Cyan
    Write-Host "  1. '작업 스케줄러' 프로그램 실행 (taskschd.msc)" -ForegroundColor White
    Write-Host "  2. '작업 스케줄러 라이브러리' 확인" -ForegroundColor White
    Write-Host "  3. 'CleonAI_AutoTrading' 작업 찾기" -ForegroundColor White
    Write-Host ""
    Write-Host "제거 방법:" -ForegroundColor Cyan
    Write-Host "  uninstall_scheduler.ps1 실행" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  주의사항:" -ForegroundColor Yellow
    Write-Host "  - 자동 실행을 위해서는 컴퓨터가 켜져 있어야 합니다." -ForegroundColor Gray
    Write-Host "  - 키움 Open API 로그인이 필요합니다." -ForegroundColor Gray
    Write-Host "  - .env 파일에 계좌 정보가 설정되어 있어야 합니다." -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ 오류: 스케줄러 설치 실패" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

Read-Host "계속하려면 Enter를 누르세요"

