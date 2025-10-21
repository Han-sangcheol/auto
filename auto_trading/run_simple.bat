@echo off
chcp 65001 >nul

echo ==========================================
echo   간단 실행 스크립트
echo ==========================================
echo.

REM 가상환경 활성화
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] 가상환경 활성화 완료
) else (
    echo [오류] 가상환경을 찾을 수 없습니다.
    echo 먼저 'python -m venv venv' 명령으로 가상환경을 생성하세요.
    pause
    exit /b 1
)

echo.
echo Python 버전:
python --version
echo.

echo 설치된 패키지:
pip list
echo.

echo ==========================================
echo   설정 완료! 이제 다음 명령으로 실행하세요:
echo   python main.py
echo ==========================================
echo.

cmd /k


