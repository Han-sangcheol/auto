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

REM .env 파일 확인 및 생성
if not exist .env (
    echo.
    echo ==========================================
    echo    .env 파일 생성 중...
    echo ==========================================
    echo.
    if exist env.template (
        copy env.template .env >nul 2>&1
        echo [성공] .env 파일이 생성되었습니다.
        echo.
        echo ==========================================
        echo    중요: .env 파일을 편집하세요!
        echo ==========================================
        echo.
        echo 다음 단계:
        echo 1. 메모장으로 .env 파일 열기
        echo 2. 필수 항목 입력:
        echo    - KIWOOM_ACCOUNT_NUMBER (계좌번호)
        echo    - KIWOOM_ACCOUNT_PASSWORD (비밀번호 4자리)
        echo    - WATCH_LIST (관심 종목)
        echo.
        echo 예시:
        echo KIWOOM_ACCOUNT_NUMBER=8123456789
        echo KIWOOM_ACCOUNT_PASSWORD=1234
        echo WATCH_LIST=005930,000660,035720
        echo.
    ) else if exist .env.example (
        copy .env.example .env >nul 2>&1
        echo [성공] .env 파일이 생성되었습니다.
        echo 이제 .env 파일을 편집하여 설정을 완료하세요.
    ) else (
        echo [경고] env.template 파일을 찾을 수 없습니다.
        echo 수동으로 .env 파일을 생성하세요.
    )
) else (
    echo [확인] .env 파일이 이미 존재합니다.
    echo.
)

echo.
echo ==========================================
echo    설치가 완료되었습니다!
echo ==========================================
echo.
echo 다음 단계:
echo.
echo [1단계] .env 파일 설정
echo    - auto_trading\.env 파일을 메모장으로 열기
echo    - 계좌번호, 비밀번호, 관심 종목 입력
echo    - 저장 후 닫기
echo.
echo [2단계] 키움 Open API 준비 (처음 사용하는 경우)
echo    - KIWOOM_API_SETUP.md 참고
echo    - Open API+ 프로그램 설치
echo    - 공동인증서 준비
echo.
echo [3단계] 프로그램 실행
echo    - start.bat 또는 start.ps1 실행
echo    - 공동인증서로 로그인
echo.
echo 자세한 가이드: GETTING_STARTED.md 참고
echo 빠른 시작: QUICKSTART.md 참고
echo.
pause

