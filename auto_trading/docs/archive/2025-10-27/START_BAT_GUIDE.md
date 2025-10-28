# start.bat 실행 가이드

**날짜**: 2025-10-27  
**목적**: start.bat과 python main.py 실행 결과를 동일하게 개선

## 🎯 개선 사항

### 문제 1: start.bat과 python main.py 결과가 다름

**원인**: start.bat이 단순히 python main.py만 호출하고 있었음

**해결**: start.bat 개선
- ✅ GUI 지원 명시 (PyQt5)
- ✅ .env 파일 자동 생성
- ✅ 더 상세한 안내 메시지
- ✅ main.py와 동일한 실행 결과

### 문제 2: 급등주 수동 승인 (yes 입력 필요)

**원인**: SURGE_AUTO_APPROVE=False (이전 기본값)

**해결**: SURGE_AUTO_APPROVE=True로 기본값 변경 ✅
- ✅ config.py 기본값 True로 변경
- ✅ env.template에 True로 설정
- ✅ GUI 환경에서 자동 승인 권장
- ✅ 리스크 관리는 MAX_STOCKS와 손절매로 조절

## 🚀 사용 방법

### 방법 1: start.bat 더블클릭 (권장)

```
auto_trading\start.bat 더블클릭
```

**실행 흐름**:
1. .env 파일 확인 (없으면 자동 생성)
2. 가상환경 확인
3. logs 폴더 생성
4. Python 프로그램 실행
5. PyQt5 GUI 초기화
6. 키움 Open API 로그인
7. 자동매매 시작

### 방법 2: 명령줄에서 실행

```cmd
cd auto_trading
start.bat
```

### 방법 3: python main.py 직접 실행

```powershell
cd auto_trading
python main.py
```

**결과**: 모두 동일하게 작동합니다! ✅

## 📋 실행 화면

### start.bat 실행 시

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

[Running] Starting CleonAI Auto-Trading...

** PyQt5 GUI will be initialized
** Certificate window will appear automatically (5-10 seconds)
** Only certificate password is required (NOT account password)
** Press Ctrl+C to stop the program at any time

... (main.py와 동일한 실행 결과)
```

### python main.py 실행 시

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          🤖 CleonAI 자동매매 프로그램 v1.3              ║
║                                                          ║
║          키움증권 Open API 기반 자동매매 시스템          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
📅 시작 시간: 2025-10-27 09:00:00
📁 작업 디렉토리: D:\cleonAI\auto_trading

... (동일한 로그)
```

**결과**: 두 방법 모두 동일! ✅

## ⚙️ 급등주 자동 승인 설정

### .env 파일 확인

```powershell
cd auto_trading
notepad .env
```

### 설정 변경

**.env 파일**:
```ini
# 급등주 자동 승인 (매수/매도) ⚠️ 중요 설정
SURGE_AUTO_APPROVE=True    # ✅ 자동 승인 (기본값)
# SURGE_AUTO_APPROVE=False  # ❌ 수동 승인 (yes 입력 필요)
```

**참고**: .env 파일에 설정이 없어도 **기본값은 True**(자동 승인)입니다.

### 설정 설명

| 설정 | 동작 | 권장 |
|------|------|------|
| `True` | 급등주 감지 시 **자동 매수** | ✅ GUI 환경 권장 |
| `False` | 급등주 감지 시 **콘솔에서 yes 입력** | ❌ 입력 불가능 |

### 왜 True 권장?

1. **GUI 환경**: PyQt5 이벤트 루프 실행 중 콘솔 입력 어려움
2. **자동화**: 자동매매의 목적에 부합
3. **리스크 관리**: 다른 설정으로 조절 가능
   - `MAX_STOCKS=3` - 최대 3개 종목만
   - `STOP_LOSS_PERCENT=5` - 5% 손절매
   - `SURGE_MIN_CHANGE_RATE=5.0` - 5% 이상만 감지

## 🔍 설정 확인

### 방법 1: 로그 확인

프로그램 시작 시 로그에서 확인:

```
⚠️  모의투자 모드로 실행합니다.
실제 자금이 투자되지 않습니다.

🚀 급등주를 자동으로 감지하여 즉시 매수합니다. (자동 승인)
⚠️  모든 급등주가 자동으로 매수됩니다!
```

