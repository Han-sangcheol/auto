# Backend 시작 스크립트

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CleonAI Trading Platform - Backend 시작" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 프로젝트 루트로 이동
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# 가상환경 확인
if (-not (Test-Path ".venv")) {
    Write-Host "가상환경이 없습니다. 먼저 setup_backend.ps1을 실행하세요." -ForegroundColor Red
    exit 1
}

# 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Backend 디렉토리로 이동
Set-Location backend

# .env 파일 확인
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env 파일이 없습니다." -ForegroundColor Yellow
    Write-Host "   .env.example을 복사하여 .env 파일을 생성하세요." -ForegroundColor Yellow
    Write-Host ""
}

# 데이터베이스 연결 확인
Write-Host "데이터베이스 연결 확인 중..." -ForegroundColor Yellow
# TODO: PostgreSQL 연결 확인 로직

# Backend 실행
Write-Host ""
Write-Host "Backend API 서버 실행 중..." -ForegroundColor Green
Write-Host "  - URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
