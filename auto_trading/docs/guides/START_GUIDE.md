# start.bat 사용 가이드

## 🎯 목적

`start.bat`는 프로그램을 쉽게 실행하기 위한 원클릭 실행 스크립트입니다.

## ✅ 정상 실행 시 화면

```
============================================================
  CleonAI Auto-Trading Program v1.3
============================================================

[1/5] Checking .env file...
[OK] .env file exists

[2/5] Checking virtual environment...
[OK] Virtual environment exists

[3/5] Testing Python...
Python 3.11.9 (32 bit)
[OK] Python works

[4/5] Checking PyQt5...
[OK] PyQt5 installed

[5/5] Checking logs folder...
[OK] Logs folder ready

============================================================
  Starting Program...
============================================================

** Certificate window will appear in 5-10 seconds
** Enter your certificate password only
** Monitoring GUI will open automatically
** Press Ctrl+C to stop

[INFO] Creating PyQt Application...
[OK] PyQt Application created successfully
[INFO] Initializing Kiwoom OpenAPI...
       - Loading ActiveX Control: KHOPENAPI.KHOpenAPICtrl.1
       - This may take 5-10 seconds...
[OK] Kiwoom OpenAPI initialized successfully

🔐 키움증권 Open API 로그인
📌 공동인증서 창이 자동으로 표시됩니다
```

→ **이 시점에 공동인증서 로그인 창이 자동으로 나타남!**

## ❌ 문제 발생 시

### 1단계: 진단 실행

```cmd
diagnose.bat
```

이 스크립트가 모든 설정을 자동으로 검사합니다.

### 2단계: 문제별 해결 방법

#### 🔴 [ERROR] .env file not found
```cmd
# 해결: 템플릿에서 생성
copy env.template .env
notepad .env  # 계좌번호, 비밀번호 입력
```

#### 🔴 [ERROR] Virtual environment not found
```cmd
# 해결: 가상환경 생성
setup.bat
```

#### 🔴 [ERROR] Python test failed
```cmd
# 해결: 가상환경 재생성
rmdir /s /q .venv
setup.bat
```

#### 🔴 [ERROR] PyQt5 not installed
```cmd
# 해결: PyQt5 설치
.venv\Scripts\activate.bat
pip install PyQt5
```

#### 🔴 [ERROR] 64-bit Python (32-bit required)
```cmd
# 해결: 32비트 Python 설치
# 1. https://www.python.org/downloads/release/python-3119/
# 2. "Windows installer (32-bit)" 다운로드
# 3. 설치 후 setup.bat 재실행
```

#### 🔴 OpenAPI 초기화 실패
```cmd
# 원인 1: Open API+ 미설치
#   → https://www.kiwoom.com/h/customer/download/VOpenApiInfoView
#   → "영웅문 Open API+" 다운로드 및 설치

# 원인 2: ActiveX 등록 문제
#   → 관리자 권한 CMD에서:
#     regsvr32 "C:\OpenAPI\OpenAPI.dll"
```

## 🔍 로그가 생성되지 않는 경우

### 원인
프로그램이 **Python 초기화 단계에서 실패**하고 있음

### 진단 방법
```cmd
# 1. 진단 스크립트 실행
diagnose.bat

# 2. 수동 테스트
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -c "import PyQt5; print('OK')"
.venv\Scripts\python.exe -c "from PyQt5.QAxContainer import QAxWidget; print('OK')"
```

### 해결 단계
1. **diagnose.bat 실행** → 모든 [OK] 확인
2. **start.bat 실행** → 어느 단계에서 멈추는지 확인
3. **해당 단계의 에러 메시지** 확인
4. **위의 문제별 해결 방법** 적용

## 📊 start.bat vs main.py 직접 실행

| 구분 | start.bat | python main.py |
|------|-----------|----------------|
| 환경 체크 | 자동 | 없음 |
| 가상환경 활성화 | 자동 | 수동 필요 |
| 에러 처리 | 상세 | 최소 |
| 권장 대상 | 일반 사용자 | 개발자 |

**결과는 동일해야 합니다!**

## 🆘 여전히 안 되면

### 완전 초기화 방법
```cmd
# 1. 가상환경 삭제
rmdir /s /q .venv

# 2. 로그 백업 (선택)
move logs logs_backup

# 3. 재설정
setup.bat

# 4. 테스트
diagnose.bat

# 5. 실행
start.bat
```

### 정보 수집 (지원 요청 시)
```cmd
# 시스템 정보
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
python --version
where python

# 진단 결과
diagnose.bat > diagnostic_report.txt

# 최근 로그 (있는 경우)
type logs\error.log
```

→ 이 정보를 함께 공유하면 빠른 지원 가능

## 💡 팁

### 빠른 재시작
```cmd
# Ctrl+C로 중지 후
start.bat  # 다시 실행
```

### 로그 실시간 보기 (별도 창)
```cmd
# PowerShell 창에서
Get-Content logs\trading.log -Wait -Tail 20
```

### 여러 계좌 사용
```cmd
# .env 파일 복사하여 관리
copy .env .env.account1
copy .env .env.account2

# 사용 시:
copy .env.account1 .env
start.bat
```

## 📞 추가 지원

- **키움증권 고객센터**: 1544-9000
- **Open API 매뉴얼**: KOA Studio 설치 후 확인
- **Python 공식 사이트**: https://www.python.org

---

## ✅ 체크리스트

실행 전 확인:
- [ ] .env 파일 생성 및 설정 완료
- [ ] 가상환경(.venv) 존재
- [ ] 32비트 Python 사용
- [ ] PyQt5 설치됨
- [ ] 키움 Open API+ 설치됨
- [ ] 공동인증서 등록됨
- [ ] 모의투자/실계좌 설정 확인

모두 체크되면:
```cmd
start.bat
```

실행! 🚀



