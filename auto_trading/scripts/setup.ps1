﻿# CleonAI Auto-Trading Setup Script (32-bit Python)
# UTF-8 Encoding Support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Change to auto_trading directory (parent of scripts folder)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptPath "..")

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   CleonAI Auto-Trading Setup" -ForegroundColor Cyan
Write-Host "   (32-bit Python for Kiwoom API)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Determine Python 32-bit path
$python32 = $null

# Check for C:\Python32 first (recommended)
if (Test-Path "C:\Python32\python.exe") {
    Write-Host "[Found] Python 32-bit at C:\Python32\" -ForegroundColor Green
    $python32 = "C:\Python32\python.exe"
} else {
    Write-Host "[!] Python 32-bit not found at C:\Python32\" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Checking system Python..." -ForegroundColor Yellow
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python is not installed."
        }
        
        # Check if system Python is 32-bit
        $is64bit = & python -c "import sys; print(sys.maxsize > 2**32)" 2>$null
        if ($is64bit -eq "True") {
            Write-Host "[ERROR] System Python is 64-bit!" -ForegroundColor Red
            Write-Host ""
            Write-Host "Kiwoom API requires 32-bit Python." -ForegroundColor Yellow
            Write-Host "Please install Python 32-bit:" -ForegroundColor Yellow
            Write-Host "  scripts\install_python32.ps1" -ForegroundColor White
            Write-Host ""
            Read-Host "Press Enter to exit"
            exit 1
        }
        
        $python32 = "python"
        Write-Host "[OK] System Python is 32-bit" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] No Python found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install Python 32-bit:" -ForegroundColor Yellow
        Write-Host "1. Run: scripts\install_python32.ps1" -ForegroundColor White
        Write-Host "2. Or download from: https://www.python.org/downloads/" -ForegroundColor White
        Write-Host "   (Select Windows installer 32-bit)" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
}

$pythonVersion = & $python32 --version 2>&1
Write-Host "Python version: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Create Virtual Environment in project root (.venv32)
# Go to project root (parent of auto_trading)
Set-Location ..
if (-not (Test-Path ".venv32")) {
    Write-Host "Creating 32-bit virtual environment (.venv32)..." -ForegroundColor Yellow
    & $python32 -m venv .venv32
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Check if Python 32-bit is properly installed" -ForegroundColor White
        Write-Host "2. Try running as Administrator" -ForegroundColor White
        Write-Host "3. Check disk space" -ForegroundColor White
        Write-Host ""
        Set-Location auto_trading
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Virtual environment created!" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment (.venv32) already exists." -ForegroundColor Green
}

# Go back to auto_trading folder
Set-Location auto_trading
Write-Host ""

# Activate Virtual Environment
Write-Host "Activating 32-bit virtual environment..." -ForegroundColor Yellow
$activateScript = "..\.venv32\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Failed to activate virtual environment" -ForegroundColor Yellow
        Write-Host "Continuing anyway..." -ForegroundColor Yellow
    } else {
        Write-Host "[Done] Virtual environment activated!" -ForegroundColor Green
    }
} else {
    Write-Host "[Warning] Virtual environment activation script not found." -ForegroundColor Yellow
    Write-Host "Continuing..." -ForegroundColor Yellow
}
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& "..\.venv32\Scripts\python.exe" -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Warning] Failed to upgrade pip. Continuing..." -ForegroundColor Yellow
}
Write-Host ""

# Install Packages
if (Test-Path "requirements.txt") {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    Write-Host "(This may take about 5 minutes)" -ForegroundColor Gray
    Write-Host ""
    & "..\.venv32\Scripts\python.exe" -m pip install -r requirements.txt
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

