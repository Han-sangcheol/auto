@echo off
REM CleonAI Auto-Trading Start Script

echo.
echo ==========================================================
echo.
echo          CleonAI Auto-Trading Program Start
echo.
echo ==========================================================
echo.

REM Pre-flight checklist
echo [Checklist]
echo.

REM Check .env file
if not exist .env (
    echo [X] .env file not found!
    echo.
    echo Please run setup.bat or setup.ps1 first and configure .env file.
    echo.
    pause
    exit /b 1
) else (
    echo [OK] .env file exists
)

REM Check virtual environment
if exist .venv\Scripts\activate.bat (
    echo [OK] Virtual environment exists
) else (
    echo [X] Virtual environment not found!
    echo.
    echo Please run setup.bat or setup.ps1 first.
    echo.
    pause
    exit /b 1
)

REM Check logs folder
if not exist logs (
    echo [!] Creating logs folder...
    mkdir logs
)
echo [OK] Logs folder exists

echo.
echo ==========================================
echo    Initializing program...
echo ==========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run Python program
echo [Running] Starting Python program...
echo.
echo ** When certificate window appears, select your certificate and enter password.
echo ** Press Ctrl+C to stop the program at any time.
echo.
python main.py

REM Exit handling
set EXIT_CODE=%ERRORLEVEL%
echo.
echo ==========================================
echo    Program Terminated
echo ==========================================
echo.

if %EXIT_CODE% EQU 0 (
    echo [Normal Exit] Program terminated normally.
) else (
    echo [Error] Program terminated with errors.
    echo.
    echo Troubleshooting:
    echo 1. Check logs\error.log file
    echo 2. See TROUBLESHOOTING.md
    echo 3. Check .env configuration
    echo.
)

echo.
echo Log files: logs\trading.log, logs\error.log
echo.
pause
