# Backend 설정 스크립트

Write-Host "Setting up CleonAI Backend..." -ForegroundColor Green

# 1. Backend 디렉토리로 이동
Set-Location backend

# 2. 가상환경 생성
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# 3. 가상환경 활성화
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# 4. 패키지 설치
Write-Host "Installing Python packages..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# 5. 완료
Write-Host ""
Write-Host "Backend setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Start Docker services: docker-compose up -d postgres redis" -ForegroundColor White
Write-Host "2. Run backend: python app/main.py" -ForegroundColor White
Write-Host "3. Open API docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

