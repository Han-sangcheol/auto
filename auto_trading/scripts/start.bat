@echo off
REM ============================================================
REM CleonAI Auto-Trading Start Script
REM ============================================================

echo.
echo ============================================================
echo   CleonAI Auto-Trading Program v1.3
echo ============================================================
echo.

REM Change to auto_trading directory (parent of scripts)
cd /d "%~dp0\.."

REM ============================================================
REM Step 1: Check .env file
REM ============================================================
echo [1/6] Checking .env file...
if not exist .env (
    echo [!] .env file not found - creating from template...
    if exist env.template (
        copy env.template .env >nul
        echo [OK] Created .env from template
        echo [!] Please edit .env file with your settings!
        echo.
        pause
        exit /b 0
    ) else (
        echo [ERROR] env.template not found!
        pause
        exit /b 1
    )
) else (
    echo [OK] .env file exists
)

REM ============================================================
REM Step 2: Check virtual environment (32-bit)
REM ============================================================
echo [2/6] Checking virtual environment...
if not exist ..\.venv32\Scripts\python.exe (
    echo [ERROR] 32-bit virtual environment not found!
    echo.
    echo Please run setup.bat first to create .venv32:
    echo   scripts\setup.bat
    echo.
    echo Or install Python 32-bit:
    echo   scripts\install_python32.ps1
    echo.
    pause
    exit /b 1
)
echo [OK] Virtual environment exists

REM ============================================================
REM Step 3: Test Python (32-bit check)
REM ============================================================
echo [3/6] Testing Python...
..\.venv32\Scripts\python.exe --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python test failed!
    pause
    exit /b 1
)
echo [OK] Python works

REM ============================================================
REM Step 4: Verify 32-bit Python
REM ============================================================
echo [4/6] Verifying 32-bit Python...
..\.venv32\Scripts\python.exe -c "import sys; sys.exit(0 if sys.maxsize <= 2**32 else 1)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 64-bit Python detected!
    echo.
    echo Kiwoom API requires 32-bit Python.
    echo Please install 32-bit Python:
    echo   scripts\install_python32.ps1
    echo.
    pause
    exit /b 1
)
echo [OK] 32-bit Python confirmed

REM ============================================================
REM Step 5: Check PyQt5
REM ============================================================
echo [5/6] Checking PyQt5...
..\.venv32\Scripts\python.exe -c "import PyQt5" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyQt5 not installed!
    echo.
    echo Installing PyQt5...
    ..\.venv32\Scripts\pip.exe install PyQt5
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install PyQt5!
        pause
        exit /b 1
    )
)
echo [OK] PyQt5 installed

REM ============================================================
REM Step 6: Create logs folder
REM ============================================================
echo [6/6] Checking logs folder...
if not exist logs (
    mkdir logs
)
echo [OK] Logs folder ready

echo.
echo ============================================================
echo   Starting Program...
echo ============================================================
echo.
echo ** Certificate window will appear in 5-10 seconds
echo ** Enter your certificate password only
echo ** Monitoring GUI will open automatically
echo ** Press Ctrl+C to stop
echo.

REM ============================================================
REM Run the program (32-bit Python)
REM ============================================================
..\.venv32\Scripts\python.exe main.py

REM ============================================================
REM Exit handling
REM ============================================================
set EXIT_CODE=%ERRORLEVEL%
echo.
echo ============================================================
if %EXIT_CODE% EQU 0 (
    echo   Program exited normally
) else (
    echo   Program exited with error code: %EXIT_CODE%
    echo.
    echo Check logs:
    echo   - logs\trading_2025-10-27.log
    echo   - logs\error_2025-10-27.log
)
echo ============================================================
echo.
pause
