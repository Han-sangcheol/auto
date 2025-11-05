# 🔧 Python 32bit 설치 가이드

## 왜 32bit Python이 필요한가요?

**키움증권 Open API는 32bit Python만 지원합니다.**

- 키움 API는 32bit COM 컴포넌트로 개발되어 있습니다
- 64bit Python에서는 키움 API를 로드할 수 없습니다
- PyQt5의 QAxWidget을 통해 ActiveX를 로드하는데, 이 과정에서 bitness가 일치해야 합니다

## 📋 현재 Python 버전 확인

### Windows PowerShell에서 확인:

```powershell
python -c "import sys, platform; print(f'Python {platform.python_version()}: {platform.architecture()[0]}')"
```

**출력 예시:**
- ✅ `Python 3.11.9: 32bit` → OK
- ❌ `Python 3.13.9: 64bit` → 32bit 설치 필요

## 🚀 설치 방법

### 방법 1: 자동 설치 스크립트 (권장) ⭐

**가장 쉽고 빠른 방법입니다.**

1. **관리자 권한**으로 PowerShell 실행
   - Windows 검색 → "PowerShell" → 우클릭 → "관리자 권한으로 실행"

2. 프로젝트 폴더로 이동:
   ```powershell
   cd D:\cleonAI\auto_trading\scripts
   ```

3. 자동 설치 스크립트 실행:
   ```powershell
   .\install_python32.ps1
   ```

4. 설치가 완료되면:
   - Python 3.11.9 (32bit)가 `C:\Python32\`에 설치됩니다
   - 시스템 PATH에는 추가되지 않습니다 (기존 Python과 충돌 방지)

### 방법 2: 수동 설치

#### 단계 1: Python 32bit 다운로드

1. Python 공식 사이트 방문: https://www.python.org/downloads/
2. Python 3.11.9 또는 3.12.x 버전 선택
3. **Windows installer (32-bit)** 다운로드 (중요!)

**직접 링크:**
- [Python 3.11.9 (32-bit)](https://www.python.org/ftp/python/3.11.9/python-3.11.9.exe)

#### 단계 2: 설치 옵션

설치 시 다음 옵션을 선택하세요:

1. ✅ "Install Now" 또는 "Customize installation"
2. ⚠️ **"Add Python to PATH" 체크 해제** (기존 Python과 충돌 방지)
3. 설치 경로: `C:\Python32\` (권장)

#### 단계 3: 설치 확인

```powershell
C:\Python32\python.exe --version
C:\Python32\python.exe -c "import sys; print('32bit' if sys.maxsize <= 2**32 else '64bit')"
```

## 🔧 가상환경 생성

### 자동 생성 (권장)

```powershell
cd D:\cleonAI\auto_trading
scripts\setup.bat
```

또는 PowerShell:
```powershell
cd D:\cleonAI\auto_trading
scripts\setup.ps1
```

### 수동 생성

```powershell
# 프로젝트 루트로 이동
cd D:\cleonAI

# 32bit Python으로 가상환경 생성
C:\Python32\python.exe -m venv .venv32

# 가상환경 활성화
.\.venv32\Scripts\Activate.ps1

