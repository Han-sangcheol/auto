# CleonAI Backend 시작 스크립트

Write-Host "Starting CleonAI Backend API Server..." -ForegroundColor Green
Write-Host ""

Set-Location backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

