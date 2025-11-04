@echo off
REM CleonAI Auto-Trading Setup Script

echo ==========================================
echo    CleonAI Auto-Trading Setup
echo ==========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Please install Python 3.11 or higher.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python version check:
python --version
echo.

REM Create virtual environment
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created!
) else (
    echo Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

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
    ) else if exist .env.example (
        copy .env.example .env >nul 2>&1
        echo [Success] .env file created.
        echo Please edit .env file to complete setup.
    ) else (
        echo [Warning] env.template file not found.
        echo Please create .env file manually.
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
