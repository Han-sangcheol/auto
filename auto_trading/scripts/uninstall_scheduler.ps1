# CleonAI 자동매매 스케줄러 제거 스크립트
# Windows 작업 스케줄러에서 자동 시작/종료 작업 제거

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CleonAI 자동매매 스케줄러 제거" -ForegroundColor Cyan
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

# 기존 작업 확인
$existingTask = Get-ScheduledTask -TaskName "CleonAI_AutoTrading" -ErrorAction SilentlyContinue

if (-not $existingTask) {
    Write-Host "⚠️  'CleonAI_AutoTrading' 작업을 찾을 수 없습니다." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "스케줄러가 이미 제거되었거나 설치되지 않았습니다." -ForegroundColor Gray
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
    exit 0
}

Write-Host "발견된 작업:" -ForegroundColor Cyan
Write-Host "  - 이름: $($existingTask.TaskName)" -ForegroundColor White
Write-Host "  - 상태: $($existingTask.State)" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "이 작업을 제거하시겠습니까? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "제거가 취소되었습니다." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "스케줄러 제거 중..." -ForegroundColor Cyan

try {
    Unregister-ScheduledTask -TaskName "CleonAI_AutoTrading" -Confirm:$false
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ 스케줄러 제거 완료!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "'CleonAI_AutoTrading' 작업이 제거되었습니다." -ForegroundColor White
    Write-Host ""
    Write-Host "프로그램은 더 이상 자동으로 시작되지 않습니다." -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ 오류: 스케줄러 제거 실패" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

Read-Host "계속하려면 Enter를 누르세요"

