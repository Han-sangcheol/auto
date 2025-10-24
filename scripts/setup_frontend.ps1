# Frontend 환경 설정 스크립트

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CleonAI Trading Platform - Frontend 설정" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 프로젝트 루트로 이동
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# 가상환경 생성
Write-Host "1️⃣  가상환경 생성 중..." -ForegroundColor Green
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ 가상환경 생성 완료" -ForegroundColor Green
} else {
    Write-Host "✅ 가상환경이 이미 존재합니다." -ForegroundColor Yellow
}

# 가상환경 활성화
Write-Host "2️⃣  가상환경 활성화 중..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Frontend 패키지 설치
Write-Host "3️⃣  Frontend 패키지 설치 중..." -ForegroundColor Green
Set-Location frontend
pip install -r requirements.txt

# .env 파일 생성
Write-Host "4️⃣  환경 변수 파일 생성..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env 파일 생성 완료 (필요시 수정하세요)" -ForegroundColor Green
} else {
    Write-Host "✅ .env 파일이 이미 존재합니다." -ForegroundColor Yellow
}

# 로그 디렉토리 생성
Write-Host "5️⃣  로그 디렉토리 생성..." -ForegroundColor Green
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "✅ 로그 디렉토리 생성 완료" -ForegroundColor Green
}

Set-Location $projectRoot

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Frontend 설정 완료!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Cyan
Write-Host "  1. Backend를 먼저 시작하세요: scripts\start_backend.ps1" -ForegroundColor White
Write-Host "  2. Frontend를 시작하세요: scripts\start_frontend.ps1" -ForegroundColor White
Write-Host ""

