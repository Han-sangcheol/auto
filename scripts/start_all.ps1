# 전체 시스템 시작 스크립트

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CleonAI Trading Platform - 전체 시작" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  주의: 이 스크립트는 Backend와 Trading Engine을 백그라운드로 실행합니다." -ForegroundColor Yellow
Write-Host "   Frontend는 별도 창에서 실행하세요." -ForegroundColor Yellow
Write-Host ""

# Docker Compose로 데이터베이스 시작
Write-Host "1️⃣  데이터베이스 시작 (Docker Compose)..." -ForegroundColor Green
docker-compose up -d postgres redis

Start-Sleep -Seconds 5

# Backend 시작 (백그라운드)
Write-Host "2️⃣  Backend API 서버 시작 (백그라운드)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "scripts\start_backend.ps1"

Start-Sleep -Seconds 3

# Trading Engine 시작 안내
Write-Host "3️⃣  Trading Engine 시작..." -ForegroundColor Green
Write-Host "   ⚠️  Trading Engine은 32-bit Python이 필요합니다." -ForegroundColor Yellow
Write-Host "   수동으로 실행하세요: scripts\start_trading_engine.ps1" -ForegroundColor Yellow
Write-Host ""

# Frontend 시작 안내
Write-Host "4️⃣  Frontend 시작..." -ForegroundColor Green
Write-Host "   별도 PowerShell 창에서 실행하세요:" -ForegroundColor Cyan
Write-Host "   > scripts\start_frontend.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "================================================" -ForegroundColor Green
Write-Host "  시스템 시작 완료!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "접속 URL:" -ForegroundColor Cyan
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Frontend: GUI 창" -ForegroundColor White
Write-Host ""

