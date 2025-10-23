# Complete Automated Setup Script
# Downloads Python 32-bit, installs it, and sets up the trading environment

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   CleonAI Auto-Trading - Complete Automated Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Download and install Python 3.11 32-bit" -ForegroundColor White
Write-Host "  2. Create isolated virtual environment" -ForegroundColor White
Write-Host "  3. Install all required packages (pandas 1.5.3)" -ForegroundColor White
Write-Host "  4. Configure .env file" -ForegroundColor White
Write-Host ""
Write-Host "Your system Python will NOT be affected!" -ForegroundColor Green
Write-Host ""
Write-Host "Starting automated installation in 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Phase 1: Python 32-bit Installation" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Run Python installer script
if (Test-Path "install_python32.ps1") {
    & .\install_python32.ps1 -Automated
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[Error] Python installation failed!" -ForegroundColor Red
        Write-Host "Please check the error messages above." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[Error] install_python32.ps1 not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Phase 2: Virtual Environment Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Run virtual environment setup script
if (Test-Path "setup_python32.ps1") {
    & .\setup_python32.ps1 -Automated
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[Error] Virtual environment setup failed!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[Error] setup_python32.ps1 not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   Complete Setup Finished!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "What's been installed:" -ForegroundColor Cyan
Write-Host "  ✓ Python 3.12 32-bit at C:\Python32\" -ForegroundColor White
Write-Host "  ✓ Virtual environment at .venv\" -ForegroundColor White
Write-Host "  ✓ All required packages" -ForegroundColor White
Write-Host "  ✓ Configuration template (.env)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Edit .env file:" -ForegroundColor Yellow
Write-Host "   - Open: auto_trading\.env with Notepad" -ForegroundColor White
Write-Host "   - Enter your Kiwoom account details" -ForegroundColor White
Write-Host "   - Save and close" -ForegroundColor White
Write-Host ""
Write-Host "2. Install Kiwoom Open API+:" -ForegroundColor Yellow
Write-Host "   - See: KIWOOM_API_SETUP.md" -ForegroundColor White
Write-Host "   - Download from Kiwoom website" -ForegroundColor White
Write-Host "   - Install and restart PC" -ForegroundColor White
Write-Host ""
Write-Host "3. Run the program:" -ForegroundColor Yellow
Write-Host "   .\start.ps1  or  .\start.bat" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - GETTING_STARTED.md (complete guide)" -ForegroundColor Gray
Write-Host "  - KIWOOM_API_SETUP.md (API setup)" -ForegroundColor Gray
Write-Host "  - TROUBLESHOOTING.md (problem solving)" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"

