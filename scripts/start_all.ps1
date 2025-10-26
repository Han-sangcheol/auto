# CleonAI Trading Platform - Start All Services

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CleonAI Trading Platform - Starting All" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Note: This script starts Backend and Trading Engine in background." -ForegroundColor Yellow
Write-Host "      Please start Frontend manually in a separate window." -ForegroundColor Yellow
Write-Host ""

# Start Docker services
Write-Host "1. Starting Database (Docker Compose)..." -ForegroundColor Green
docker-compose up -d postgres redis

Start-Sleep -Seconds 5

# Start Backend (background)
Write-Host "2. Starting Backend API Server (background)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "scripts\start_backend.ps1"

Start-Sleep -Seconds 3

# Trading Engine instructions
Write-Host "3. Trading Engine..." -ForegroundColor Green
Write-Host "   Note: Trading Engine requires 32-bit Python." -ForegroundColor Yellow
Write-Host "   Please run manually: scripts\start_trading_engine.ps1" -ForegroundColor Yellow
Write-Host ""

# Frontend instructions
Write-Host "4. Frontend..." -ForegroundColor Green
Write-Host "   Please run in a separate PowerShell window:" -ForegroundColor Cyan
Write-Host "   > scripts\start_frontend.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "================================================" -ForegroundColor Green
Write-Host "  System Started!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Frontend: GUI Window" -ForegroundColor White
Write-Host ""
