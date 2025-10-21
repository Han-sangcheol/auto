@echo off
chcp 65001 >nul
REM 자동매매 프로그램 실행 스크립트

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║          CleonAI 자동매매 프로그램 시작                  ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM 실행 전 체크리스트
echo [체크리스트]
echo.

REM .env 파일 확인
if not exist .env (
    echo [X] .env 파일이 없습니다!
    echo.
    echo 먼저 setup.bat을 실행하고 .env 파일을 설정하세요.
    echo.
    pause
    exit /b 1
) else (
    echo [OK] .env 파일 존재
)

REM 가상환경 확인
if exist .venv\Scripts\activate.bat (
    echo [OK] 가상환경 존재
) else (
    echo [X] 가상환경을 찾을 수 없습니다!
    echo.
    echo setup.bat을 먼저 실행하세요.
    echo.
    pause
    exit /b 1
)

REM logs 폴더 확인
if not exist logs (
    echo [!] logs 폴더 생성 중...
    mkdir logs
)
echo [OK] logs 폴더 존재

echo.
echo ==========================================
echo    프로그램 초기화 중...
echo ==========================================
echo.

REM 가상환경 활성화
call .venv\Scripts\activate.bat

REM Python 실행
echo [실행] Python 프로그램 시작...
echo.
echo ※ 공동인증서 창이 나타나면 인증서를 선택하고 비밀번호를 입력하세요.
echo ※ Ctrl+C를 눌러 언제든지 중지할 수 있습니다.
echo.
python main.py

REM 종료 처리
set EXIT_CODE=%ERRORLEVEL%
echo.
echo ==========================================
echo    프로그램 종료
echo ==========================================
echo.

if %EXIT_CODE% EQU 0 (
    echo [정상 종료] 프로그램이 정상적으로 종료되었습니다.
) else (
    echo [오류 발생] 프로그램이 오류와 함께 종료되었습니다.
    echo.
    echo 오류 해결:
    echo 1. logs\error.log 파일 확인
    echo 2. TROUBLESHOOTING.md 참고
    echo 3. 설정 파일(.env) 확인
    echo.
)

echo.
echo 로그 파일: logs\trading.log, logs\error.log
echo.
pause

