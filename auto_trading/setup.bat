@echo off
chcp 65001 >nul
REM 자동매매 프로그램 설치 스크립트

echo ==========================================
echo    CleonAI 자동매매 프로그램 설치
echo ==========================================
echo.

REM Python 버전 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo 오류: Python이 설치되지 않았습니다.
    echo Python 3.11 이상을 설치해주세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 버전 확인:
python --version
echo.

REM 가상환경 생성
if not exist .venv (
    echo 가상환경 생성 중...
    python -m venv .venv
    echo 가상환경 생성 완료!
) else (
    echo 가상환경이 이미 존재합니다.
)
echo.

REM 가상환경 활성화
echo 가상환경 활성화 중...
call .venv\Scripts\activate.bat

REM pip 업그레이드
echo pip 업그레이드 중...
python -m pip install --upgrade pip
echo.

REM 패키지 설치
echo 필요한 패키지 설치 중...
echo (약 5분 소요될 수 있습니다)
pip install -r requirements.txt
echo.

REM logs 디렉토리 생성
if not exist logs (
    echo 로그 디렉토리 생성 중...
    mkdir logs
)

REM .env 파일 확인
if not exist .env (
    echo.
    echo ==========================================
    echo    중요: .env 파일을 생성해주세요!
    echo ==========================================
    echo.
    echo 다음 단계:
    echo 1. .env.example 파일을 .env로 복사
    echo 2. .env 파일을 열어서 계좌 정보 입력
    echo    - KIWOOM_ACCOUNT_NUMBER
    echo    - KIWOOM_ACCOUNT_PASSWORD
    echo    - WATCH_LIST
    echo.
    if exist .env.example (
        copy .env.example .env >nul 2>&1
        echo .env 파일이 생성되었습니다.
        echo 이제 .env 파일을 편집하여 설정을 완료하세요.
    )
) else (
    echo .env 파일이 이미 존재합니다.
)

echo.
echo ==========================================
echo    설치가 완료되었습니다!
echo ==========================================
echo.
echo 다음 단계:
echo 1. .env 파일 설정 확인
echo 2. KIWOOM_API_SETUP.md 참고하여 키움 API 준비
echo 3. start.bat 실행
echo.
pause