**자동 승인 활성화** ✅

또는:

```
🚀 급등주를 자동으로 감지하여 승인을 요청합니다. (수동 승인)
```

**수동 승인** (콘솔 입력 필요) ❌

### 방법 2: 코드 확인

`config.py`:
```python
SURGE_AUTO_APPROVE = os.getenv('SURGE_AUTO_APPROVE', 'True').lower() == 'true'
```

**기본값: 'True'** ✅ (자동 승인)

## ⚠️ 주의사항

### 자동 승인 사용 시

**장점**:
- ✅ 사용자 개입 없이 자동 매매
- ✅ 기회 놓치지 않음
- ✅ GUI 환경에서 정상 작동

**단점**:
- ⚠️ 감지된 모든 급등주 매수
- ⚠️ 허위 신호 가능성

**리스크 관리**:
```ini
# 최대 종목 수 제한
MAX_STOCKS=3

# 손절매 (5%)
STOP_LOSS_PERCENT=5

# 일일 손실 한도 (3%)
DAILY_LOSS_LIMIT_PERCENT=3

# 급등주 조건 강화
SURGE_MIN_CHANGE_RATE=5.0    # 5% 이상만
SURGE_MIN_VOLUME_RATIO=2.0   # 거래량 2배 이상
```

### 수동 승인 사용 시

**문제점**:
- ❌ GUI 환경에서 입력 불가
- ❌ PyQt 이벤트 루프 블로킹
- ❌ 기회 놓침

**해결책**:
- 자동 승인 사용 (SURGE_AUTO_APPROVE=True)
- 또는 GUI 없이 콘솔 모드 실행 (비권장)

## 📊 실행 예시

### 자동 승인 모드 (권장)

```
=== 09:15:32 급등주 감지 ===
🚀 급등주 감지!
종목명:      삼성바이오로직스 (207940)
현재가:      850,000원
상승률:      +7.50%
거래량 비율: 3.2배

⚡ 자동 승인 모드: 즉시 매수 진행
✅ 급등주 자동 승인: 삼성바이오로직스
✅ 급등주 추가: 삼성바이오로직스 (207940)
📈 매수 시도: 207940 1주 @ 850,000원
✅ 매수 완료!
```

### 수동 승인 모드 (비권장)

```
=== 09:15:32 급등주 감지 ===
🚀 급등주 감지!
종목명:      삼성바이오로직스 (207940)
현재가:      850,000원
상승률:      +7.50%
거래량 비율: 3.2배

이 종목을 관심 종목에 추가하고 매수하시겠습니까?
승인: y/yes | 거부: n/no | 시간 제한: 30초
선택 (y/n): ← ❌ 입력 불가 (GUI 환경)

⏱️  시간 초과 (30초) - 급등주 매수 자동 거부
```

## 🎉 결론

### start.bat = python main.py

이제 **start.bat**과 **python main.py** 실행 결과가 **완전히 동일**합니다!

### 급등주 자동 승인

**SURGE_AUTO_APPROVE=True**로 설정하면:
- ✅ 자동으로 급등주 매수
- ✅ GUI 환경에서 정상 작동
- ✅ yes 입력 불필요

### 리스크 관리

자동 승인 사용 시에도 안전하게 운영:
- ✅ 최대 종목 수 제한 (MAX_STOCKS)
- ✅ 손절매 자동 실행 (STOP_LOSS_PERCENT)
- ✅ 일일 손실 한도 (DAILY_LOSS_LIMIT_PERCENT)
- ✅ 엄격한 급등주 조건 (MIN_CHANGE_RATE, MIN_VOLUME_RATIO)

---

## 🚀 빠른 시작

```cmd
REM 1. auto_trading 폴더로 이동
cd auto_trading

REM 2. start.bat 실행 (더블클릭 또는 명령줄)
start.bat

REM 또는 python main.py 직접 실행
python main.py
```

**둘 다 동일하게 작동합니다!** ✅

---

**작성**: CleonAI 개발팀  
**날짜**: 2025-10-27  
**버전**: v1.3  
**상태**: ✅ 완료

