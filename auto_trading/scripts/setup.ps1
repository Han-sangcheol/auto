﻿# CleonAI Auto-Trading Setup Script
# UTF-8 Encoding Support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   CleonAI Auto-Trading Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python Version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python is not installed."
    }
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
    Write-Host ""
    
    # Check if Python version is 3.11 or higher
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "[Warning] Python 3.11 or higher is recommended." -ForegroundColor Yellow
            Write-Host "Current version: Python $major.$minor" -ForegroundColor Yellow
            Write-Host ""
        }
    }
} catch {
    Write-Host "[Error] Python is not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.11 or higher." -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to continue"
    exit 1
}

# Create Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[Error] Failed to create virtual environment." -ForegroundColor Red
        Read-Host "Press Enter to continue"
        exit 1
    }
    Write-Host "[Done] Virtual environment created!" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment already exists." -ForegroundColor Green
}
Write-Host ""

# Activate Virtual Environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$activateScript = ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[Done] Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "[Warning] Virtual environment activation script not found." -ForegroundColor Yellow
    Write-Host "Continuing..." -ForegroundColor Yellow
}
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Warning] Failed to upgrade pip. Continuing..." -ForegroundColor Yellow
}
Write-Host ""

# Install Packages
if (Test-Path "requirements.txt") {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    Write-Host "(This may take about 5 minutes)" -ForegroundColor Gray
    Write-Host ""
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[Error] Failed to install packages." -ForegroundColor Red
        Write-Host "Please check requirements.txt file." -ForegroundColor Yellow
        Read-Host "Press Enter to continue"
        exit 1
    }
    Write-Host "[Done] Packages installed!" -ForegroundColor Green
} else {
    Write-Host "[Warning] requirements.txt file not found." -ForegroundColor Yellow
}
Write-Host ""

# Create logs Directory
if (-not (Test-Path "logs")) {
    Write-Host "Creating logs directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "[Done] Logs directory created!" -ForegroundColor Green
} else {
    Write-Host "[OK] Logs directory already exists." -ForegroundColor Green
}
Write-Host ""

# Check and Create .env File
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "   Creating .env file..." -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-Path "env.template") {
        Copy-Item "env.template" ".env"
        Write-Host "[Success] .env file created." -ForegroundColor Green
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Yellow
        Write-Host "   IMPORTANT: Edit .env file!" -ForegroundColor Yellow
        Write-Host "==========================================" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor White
        Write-Host "1. Open .env file with Notepad" -ForegroundColor White
        Write-Host "2. Fill in required fields:" -ForegroundColor White
        Write-Host "   - KIWOOM_ACCOUNT_NUMBER (account number)" -ForegroundColor White
        Write-Host "   - KIWOOM_ACCOUNT_PASSWORD (4-digit password)" -ForegroundColor White
        Write-Host "   - WATCH_LIST (stocks to watch)" -ForegroundColor White
        Write-Host ""
        Write-Host "Example:" -ForegroundColor Gray
        Write-Host "KIWOOM_ACCOUNT_NUMBER=8123456789" -ForegroundColor Gray
        Write-Host "KIWOOM_ACCOUNT_PASSWORD=1234" -ForegroundColor Gray
        Write-Host "WATCH_LIST=005930,000660,035720" -ForegroundColor Gray
        Write-Host ""
    } elseif (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[Success] .env file created." -ForegroundColor Green
        Write-Host "Please edit .env file to complete setup." -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "[Warning] env.template file not found." -ForegroundColor Yellow
        Write-Host "Please create .env file manually." -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "[OK] .env file already exists." -ForegroundColor Green
    Write-Host ""
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "[Step 1] Configure .env file" -ForegroundColor Yellow
Write-Host "   - Open auto_trading\.env with Notepad" -ForegroundColor White
Write-Host "   - Enter account info and stock list" -ForegroundColor White
Write-Host "   - Save and close" -ForegroundColor White
Write-Host ""
Write-Host "[Step 2] Setup Kiwoom Open API (First time users)" -ForegroundColor Yellow
Write-Host "   - See KIWOOM_API_SETUP.md" -ForegroundColor White
Write-Host "   - Install Open API+ program" -ForegroundColor White
Write-Host "   - Prepare digital certificate" -ForegroundColor White
Write-Host ""
Write-Host "[Step 3] Run the program" -ForegroundColor Yellow
Write-Host "   - Right-click start.ps1 -> 'Run with PowerShell'" -ForegroundColor White
Write-Host "   OR in PowerShell: .\start.ps1" -ForegroundColor White
Write-Host "   - Login with digital certificate" -ForegroundColor White
Write-Host ""
Write-Host "Detailed guide: GETTING_STARTED.md" -ForegroundColor Gray
Write-Host "Quick start: QUICKSTART.md" -ForegroundColor Gray
Write-Host ""

# PowerShell Execution Policy Note
Write-Host "** PowerShell Execution Policy Note **" -ForegroundColor Cyan
Write-Host "If you encounter execution policy error, run:" -ForegroundColor Gray
Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit"

