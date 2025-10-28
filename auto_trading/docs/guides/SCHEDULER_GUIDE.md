# 자동 시작/종료 스케줄러 사용 가이드

## 📅 개요

Windows 작업 스케줄러를 활용하여 CleonAI 자동매매 프로그램을 자동으로 시작하고 종료합니다.

### 🎯 주요 기능

1. **자동 시작**: 평일 08:30에 프로그램 자동 실행
2. **자동 종료**: 16:00에 프로그램 자동 종료
3. **공휴일 스킵**: 평일에만 실행 (주말 자동 제외)
4. **안전한 종료**: 모든 포지션 정리 후 종료

---

## 🚀 설치 방법

### 1단계: 관리자 권한으로 PowerShell 실행

```powershell
# Windows 검색 → "PowerShell" → 우클릭 → "관리자 권한으로 실행"
```

### 2단계: 스케줄러 설치 스크립트 실행

```powershell
cd D:\cleonAI\auto_trading
.\install_scheduler.ps1
```

### 3단계: 설정 확인

```
설정 정보:
  - 작업 이름: CleonAI_AutoTrading
  - 시작 시간: 평일 08:30
  - 종료 시간: 평일 16:00
  - 사용자: DESKTOP-XXX\User
```

### 4단계: 설치 승인

```
스케줄러를 설치하시겠습니까? (Y/N): Y
```

---

## ✅ 설치 확인

### 작업 스케줄러에서 확인

1. `Win + R` → `taskschd.msc` 입력
2. "작업 스케줄러 라이브러리" 선택
3. "CleonAI_AutoTrading" 작업 확인

### 작업 속성 확인

- **트리거**: 평일 08:30 (월~금)
- **동작**: Python.exe 실행 (`D:\cleonAI\.venv\Scripts\python.exe`)
- **인수**: `main.py`
- **작업 디렉터리**: `D:\cleonAI\auto_trading`

---

## ⚙️ 자동 종료 설정

### .env 파일 설정

```bash
# 자동 종료 활성화 (16:00에 자동 종료)
ENABLE_AUTO_SHUTDOWN=True
```

### 종료 시간

- **기본 설정**: 16:00 (오후 4시)
- **변경 방법**: `scheduler.py`의 `AUTO_STOP_TIME` 수정

```python
# scheduler.py
AUTO_STOP_TIME = dt_time(16, 0)  # 16:00
```

---

## 🔧 사용 방법

### 자동 실행 (스케줄러)

- **설치 후**: 평일 08:30에 자동으로 프로그램 시작
- **필요 조건**:
  - 컴퓨터가 켜져 있어야 함
  - Windows 로그인 상태
  - 키움 Open API 설치됨

### 수동 실행

```powershell
cd D:\cleonAI\auto_trading
.\.venv\Scripts\Activate.ps1
python main.py
```

### 자동 종료

- **ENABLE_AUTO_SHUTDOWN=True**: 16:00에 자동 종료
- **ENABLE_AUTO_SHUTDOWN=False**: 수동 종료 (24시간 운영)

---

## 🗑️ 제거 방법

### 1단계: 관리자 권한으로 PowerShell 실행

```powershell
cd D:\cleonAI\auto_trading
.\uninstall_scheduler.ps1
```

### 2단계: 제거 승인

```
이 작업을 제거하시겠습니까? (Y/N): Y
```

### 3단계: 제거 확인

```
✅ 스케줄러 제거 완료!
프로그램은 더 이상 자동으로 시작되지 않습니다.
```

---

## 📊 시장 시간 체크

### 프로그램 내장 기능

```python
from scheduler import TradingScheduler

# 현재 시장 상태 확인
status = TradingScheduler.get_market_status()
print(f"시장 상태: {status}")  # "개장 전", "거래 중", "마감 후", "주말 (휴장)"

# 거래 시간 여부
is_trading = TradingScheduler.is_market_hours()
print(f"거래 시간: {is_trading}")  # True/False
```

### 시장 시간 정보

| 구분       | 시간         | 비고               |
| ---------- | ------------ | ------------------ |
| 자동 시작  | 08:30        | 스케줄러           |
| 시장 개장  | 09:00        | 거래 시작          |
| 시장 마감  | 15:30        | 거래 종료          |
| 자동 종료  | 16:00        | ENABLE_AUTO_SHUTDOWN=True |

---

## ⚠️ 주의사항

### 필수 조건

