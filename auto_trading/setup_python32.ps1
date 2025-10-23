# Automated Python 32-bit Setup Script for Kiwoom API
# This script sets up an isolated Python 32-bit environment

param(
    [switch]$Automated = $false
)

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Python 32-bit Isolated Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python 32-bit is installed
$python32Path = "C:\Python32\python.exe"

Write-Host "Step 1: Checking Python 32-bit installation..." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $python32Path)) {
    Write-Host "[ERROR] Python 32-bit not found at: $python32Path" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 32-bit first:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "2. Select: Windows installer (32-bit)" -ForegroundColor White
    Write-Host "3. Install to: C:\Python32\" -ForegroundColor White
    Write-Host "4. UNCHECK 'Add Python to PATH'" -ForegroundColor Red
    Write-Host ""
    Write-Host "See detailed guide: SETUP_ISOLATED_PYTHON.md" -ForegroundColor Cyan
    Write-Host ""
    if (-not $Automated) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

Write-Host "[OK] Python 32-bit found!" -ForegroundColor Green
Write-Host ""

# Verify it's 32-bit
Write-Host "Step 2: Verifying Python architecture..." -ForegroundColor Yellow
$bitCheck = & $python32Path -c "import sys; print('32' if sys.maxsize <= 2**32 else '64')" 2>&1

if ($bitCheck -match "32") {
    Write-Host "[OK] Confirmed 32-bit Python" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Python at C:\Python32\ is 64-bit!" -ForegroundColor Red
    Write-Host "Please install 32-bit Python to C:\Python32\" -ForegroundColor Yellow
    if (-not $Automated) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

# Show Python version
$pythonVersion = & $python32Path --version 2>&1
Write-Host "Python version: $pythonVersion" -ForegroundColor Cyan
Write-Host ""

# Check if old virtual environment exists
Write-Host "Step 3: Cleaning old virtual environment..." -ForegroundColor Yellow

if (Test-Path ".venv") {
    Write-Host "Old virtual environment found. Removing..." -ForegroundColor Yellow
    
    if (-not $Automated) {
        $confirm = Read-Host "Delete old .venv folder? (yes/no)"
        if ($confirm -eq "yes") {
            Remove-Item -Recurse -Force .venv
            Write-Host "[Done] Old environment removed" -ForegroundColor Green
        } else {
            Write-Host "[Skipped] Keeping old environment" -ForegroundColor Yellow
            Write-Host "Warning: This may cause issues if it's 64-bit" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Automated mode: Removing old environment automatically" -ForegroundColor Yellow
        Remove-Item -Recurse -Force .venv
        Write-Host "[Done] Old environment removed" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] No old environment found" -ForegroundColor Green
}
Write-Host ""

# Create new virtual environment with Python 32-bit
Write-Host "Step 4: Creating new 32-bit virtual environment..." -ForegroundColor Yellow
Write-Host "This may take a minute..." -ForegroundColor Gray
Write-Host ""

& $python32Path -m venv .venv

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
    if (-not $Automated) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

Write-Host "[Done] Virtual environment created!" -ForegroundColor Green
Write-Host ""

# Verify new environment is 32-bit
Write-Host "Step 5: Verifying new environment..." -ForegroundColor Yellow
$venvBitCheck = & .venv\Scripts\python.exe -c "import sys; print('32' if sys.maxsize <= 2**32 else '64')" 2>&1

if ($venvBitCheck -match "32") {
    Write-Host "[OK] Virtual environment is 32-bit!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Virtual environment is still 64-bit!" -ForegroundColor Red
    Write-Host "Something went wrong. Please check the setup." -ForegroundColor Yellow
    if (-not $Automated) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}
Write-Host ""

# Activate and upgrade pip
Write-Host "Step 6: Upgrading pip..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1
& .venv\Scripts\python.exe -m pip install --upgrade pip
Write-Host ""

# Install packages
Write-Host "Step 7: Installing required packages..." -ForegroundColor Yellow
Write-Host "(This may take 5-10 minutes)" -ForegroundColor Gray
Write-Host ""

if (Test-Path "requirements.txt") {
    & .venv\Scripts\python.exe -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Package installation failed" -ForegroundColor Red
        if (-not $Automated) {
            Read-Host "Press Enter to exit"
        }
        exit 1
    }
    
    Write-Host "[Done] All packages installed!" -ForegroundColor Green
} else {
    Write-Host "[Warning] requirements.txt not found" -ForegroundColor Yellow
}
Write-Host ""

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "[Done] Created logs directory" -ForegroundColor Green
}

# Check .env file
Write-Host "Step 8: Checking configuration..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "[Warning] .env file not found" -ForegroundColor Yellow
    
    if (Test-Path "env.template") {
        Copy-Item "env.template" ".env"
        Write-Host "[Done] Created .env file from template" -ForegroundColor Green
        Write-Host ""
        Write-Host "IMPORTANT: Edit .env file with your account information!" -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] .env file exists" -ForegroundColor Green
}
Write-Host ""

# Final summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Environment Details:" -ForegroundColor Cyan
Write-Host "  Python: 32-bit" -ForegroundColor White
Write-Host "  Location: $python32Path" -ForegroundColor White
Write-Host "  Virtual Environment: .venv (32-bit)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your account information" -ForegroundColor White
Write-Host "2. Install Kiwoom Open API+ (if not installed)" -ForegroundColor White
Write-Host "3. Run: .\start.ps1 or .\start.bat" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - SETUP_ISOLATED_PYTHON.md (setup guide)" -ForegroundColor Gray
Write-Host "  - KIWOOM_API_SETUP.md (Kiwoom API guide)" -ForegroundColor Gray
Write-Host "  - GETTING_STARTED.md (complete guide)" -ForegroundColor Gray
Write-Host ""
Write-Host "Your system Python 64-bit is unaffected!" -ForegroundColor Green
Write-Host ""

if (-not $Automated) {
    Read-Host "Press Enter to exit"
}

