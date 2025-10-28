# start.bat 실행 문제 해결 가이드

## 🔍 문제 진단

### 1단계: start.bat를 실행했을 때 표시되는 메시지 확인

```cmd
.\start.bat
```

#### Case 1: "[OK] PyQt Application created successfully" 까지 표시
✅ PyQt는 정상 작동
❌ 키움 OpenAPI 초기화 실패

**해결 방법:**
1. 키움 Open API+ 설치 확인
   - 제어판 > 프로그램 제거 > "영웅문 Open API+"
   - 없으면 설치: https://www.kiwoom.com/h/customer/download/VOpenApiInfoView

2. 32비트 Python 확인
   ```cmd
   python --version
   ```
   → "32 bit" 표시되어야 함
   → "64 bit"이면 32비트 Python 재설치 필요

3. ActiveX 재등록 (관리자 권한)
   ```cmd
   regsvr32 "C:\OpenAPI\OpenAPI.dll"
   ```

#### Case 2: "[ERROR] PyQt5 not installed!"
❌ PyQt5 설치 안됨

**해결 방법:**
```cmd
.venv\Scripts\activate.bat
pip install PyQt5
```

#### Case 3: 아무것도 표시 안됨
❌ 가상환경 활성화 실패

**해결 방법:**
```cmd
setup.bat  # 가상환경 재생성
```

---

## 📊 main.py vs start.bat 차이

### main.py 직접 실행
```cmd
cd auto_trading
.venv\Scripts\activate.bat
python main.py
```
- **장점**: 명시적인 가상환경 활성화
- **사용**: 개발/디버깅 시

### start.bat 실행
```cmd
.\start.bat
```
- **장점**: 자동 체크리스트 (환경 검증)
- **사용**: 일반 사용자 실행

**결과는 동일해야 합니다!**

---

## 🔧 단계별 디버깅

### Step 1: Python 환경 확인
```cmd
cd auto_trading
.venv\Scripts\python.exe --version
```
→ Python 3.11.x (32 bit) 표시되어야 함

### Step 2: PyQt5 확인
```cmd
.venv\Scripts\python.exe -c "import PyQt5; print(PyQt5.__version__)"
```
→ 버전 번호 표시되어야 함

### Step 3: 키움 API 확인
```cmd
.venv\Scripts\python.exe -c "from PyQt5.QAxContainer import QAxWidget; print('OK')"
```
→ "OK" 표시되어야 함

### Step 4: ActiveX 로드 확인
```cmd
.venv\Scripts\python.exe -c "from PyQt5.QtWidgets import QApplication; from PyQt5.QAxContainer import QAxWidget; import sys; app=QApplication(sys.argv); ocx=QAxWidget('KHOPENAPI.KHOpenAPICtrl.1'); print('OK')"
```
→ "OK" 표시되어야 함 (5-10초 소요)

---

## ⚡ 빠른 해결 방법

### 방법 1: 가상환경 재생성
```cmd
rmdir /s /q .venv
setup.bat
```

### 방법 2: 32비트 Python 확인 및 재설치
```cmd
# 현재 Python 확인
where python
python --version

# 64비트면 32비트로 교체
# https://www.python.org/downloads/release/python-3119/
# → "Windows installer (32-bit)" 다운로드
```

### 방법 3: 키움 OpenAPI 재설치
1. 기존 OpenAPI 제거
2. PC 재부팅
3. 관리자 권한으로 새로 설치
4. PC 재부팅

---

## 📝 로그 확인

### 상세 로그 보기
```cmd
type logs\trading.log
type logs\error.log
```

### 최근 에러만 보기
```cmd
powershell "Get-Content logs\error.log -Tail 20"
```

---

## 🆘 그래도 안 되면

### 1. 정보 수집
```cmd
echo Python Version:
python --version

echo.
echo Python Location:
where python

echo.
echo PyQt5 Test:
python -c "import PyQt5; print('OK')"

echo.
echo Virtual Env:
dir .venv\Scripts\python.exe
```

결과를 복사하여 문의

### 2. main.py로 직접 실행 테스트
```cmd
.venv\Scripts\activate.bat
python main.py
```

차이점을 확인

### 3. 로그 파일 확인
- `logs\trading_2025-10-27.log` (가장 최신)
- `logs\error_2025-10-27.log`

마지막 에러 메시지 확인

---

## ✅ 정상 작동 시 출력

```
==========================================================
          CleonAI Auto-Trading Program v1.3
          (GUI Support - PyQt5)
==========================================================

[Checklist]
[OK] .env file exists
[OK] Virtual environment exists
[OK] Logs folder exists

==========================================
    Initializing program...
==========================================

[Activating] Virtual environment...

[Check] Python environment:
D:\cleonAI\auto_trading\.venv\Scripts\python.exe
Python 3.11.9 (32 bit)

[Check] PyQt5 installation:
[OK] PyQt5 is installed

==========================================
[Running] Starting CleonAI Auto-Trading...
==========================================

** PyQt5 GUI will be initialized
** Monitoring window will appear
** Certificate window will appear automatically (5-10 seconds)
** Only certificate password is required (NOT account password)
** Press Ctrl+C to stop the program at any time

[INFO] Creating PyQt Application...
[OK] PyQt Application created successfully
[INFO] Initializing Kiwoom OpenAPI...
       - Loading ActiveX Control: KHOPENAPI.KHOpenAPICtrl.1
       - This may take 5-10 seconds...
[OK] Kiwoom OpenAPI initialized successfully

🔐 키움증권 Open API 로그인
📌 공동인증서 창이 자동으로 표시됩니다
📌 인증서를 선택하고 비밀번호를 입력하세요
```

이 시점에 **공동인증서 로그인 창**이 자동으로 표시됩니다!

---

## 📞 추가 지원

- 키움증권 HTS 고객센터: 1544-9000
- Open API 매뉴얼: KOA Studio 참고
- Python 설치: https://www.python.org/downloads/



