# CleonAI Auto-Trading Start Script
# UTF-8 Encoding Support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

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

# Check virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "[X] Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run setup.ps1 first." -ForegroundColor Yellow
    Write-Host ""
    $hasError = $true
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

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$activateScript = ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[Done] Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "[Warning] Virtual environment activation script not found." -ForegroundColor Yellow
}
Write-Host ""

# Run Python program
Write-Host "[Running] Starting Python program..." -ForegroundColor Green
Write-Host ""
Write-Host "** When the certificate window appears, select your certificate and enter password." -ForegroundColor Yellow
Write-Host "** Press Ctrl+C to stop the program at any time." -ForegroundColor Yellow
Write-Host ""

# Execute main.py
try {
    python main.py
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