# 패키지 설치
cd auto_trading
pip install -r requirements.txt
```

## ▶️ 프로그램 실행

### 방법 1: 실행 스크립트 사용 (권장)

```powershell
cd D:\cleonAI\auto_trading
scripts\start.bat
```

또는:
```powershell
cd D:\cleonAI\auto_trading
scripts\start.ps1
```

### 방법 2: 직접 실행

```powershell
cd D:\cleonAI
.\.venv32\Scripts\Activate.ps1
cd auto_trading
python main.py
```

## 🔍 문제 해결

### 1. "64-bit Python detected!" 오류

**증상:**
```
❌ ERROR: 64-bit Python detected!
키움증권 Open API는 32-bit Python만 지원합니다.
```

**해결:**
- 32bit Python을 설치했는지 확인
- `.venv32` 가상환경을 사용하는지 확인
- `start.bat` 또는 `start.ps1` 스크립트로 실행

### 2. "QAxWidget object has no attribute 'OnEventConnect'"

**증상:**
```
QAxBase::setControl: requested control KHOPENAPI.KHOpenAPICtrl.1 could not be instantiated
```

**원인:**
- 64bit Python 사용 중
- 키움 Open API+ 미설치

**해결:**
1. Python 32bit 설치 (위 가이드 참고)
2. 키움 Open API+ 설치 (KIWOOM_API_SETUP.md 참고)

### 3. Virtual environment not found

**증상:**
```
[ERROR] 32-bit virtual environment not found!
```

**해결:**
```powershell
cd D:\cleonAI\auto_trading
scripts\setup.bat
```

### 4. Python이 C:\Python32에 없음

**해결 1 (권장):** 자동 설치 스크립트 사용
```powershell
cd auto_trading\scripts
.\install_python32.ps1
```

**해결 2:** 수동으로 Python 32bit를 `C:\Python32`에 설치

## 📁 프로젝트 구조

```
D:\cleonAI\
├── .venv32\                 # 32bit Python 가상환경 (auto_trading 전용)
├── .venv\                   # 64bit Python 가상환경 (backend, frontend)
│
├── auto_trading\            # 🔴 32bit Python 필수 (키움 API)
│   ├── main.py
│   ├── scripts\
│   │   ├── start.bat        # 32bit Python으로 실행
│   │   ├── setup.bat        # .venv32 생성
│   │   └── install_python32.ps1  # Python 32bit 자동 설치
│   └── ...
│
├── backend\                 # ✅ 64bit Python 사용 가능
├── frontend\                # ✅ 64bit Python 사용 가능
└── trading-engine\          # ✅ 64bit Python 사용 가능
```

## 💡 자주 묻는 질문 (FAQ)

### Q1: 64bit Python이 이미 설치되어 있는데, 32bit도 설치해도 되나요?

**A:** 네, 문제없습니다!
- 32bit Python을 `C:\Python32`에 설치하면 기존 64bit Python과 충돌하지 않습니다
- PATH에 추가하지 않으면 완전히 독립적으로 사용할 수 있습니다

### Q2: 왜 .venv가 아니라 .venv32를 사용하나요?

**A:** 프로젝트의 다른 부분(backend, frontend)은 64bit Python을 사용할 수 있기 때문입니다.
- `.venv32`: auto_trading 전용 (32bit)
- `.venv`: backend, frontend, trading-engine (64bit)

### Q3: 시스템 Python을 32bit로 바꿔야 하나요?

**A:** 아니요!
- 기존 64bit Python은 그대로 두고
- 32bit Python을 추가로 설치하여 사용하면 됩니다
- 가상환경을 통해 완전히 분리됩니다

### Q4: Mac이나 Linux에서는 어떻게 하나요?

**A:** 키움 API는 Windows 전용입니다.
- Mac/Linux에서는 Wine을 사용하거나
- Windows 가상머신을 사용해야 합니다
- 권장: Windows 10/11 사용

## 📚 관련 문서

- [키움 API 설치 가이드](KIWOOM_API_SETUP.md)
- [빠른 시작 가이드](../guides/QUICKSTART.md)
- [문제 해결](../troubleshooting/TROUBLESHOOTING.md)
- [전체 설치 가이드](GETTING_STARTED.md)

## ⚠️ 주의사항

1. **반드시 32bit Python 사용**: 64bit로는 키움 API가 작동하지 않습니다
2. **관리자 권한**: install_python32.ps1 실행 시 필요
3. **가상환경 사용**: 여러 Python 버전 충돌 방지
4. **정확한 경로**: 스크립트는 `.venv32`가 프로젝트 루트에 있다고 가정합니다

## 🎯 요약

1. **Python 32bit 설치**
   ```powershell
   cd auto_trading\scripts
   .\install_python32.ps1  # 관리자 권한
   ```

2. **가상환경 생성**
   ```powershell
   cd auto_trading
   scripts\setup.bat
   ```

3. **프로그램 실행**
   ```powershell
   scripts\start.bat
   ```

완료! 🎉

