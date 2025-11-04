# Automated Python 3.12 32-bit Installation Script
# Installs Python to C:\Python32\ without affecting system PATH

param(
    [string]$InstallPath = "C:\Python32",
    [string]$PythonVersion = "3.11.9",  # Python 3.11 for pandas 32-bit compatibility
    [switch]$Automated = $false
)

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Automated Python 32-bit Installer" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target Installation:" -ForegroundColor Yellow
Write-Host "  Version: Python $PythonVersion (32-bit)" -ForegroundColor White
Write-Host "  Location: $InstallPath" -ForegroundColor White
Write-Host "  PATH: Will NOT be modified" -ForegroundColor Green
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[Warning] Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Installation may fail. Recommend: Run as Administrator" -ForegroundColor Yellow
    if (-not $Automated) {
        $continue = Read-Host "Continue anyway? (yes/no)"
        if ($continue -ne "yes") {
            Write-Host "Installation cancelled." -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "Automated mode: Continuing without admin rights..." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Check if already installed
if (Test-Path "$InstallPath\python.exe") {
    Write-Host "[Check] Python already exists at $InstallPath" -ForegroundColor Yellow
    
    $existingVersion = & "$InstallPath\python.exe" --version 2>&1
    $existingBit = & "$InstallPath\python.exe" -c "import sys; print('32' if sys.maxsize <= 2**32 else '64')" 2>&1
    
    Write-Host "Existing version: $existingVersion" -ForegroundColor White
    Write-Host "Architecture: $existingBit-bit" -ForegroundColor White
    Write-Host ""
    
    if (-not $Automated) {
        $overwrite = Read-Host "Overwrite existing installation? (yes/no)"
        if ($overwrite -ne "yes") {
            Write-Host "Installation cancelled. Using existing Python." -ForegroundColor Green
            exit 0
        }
    } else {
        Write-Host "Automated mode: Using existing Python installation" -ForegroundColor Green
        exit 0
    }
    Write-Host ""
}

# Construct download URL
$baseUrl = "https://www.python.org/ftp/python"
$installerName = "python-$PythonVersion.exe"
$downloadUrl = "$baseUrl/$PythonVersion/$installerName"
$installerPath = "$env:TEMP\$installerName"

Write-Host "Step 1: Downloading Python $PythonVersion (32-bit)..." -ForegroundColor Yellow
Write-Host "URL: $downloadUrl" -ForegroundColor Gray
Write-Host "Downloading to: $installerPath" -ForegroundColor Gray
Write-Host ""

try {
    # Download with progress
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    $ProgressPreference = 'Continue'
    
    $fileSize = (Get-Item $installerPath).Length / 1MB
    Write-Host "[Done] Downloaded successfully! ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[Error] Failed to download Python installer" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually from:" -ForegroundColor Yellow
    Write-Host "https://www.python.org/downloads/release/python-$($PythonVersion.Replace('.', ''))/" -ForegroundColor Cyan
    Write-Host ""
    if (-not $Automated) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

# Verify installer
if (-not (Test-Path $installerPath)) {
    Write-Host "[Error] Installer file not found: $installerPath" -ForegroundColor Red
    exit 1
}

Write-Host "Step 2: Installing Python to $InstallPath..." -ForegroundColor Yellow
Write-Host "This may take 2-3 minutes. Please wait..." -ForegroundColor Gray
Write-Host ""

# Silent installation arguments
$installArgs = @(
    "/quiet",                      # Silent installation
    "InstallAllUsers=1",           # Install for all users
    "TargetDir=$InstallPath",      # Custom installation path
    "PrependPath=0",               # Do NOT add to PATH
    "Include_test=0",              # Skip tests
    "Include_doc=0",               # Skip documentation (faster)
    "Include_launcher=0",          # No py launcher (avoid conflicts)
    "AssociateFiles=0",            # Don't associate .py files
    "Shortcuts=0"                  # No shortcuts
)

try {
    # Start installation process
    $process = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host "[Done] Installation completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "[Error] Installation failed with exit code: $($process.ExitCode)" -ForegroundColor Red
        Write-Host "Common exit codes:" -ForegroundColor Yellow
        Write-Host "  1602: User cancelled" -ForegroundColor Gray
        Write-Host "  1603: Fatal error during installation" -ForegroundColor Gray
        Write-Host "  1618: Another installation in progress" -ForegroundColor Gray
        Write-Host ""
        if (-not $Automated) {
            Read-Host "Press Enter to exit"
        }
        exit 1
    }
} catch {
    Write-Host "[Error] Installation process failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Clean up installer
Write-Host "Step 3: Cleaning up..." -ForegroundColor Yellow
try {
    Remove-Item $installerPath -Force
    Write-Host "[Done] Temporary files removed" -ForegroundColor Green
} catch {
    Write-Host "[Warning] Could not remove installer file: $installerPath" -ForegroundColor Yellow
}

Write-Host ""

# Verify installation
Write-Host "Step 4: Verifying installation..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "$InstallPath\python.exe") {
    Write-Host "[OK] Python executable found" -ForegroundColor Green
    
    # Check version
    $installedVersion = & "$InstallPath\python.exe" --version 2>&1
    Write-Host "Installed version: $installedVersion" -ForegroundColor Cyan
    
    # Check architecture (32-bit or 64-bit)
    $bitCheck = & "$InstallPath\python.exe" -c "import sys; print('32-bit' if sys.maxsize <= 2**32 else '64-bit')" 2>&1
    
    if ($bitCheck -match "32-bit") {
        Write-Host "Architecture: 32-bit ✓" -ForegroundColor Green
    } else {
        Write-Host "Architecture: $bitCheck ✗" -ForegroundColor Red
        Write-Host "[Error] Expected 32-bit but got different architecture!" -ForegroundColor Red
        Write-Host "Please download 32-bit installer manually." -ForegroundColor Yellow
        exit 1
    }
    
    # Check pip
    if (Test-Path "$InstallPath\Scripts\pip.exe") {
        Write-Host "pip: Installed ✓" -ForegroundColor Green
    } else {
        Write-Host "pip: Not found ✗" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "[Success] Python 32-bit installed successfully!" -ForegroundColor Green
    
} else {
    Write-Host "[Error] Python executable not found at: $InstallPath\python.exe" -ForegroundColor Red
    Write-Host "Installation may have failed." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   Installation Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installation Details:" -ForegroundColor Cyan
Write-Host "  Python Path: $InstallPath\python.exe" -ForegroundColor White
Write-Host "  pip Path: $InstallPath\Scripts\pip.exe" -ForegroundColor White
Write-Host "  Added to PATH: No (isolated installation)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Run: .\setup_python32.ps1" -ForegroundColor White
Write-Host "   (Creates virtual environment with this Python)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Or manually create venv:" -ForegroundColor White
Write-Host "   $InstallPath\python.exe -m venv .venv" -ForegroundColor Gray
Write-Host ""
Write-Host "Your system Python is unaffected!" -ForegroundColor Green
Write-Host ""

if (-not $Automated) {
    Read-Host "Press Enter to exit"
}