1. **컴퓨터 전원**: 자동 시작 시간에 컴퓨터가 켜져 있어야 함
2. **Windows 로그인**: 로그인된 상태여야 함
3. **키움 API**: 키움 Open API가 설치되어 있어야 함
4. **.env 설정**: 계좌 정보가 올바르게 설정되어야 함

### 보안

- **관리자 권한**: 스케줄러 설치/제거 시 필요
- **자동 로그인**: 키움 API 로그인은 수동 (보안상 권장)
- **모의투자**: 실계좌 사용 전 충분한 테스트 필요

### 로그

- **설치 로그**: `logs/trading.log`
- **에러 로그**: `logs/error.log`
- **Windows 이벤트**: 작업 스케줄러 로그 확인 가능

---

## 🐛 문제 해결

### 작업이 실행되지 않음

**증상**: 08:30에 프로그램이 시작되지 않음

**해결**:
1. 작업 스케줄러에서 작업 상태 확인
2. "기록" 탭에서 실행 로그 확인
3. Python 경로가 올바른지 확인
4. 수동으로 실행해보기

### 자동 종료가 작동하지 않음

**증상**: 16:00에 프로그램이 종료되지 않음

**해결**:
1. `.env` 파일에서 `ENABLE_AUTO_SHUTDOWN=True` 확인
2. `scheduler.py`가 로드되는지 확인
3. 로그 파일에서 "스케줄러 활성화" 메시지 확인

### 권한 오류

**증상**: "관리자 권한이 필요합니다"

**해결**:
- PowerShell을 "관리자 권한으로 실행"

---

## 📝 고급 설정

### 스케줄 시간 변경

**install_scheduler.ps1 수정**:

```powershell
# 시작 시간 변경 (예: 08:00)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "08:00"
```

**scheduler.py 수정** (자동 종료 시간):

```python
AUTO_STOP_TIME = dt_time(17, 0)  # 17:00으로 변경
```

### 공휴일 제외

현재 버전은 평일(월~금)만 실행됩니다. 한국 공휴일을 추가로 제외하려면:

1. `scheduler.py`에 공휴일 목록 추가
2. `is_market_hours()` 메서드에 공휴일 체크 로직 추가

```python
# 예시 (구현 필요)
HOLIDAYS = [
    datetime(2025, 1, 1),   # 신정
    datetime(2025, 2, 10),  # 설날
    # ...
]

def is_holiday():
    return datetime.now().date() in [h.date() for h in HOLIDAYS]
```

---

## 📚 참고 자료

### Windows 작업 스케줄러

- **실행**: `Win + R` → `taskschd.msc`
- **공식 문서**: [Microsoft Docs - Task Scheduler](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)

### PowerShell 명령어

```powershell
# 모든 예약된 작업 확인
Get-ScheduledTask

# 특정 작업 확인
Get-ScheduledTask -TaskName "CleonAI_AutoTrading"

# 작업 수동 실행
Start-ScheduledTask -TaskName "CleonAI_AutoTrading"

# 작업 중지
Stop-ScheduledTask -TaskName "CleonAI_AutoTrading"

# 작업 비활성화
Disable-ScheduledTask -TaskName "CleonAI_AutoTrading"

# 작업 활성화
Enable-ScheduledTask -TaskName "CleonAI_AutoTrading"
```

---

## 🎯 베스트 프랙티스

### 1. 모의투자 테스트

```
[필수] 실계좌 사용 전 최소 1주일 이상 모의투자 테스트
```

### 2. 로그 모니터링

```powershell
# 실시간 로그 확인
Get-Content logs\trading.log -Wait -Tail 50
```

### 3. 알림 설정

```bash
# .env
ENABLE_NOTIFICATIONS=True
ENABLE_SOUND_ALERTS=True
```

### 4. 헬스 체크 활성화

```bash
# .env
ENABLE_HEALTH_MONITOR=True
ENABLE_AUTO_RECOVERY=True
```

### 5. 정기 점검

- **매일**: 로그 확인
- **매주**: 통계 분석
- **매월**: 설정 최적화

---

## 📞 지원

문제가 발생하면:

1. **로그 확인**: `logs/trading.log`, `logs/error.log`
2. **작업 스케줄러**: 실행 기록 확인
3. **이슈 리포트**: GitHub Issues에 상세 정보 제공

---

**⚠️  중요**: 투자 손실에 대한 책임은 사용자 본인에게 있습니다. 충분한 테스트 후 사용하세요.

