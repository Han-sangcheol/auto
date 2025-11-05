# CleonAI Auto-Trading Start Script
# UTF-8 Encoding Support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Change to auto_trading directory (parent of scripts)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptPath "..")

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                          ║" -ForegroundColor Cyan
Write-Host "║       CleonAI Auto-Trading Program Start                ║" -ForegroundColor Cyan
Write-Host "║                                                          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Pre-flight Checklist
Write-Host "[Checklist]" -ForegroundColor Yellow
Write-Host ""

$hasError = $false

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "[X] .env file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run setup.ps1 first and configure .env file." -ForegroundColor Yellow
    Write-Host ""
    $hasError = $true
} else {
    Write-Host "[OK] .env file exists" -ForegroundColor Green
}

# Check virtual environment (32-bit)
if (Test-Path "..\.venv32\Scripts\Activate.ps1") {
    Write-Host "[OK] Virtual environment (.venv32) exists" -ForegroundColor Green
} else {
    Write-Host "[X] 32-bit virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run setup.ps1 first to create .venv32." -ForegroundColor Yellow
    Write-Host "Or install Python 32-bit: scripts\install_python32.ps1" -ForegroundColor Yellow
    Write-Host ""
    $hasError = $true
}

# Verify 32-bit Python
if (-not $hasError) {
    $pythonPath = "..\.venv32\Scripts\python.exe"
    if (Test-Path $pythonPath) {
        $is64bit = & $pythonPath -c "import sys; print(sys.maxsize > 2**32)" 2>$null
        if ($is64bit -eq "True") {
            Write-Host "[X] 64-bit Python detected!" -ForegroundColor Red
            Write-Host ""
            Write-Host "Kiwoom API requires 32-bit Python." -ForegroundColor Yellow
            Write-Host "Please install 32-bit Python: scripts\install_python32.ps1" -ForegroundColor Yellow
            Write-Host ""
            $hasError = $true
        } else {
            Write-Host "[OK] 32-bit Python confirmed" -ForegroundColor Green
        }
    }
}

# Check logs folder
if (-not (Test-Path "logs")) {
    Write-Host "[!] Creating logs folder..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "logs" | Out-Null
}
Write-Host "[OK] Logs folder exists" -ForegroundColor Green

# Exit if errors found
if ($hasError) {
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Initializing program..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment (32-bit)
Write-Host "Activating 32-bit virtual environment..." -ForegroundColor Yellow
$activateScript = "..\.venv32\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[Done] Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "[Warning] Virtual environment activation script not found." -ForegroundColor Yellow
}
Write-Host ""

# Run Python program (32-bit)
Write-Host "[Running] Starting Python program (32-bit)..." -ForegroundColor Green
Write-Host ""
Write-Host "** When the certificate window appears, select your certificate and enter password." -ForegroundColor Yellow
Write-Host "** Press Ctrl+C to stop the program at any time." -ForegroundColor Yellow
Write-Host ""

# Execute main.py with 32-bit Python
try {
    & "..\.venv32\Scripts\python.exe" main.py
    $exitCode = $LASTEXITCODE
} catch {
    $exitCode = 1
}

# Exit handling
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Program Terminated" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($exitCode -eq 0) {
    Write-Host "[Normal Exit] Program terminated normally." -ForegroundColor Green
} else {
    Write-Host "[Error] Program terminated with errors." -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check logs\error.log file" -ForegroundColor White
    Write-Host "2. See TROUBLESHOOTING.md" -ForegroundColor White
    Write-Host "3. Check .env configuration" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "Log files: logs\trading.log, logs\error.log" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"
