@echo off
REM ============================================================
REM CleonAI Auto-Trading Diagnostic Script
REM ============================================================

echo.
echo ============================================================
echo   CleonAI Diagnostic Tool
echo ============================================================
echo.

REM Change to script directory
cd /d "%~dp0"

echo [Diagnostic Information]
echo.

REM 1. Current Directory
echo 1. Current Directory:
echo    %CD%
echo.

REM 2. .env file
echo 2. .env File:
if exist .env (
    echo    [OK] EXISTS
) else (
    echo    [ERROR] NOT FOUND
)
echo.

REM 3. Virtual Environment
echo 3. Virtual Environment:
if exist .venv\Scripts\python.exe (
    echo    [OK] EXISTS
    echo    Path: %CD%\.venv\Scripts\python.exe
) else (
    echo    [ERROR] NOT FOUND
)
echo.

REM 4. Python Version
echo 4. Python Version:
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe --version
    .venv\Scripts\python.exe -c "import sys; print('   Platform:', sys.platform); print('   Architecture:', '32-bit' if sys.maxsize <= 2**32 else '64-bit')"
) else (
    echo    [ERROR] Cannot check - Python not found
)
echo.

REM 5. PyQt5
echo 5. PyQt5:
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -c "import PyQt5; print('   [OK] Version:', PyQt5.QtCore.QT_VERSION_STR)" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo    [ERROR] NOT INSTALLED
    )
) else (
    echo    [ERROR] Cannot check - Python not found
)
echo.

REM 6. Kiwoom API Test
echo 6. Kiwoom OpenAPI Test:
if exist .venv\Scripts\python.exe (
    echo    Testing ActiveX control... (this may take 5-10 seconds)
    .venv\Scripts\python.exe -c "from PyQt5.QAxContainer import QAxWidget; print('   [OK] QAxWidget available')" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo    [ERROR] QAxWidget not available
    )
) else (
    echo    [ERROR] Cannot check - Python not found
)
echo.

REM 7. Required files
echo 7. Required Files:
if exist main.py (echo    [OK] main.py) else (echo    [ERROR] main.py NOT FOUND)
if exist config.py (echo    [OK] config.py) else (echo    [ERROR] config.py NOT FOUND)
if exist kiwoom_api.py (echo    [OK] kiwoom_api.py) else (echo    [ERROR] kiwoom_api.py NOT FOUND)
if exist trading_engine.py (echo    [OK] trading_engine.py) else (echo    [ERROR] trading_engine.py NOT FOUND)
if exist monitor_gui.py (echo    [OK] monitor_gui.py) else (echo    [ERROR] monitor_gui.py NOT FOUND)
echo.

REM 8. Logs folder
echo 8. Logs Folder:
if exist logs (
    echo    [OK] EXISTS
    dir /b logs\*.log 2>nul | find /c /v "" > temp_count.txt
    set /p LOG_COUNT=<temp_count.txt
    del temp_count.txt
    echo    Log files: !LOG_COUNT!
) else (
    echo    [!] NOT FOUND - will be created automatically
)
echo.

echo ============================================================
echo   Diagnostic Complete
echo ============================================================
echo.
echo If all checks show [OK], you can run: start.bat
echo.
echo If any checks show [ERROR]:
echo   - Missing .env: Copy env.template to .env
echo   - Missing .venv: Run setup.bat
echo   - Missing PyQt5: Activate .venv and run: pip install PyQt5
echo   - 64-bit Python: Reinstall with 32-bit Python
echo   - Missing OpenAPI: Install from https://www.kiwoom.com
echo.
pause



