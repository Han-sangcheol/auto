# 🔧 Python 32bit/64bit 구분 업데이트 (2025-11-05)

## 📋 업데이트 요약

키움 API는 32bit Python만 지원하므로, 프로젝트를 명확하게 32bit/64bit로 구분했습니다.

### 주요 변경사항

1. **main.py에 Python 버전 체크 추가** ✅
   - 프로그램 시작 시 자동으로 32bit 확인
   - 64bit이면 명확한 에러 메시지와 해결 방법 표시
   - 위치: `auto_trading/main.py` 최상단

2. **실행 스크립트 수정** ✅
   - `start.bat`, `start.ps1` → `.venv32` 사용
   - 32bit Python 자동 체크 추가
   - 명확한 에러 메시지 제공

3. **설치 스크립트 수정** ✅
   - `setup.bat`, `setup.ps1` → `.venv32` 생성
   - C:\Python32 자동 감지
   - 32bit 확인 로직 추가

4. **문서 업데이트** ✅
   - `README.md`: 32bit 필수 경고 강조
   - 새 문서: `docs/installation/PYTHON_32BIT_SETUP.md`
   - 빠른 시작 섹션 개선
   - 문제 해결 가이드 추가

## 🚀 사용자 액션 필요

### 1단계: Python 32bit 설치

**관리자 권한** PowerShell에서:

```powershell
cd D:\cleonAI\auto_trading\scripts
.\install_python32.ps1
```

이 스크립트는:
- Python 3.11.9 (32bit) 다운로드
- `C:\Python32\`에 자동 설치
- PATH 변경 없음 (기존 Python과 충돌 방지)

### 2단계: 가상환경 재생성

```powershell
cd D:\cleonAI\auto_trading
scripts\setup.bat
```

또는:
```powershell
scripts\setup.ps1
```

이 스크립트는:
- 프로젝트 루트에 `.venv32` 생성
- Python 32bit로 가상환경 구성
- requirements.txt 패키지 자동 설치

### 3단계: 프로그램 실행

```powershell
cd D:\cleonAI\auto_trading
scripts\start.bat
```

또는:
```powershell
scripts\start.ps1
```

## 📁 프로젝트 구조

```
D:\cleonAI\
├── .venv32\                     # 🔴 32bit Python (auto_trading 전용)
│   └── Scripts\
│       └── python.exe           # 32bit Python 실행 파일
│
├── .venv\                       # ✅ 64bit Python (backend, frontend 등)
│   └── Scripts\
│       └── python.exe           # 64bit Python 실행 파일
│
├── auto_trading\                # 키움 API 자동매매 (32bit 필수)
│   ├── main.py                  # ← 32bit 체크 코드 추가됨
│   ├── scripts\
│   │   ├── start.bat            # ← .venv32 사용하도록 수정
│   │   ├── start.ps1            # ← .venv32 사용하도록 수정
│   │   ├── setup.bat            # ← .venv32 생성하도록 수정
│   │   ├── setup.ps1            # ← .venv32 생성하도록 수정
│   │   └── install_python32.ps1 # Python 32bit 자동 설치
│   └── docs\
│       └── installation\
│           └── PYTHON_32BIT_SETUP.md  # ← 새 문서
│
├── backend\                     # FastAPI (64bit 가능)
├── frontend\                    # PyQt GUI (64bit 가능)
└── trading-engine\              # 트레이딩 엔진 (64bit 가능)
```

## 🔍 변경된 파일 목록

### 코드 파일
1. `auto_trading/main.py`
   - `check_python_bitness()` 함수 추가
   - import 전에 32bit 체크 실행

### 스크립트 파일
2. `auto_trading/scripts/start.bat`
   - `.venv` → `..\.venv32`
   - 32bit Python 체크 로직 추가

3. `auto_trading/scripts/start.ps1`
   - `.venv` → `..\.venv32`
   - 32bit Python 확인 추가

4. `auto_trading/scripts/setup.bat`
   - C:\Python32 자동 감지
   - `.venv32` 생성 (루트에)
   - 32bit 확인 로직

5. `auto_trading/scripts/setup.ps1`
   - C:\Python32 자동 감지
   - `.venv32` 생성 (루트에)
   - 32bit 확인 로직

### 문서 파일
6. `auto_trading/README.md`
   - 시스템 요구사항 강조
   - 빠른 시작 체크리스트 추가
   - Python 환경 구분 섹션 추가
   - 문제 해결 가이드 추가

7. `auto_trading/docs/installation/PYTHON_32BIT_SETUP.md` (신규)
   - 완전한 32bit 설치 가이드
   - 자동/수동 설치 방법
   - 문제 해결 섹션
   - FAQ

8. `auto_trading/PYTHON_32BIT_UPDATE.md` (이 문서)
   - 변경 사항 요약
   - 사용자 액션 가이드

## ✅ 테스트 방법

### 1. Python 버전 확인

```powershell
# 64bit Python (기존)
python -c "import sys; print('64bit' if sys.maxsize > 2**32 else '32bit')"
# 출력: 64bit

