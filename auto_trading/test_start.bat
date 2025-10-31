@echo off
REM Test start script - minimal version

echo ==========================================
echo Testing CleonAI Start Script
echo ==========================================
echo.

REM Show current directory
echo Current Directory:
cd
echo.

REM Test Python
echo Testing Python:
.venv\Scripts\python.exe --version
echo.

REM Test PyQt5
echo Testing PyQt5:
.venv\Scripts\python.exe -c "import PyQt5; print('PyQt5 OK')"
echo.

REM Test simple script
echo Testing Python script execution:
.venv\Scripts\python.exe -c "print('Hello from Python!'); import sys; print('Args:', sys.argv)" test_arg
echo.

REM Test main.py exists
echo Checking main.py:
if exist main.py (
    echo [OK] main.py exists
) else (
    echo [ERROR] main.py NOT FOUND!
)
echo.

echo ==========================================
echo Test Complete
echo ==========================================
pause






