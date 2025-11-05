@echo off
REM CleonAI Auto-Trading Setup Script (32-bit Python)

REM Change to auto_trading directory (parent of scripts folder)
cd /d "%~dp0\.."

echo ==========================================
echo    CleonAI Auto-Trading Setup
echo    (32-bit Python for Kiwoom API)
echo ==========================================
echo.

REM Determine Python 32-bit path
set PYTHON_32=

REM Check for C:\Python32 first (recommended)
if exist C:\Python32\python.exe (
    echo [Found] Python 32-bit at C:\Python32\
    set PYTHON_32=C:\Python32\python.exe
    goto :python_found
)

echo [!] Python 32-bit not found at C:\Python32\
echo.
echo Checking system Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No Python found!
    echo.
    echo Please install Python 32-bit:
    echo 1. Run: scripts\install_python32.ps1
    echo 2. Or download from: https://www.python.org/downloads/
    echo    (Select Windows installer 32-bit)
    echo.
    pause
    exit /b 1
)

REM Check if system Python is 32-bit
python -c "import sys; sys.exit(0 if sys.maxsize <= 2**32 else 1)" 2>nul
if errorlevel 1 (
    echo [ERROR] System Python is 64-bit!
    echo.
    echo Kiwoom API requires 32-bit Python.
    echo Please install Python 32-bit:
    echo   scripts\install_python32.ps1
    echo.
    pause
    exit /b 1
)
set PYTHON_32=python

:python_found
echo Python version check:
%PYTHON_32% --version
echo.

REM Create virtual environment in project root (.venv32)
REM Go to project root (parent of auto_trading)
cd ..
if not exist .venv32 (
    echo Creating 32-bit virtual environment (.venv32)...
    %PYTHON_32% -m venv .venv32
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        echo.
        echo Troubleshooting:
        echo 1. Check if Python 32-bit is properly installed
        echo 2. Try running as Administrator
        echo 3. Check disk space
        echo.
        cd auto_trading
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created!
) else (
    echo [OK] Virtual environment (.venv32) already exists.
)

REM Go back to auto_trading folder
cd auto_trading
echo.

REM Activate virtual environment
echo Activating 32-bit virtual environment...
call ..\.venv32\Scripts\activate.bat
if errorlevel 1 (
    echo [WARNING] Failed to activate virtual environment
    echo Continuing anyway...
)
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install packages
echo Installing required packages...
echo (This may take about 5 minutes)
pip install -r requirements.txt
echo.

REM Create logs directory
if not exist logs (
    echo Creating logs directory...
    mkdir logs
)

REM Check and create .env file
if not exist .env (
    echo.
    echo ==========================================
    echo    Creating .env file...
    echo ==========================================
    echo.
    if exist env.template (
        copy env.template .env >nul 2>&1
        echo [Success] .env file created.
        echo.
        echo ==========================================
        echo    IMPORTANT: Edit .env file!
        echo ==========================================
        echo.
        echo Next steps:
        echo 1. Open .env file with Notepad
        echo 2. Fill in required fields:
        echo    - KIWOOM_ACCOUNT_NUMBER (account number)
        echo    - KIWOOM_ACCOUNT_PASSWORD (4-digit password)
        echo    - WATCH_LIST (stocks to watch)
        echo.
        echo Example:
        echo KIWOOM_ACCOUNT_NUMBER=8123456789
        echo KIWOOM_ACCOUNT_PASSWORD=1234
        echo WATCH_LIST=005930,000660,035720
        echo.
    ) else (
        if exist .env.example (
            copy .env.example .env >nul 2>&1
            echo [Success] .env file created.
            echo Please edit .env file to complete setup.
        ) else (
            echo [Warning] env.template file not found.
            echo Please create .env file manually.
        )
    )
) else (
    echo [OK] .env file already exists.
    echo.
)

echo.
echo ==========================================
echo    Setup Complete!
echo ==========================================
echo.
echo Next Steps:
echo.
echo [Step 1] Configure .env file
echo    - Open auto_trading\.env with Notepad
echo    - Enter account number, password, and stock list
echo    - Save and close
echo.
echo [Step 2] Setup Kiwoom Open API (for first-time users)
echo    - See KIWOOM_API_SETUP.md
echo    - Install Open API+ program
echo    - Prepare digital certificate
echo.
echo [Step 3] Run the program
echo    - Run start.bat or start.ps1
echo    - Login with digital certificate
echo.
echo Detailed guide: GETTING_STARTED.md
echo Quick start: QUICKSTART.md
echo.
pause
