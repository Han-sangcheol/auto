@echo off
chcp 65001 >nul
REM 자동매매 프로그램 실행 스크립트

echo ==========================================
echo    CleonAI 자동매매 프로그램 시작
echo ==========================================
echo.

REM 가상환경 활성화
if exist .venv\Scripts\activate.bat (
    echo 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
) else (
    echo 오류: 가상환경을 찾을 수 없습니다.
    echo 먼저 'python -m venv .venv' 명령으로 가상환경을 생성하세요.
    pause
    exit /b 1
)

REM Python 실행
echo 프로그램 실행 중...
echo.
python main.py

REM 종료
echo.
echo ==========================================
echo    프로그램이 종료되었습니다.
echo ==========================================
pause