# 32bit Python (새로 설치)
C:\Python32\python.exe -c "import sys; print('64bit' if sys.maxsize > 2**32 else '32bit')"
# 출력: 32bit
```

### 2. 가상환경 확인

```powershell
# .venv32 확인
D:\cleonAI\.venv32\Scripts\python.exe -c "import sys; print('64bit' if sys.maxsize > 2**32 else '32bit')"
# 출력: 32bit
```

### 3. 프로그램 실행 테스트

```powershell
cd D:\cleonAI\auto_trading
scripts\start.bat
```

**예상 동작:**
- 32bit Python이면 → 정상 실행
- 64bit Python이면 → 명확한 에러 메시지 표시

## 🔧 문제 해결

### 문제 1: "64-bit Python detected!"

**원인:** 64bit Python으로 실행 중

**해결:**
```powershell
# 1. Python 32bit 설치
cd auto_trading\scripts
.\install_python32.ps1

# 2. 가상환경 재생성
cd ..
scripts\setup.bat

# 3. 실행
scripts\start.bat
```

### 문제 2: ".venv32 not found"

**원인:** 가상환경이 생성되지 않음

**해결:**
```powershell
cd auto_trading
scripts\setup.bat
```

### 문제 3: "QAxWidget object has no attribute 'OnEventConnect'"

**원인:** 64bit Python 사용 또는 키움 API 미설치

**해결:**
1. Python 32bit 확인
2. 키움 Open API+ 설치 확인
3. 실행 스크립트 사용: `scripts\start.bat`

## 📚 참고 문서

- [Python 32bit 설치 가이드](docs/installation/PYTHON_32BIT_SETUP.md) ⭐
- [키움 API 설치](docs/installation/KIWOOM_API_SETUP.md)
- [빠른 시작](docs/guides/QUICKSTART.md)
- [문제 해결](docs/troubleshooting/TROUBLESHOOTING.md)

## 💡 핵심 포인트

1. ⚠️ **키움 API는 32bit Python만 지원**
2. ✅ **64bit/32bit Python 동시 설치 가능** (충돌 없음)
3. 🔴 **auto_trading은 항상 .venv32 사용**
4. ✅ **다른 모듈(backend, frontend)은 .venv(64bit) 사용 가능**
5. 📜 **실행 스크립트 사용 권장** (자동으로 올바른 Python 사용)

## 🎯 다음 단계

1. ✅ Python 32bit 설치 완료
2. ✅ 가상환경 재생성 완료
3. ⏭️ 프로그램 실행 테스트

실행 결과를 확인하고, 문제가 있으면 위 문제 해결 섹션을 참고하세요!

---

**업데이트 날짜**: 2025-11-05  
**작성자**: AI Assistant  
**버전**: 1.0

