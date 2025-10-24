# Frontend 시작 스크립트

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CleonAI Trading Platform - Frontend 시작" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 프로젝트 루트로 이동
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# 가상환경 확인
if (-not (Test-Path ".venv")) {
    Write-Host "가상환경이 없습니다. 먼저 setup_frontend.ps1을 실행하세요." -ForegroundColor Red
    exit 1
}

# 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Frontend 디렉토리로 이동
Set-Location frontend

# Backend 연결 확인
Write-Host "Backend 연결 확인 중..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -UseBasicParsing
    Write-Host "✅ Backend 연결 성공" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend에 연결할 수 없습니다." -ForegroundColor Yellow
    Write-Host "   Backend를 먼저 시작해야 합니다: scripts\start_backend.ps1" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "계속 진행하시겠습니까? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Frontend 실행
Write-Host ""
Write-Host "Frontend 실행 중..." -ForegroundColor Green
python main.py

