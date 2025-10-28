# Phase 4-A: 에러 자동 복구 & 헬스 모니터 완료

작성일: 2025-10-27

## 📋 완료 내용

### 1. 헬스 모니터 시스템

#### 1.1 health_monitor.py 생성
**기능**:
- ✅ API 연결 상태 주기적 체크
- ✅ 메모리/CPU 사용률 모니터링
- ✅ 활성 스레드 수 추적
- ✅ 프로그램 응답 상태 확인
- ✅ 이상 감지 시 자동 복구 시도
- ✅ 헬스 체크 이력 저장 (최대 1000개)

**체크 항목**:
| 항목 | 임계값 | 조치 |
|------|--------|------|
| API 연결 | 끊김 감지 | 자동 재연결 |
| 메모리 사용률 | 80% 이상 | 경고 로그 |
| CPU 사용률 | 90% 이상 | 경고 로그 |
| 스레드 수 | 20개 이상 | 경고 로그 |
| 연속 에러 | 5회 이상 | 모니터링 중지 |

**코드 예시**:
```python
# 헬스 체크 결과
{
    'timestamp': datetime.now(),
    'is_healthy': True,
    'api_connected': True,
    'engine_running': True,
    'memory_percent': 45.2,
    'cpu_percent': 15.8,
    'thread_count': 8,
    'issues': [],  # 심각한 문제
    'warnings': []  # 경고 사항
}
```

#### 1.2 자동 복구 로직
**복구 시나리오**:
1. **API 연결 끊김**:
   ```python
   감지 → 재연결 시도 → 성공 시 에러 카운트 리셋
   ```

2. **연속 에러 발생**:
   ```python
   5회 연속 실패 → 모니터링 중지 → 수동 개입 필요 로그
   ```

3. **복구 시도 제한**:
   ```python
   최대 3회까지만 자동 복구 시도
   → 초과 시 수동 개입 알림
   ```

**복구 통계**:
- 복구 시도 횟수 추적
- 복구 성공/실패 기록
- 건강률 계산 (최근 10회 체크 기준)

### 2. Kiwoom API 재연결 기능

#### 2.1 kiwoom_api.py 개선
**추가된 메서드**:

1. **`reconnect()`**: API 재연결
   ```python
   def reconnect(self) -> bool:
       """
       기존 연결 해제 → 재로그인 시도
       Returns: 재연결 성공 여부
       """
   ```

2. **`get_connection_status()`**: 연결 상태 조회
   ```python
   def get_connection_status(self) -> Dict:
       """
       Returns: {
           'is_connected': bool,
           'connect_state': int,
           'account_number': str,
           'has_account': bool
       }
       """
   ```

**동작 방식**:
```python
# 연결 끊김 감지
if not kiwoom.is_connected:
    # 기존 연결 종료
    kiwoom.ocx.dynamicCall("CommTerminate()")
    
    # 1초 대기
    time.sleep(1)
    
    # 재로그인
    success = kiwoom.login()
```

### 3. Trading Engine 통합

#### 3.1 헬스 모니터 통합
**초기화** (`initialize()`):
```python
# 헬스 모니터 생성
self.health_monitor = HealthMonitor(
    trading_engine=self,
    kiwoom_api=self.kiwoom,
    check_interval=60,  # 1분
    enable_auto_recovery=True
)
```

**시작** (`start_trading()`):
```python
# 헬스 모니터링 시작
if self.health_monitor:
    self.health_monitor.start()
```

**중지** (`stop_trading()`):
```python
# 헬스 모니터링 중지
if self.health_monitor:
    self.health_monitor.stop()
    # 최종 헬스 요약 출력
    self.health_monitor.print_health_summary()
```

#### 3.2 에러 복구 카운트 개선
**추가 변수**:
```python
self.error_count = 0
self.max_errors = 5
self.last_error_time = None
```

**향후 확장 준비**:
- 에러 발생 시간 추적
- 특정 시간 내 에러 빈도 계산
- 에러 패턴 분석

### 4. 설정 시스템 확장

#### 4.1 config.py 업데이트
```python
# 헬스 모니터 설정
ENABLE_HEALTH_MONITOR = True
HEALTH_CHECK_INTERVAL = 60  # 1분
ENABLE_AUTO_RECOVERY = True
```

#### 4.2 env.template 업데이트
```env
# 헬스 모니터 활성화
ENABLE_HEALTH_MONITOR=True

# 헬스 체크 간격 (초)
# 추천: 60-180초
HEALTH_CHECK_INTERVAL=60

# 자동 복구 활성화
ENABLE_AUTO_RECOVERY=True
```

#### 4.3 print_config() 출력
```
헬스 모니터:
  헬스 모니터: 활성화
  체크 간격: 60초
  자동 복구: 활성화
```

### 5. 패키지 의존성

#### 5.1 requirements_extended.txt 추가
```
# Phase 4: 헬스 모니터
psutil==5.9.6  # 프로세스/시스템 모니터링
```

**psutil 주요 기능**:
- 프로세스 메모리 사용률 조회
- CPU 사용률 조회
- 스레드 수 조회
- 네트워크/디스크 I/O 조회 (향후 확장 가능)

---

## 🎯 주요 성과

### 1. 안정성 대폭 향상
- ✅ API 연결 끊김 자동 복구
- ✅ 리소스 과다 사용 조기 감지
- ✅ 프로그램 이상 징후 실시간 모니터링
- ✅ 연속 에러 발생 시 안전 종료

### 2. 무인 운영 강화
- ✅ 24시간 운영 중 발생하는 일시적 문제 자동 해결
- ✅ 사용자 개입 최소화
- ✅ 이상 상황 로그 상세 기록
- ✅ 복구 불가능 시 명확한 알림

### 3. 디버깅 편의성
- ✅ 헬스 체크 이력 1000개 저장
- ✅ 건강률 통계 제공
- ✅ 문제 발생 시간 및 원인 추적 가능
- ✅ 헬스 요약 정보 한눈에 확인

---

## 📊 헬스 모니터 출력 예시

### 정상 상태
```
✅ 헬스 체크 정상 - API: 연결, 엔진: 실행, 메모리: 45.2%, CPU: 15.8%
```

### 이상 감지
```
==========================================
🚨 프로그램 이상 감지!
연속 에러: 2회
이슈: API 연결 끊김
경고: 메모리 사용률 높음: 85.3%
==========================================

🔧 자동 복구 시도 중... (1/3)
🔄 API 재연결 시도 중...
✅ API 재연결 성공
🎉 자동 복구 성공!
```

### 헬스 요약 (종료 시)
```
====================================
🏥 헬스 체크 요약
====================================
상태: ✅ 정상
마지막 체크: 2025-10-27 15:30:45
건강률 (최근 10회): 100.0%
연속 에러: 0회
총 에러: 0회
복구 시도: 0회

API 연결: ✅
엔진 실행: ✅
메모리 사용률: 45.2%
CPU 사용률: 15.8%
활성 스레드: 8개
====================================
```

---

## 🔧 사용 방법

### 1. 기본 설정 (권장)
```env
ENABLE_HEALTH_MONITOR=True
HEALTH_CHECK_INTERVAL=60
ENABLE_AUTO_RECOVERY=True
```

**필요 패키지**:
```powershell
pip install psutil
```

### 2. 비활성화
```env
ENABLE_HEALTH_MONITOR=False
```
**추가 패키지 불필요**

### 3. 고급 설정
```env
# 더 짧은 간격 (CPU 사용률 증가)
HEALTH_CHECK_INTERVAL=30  # 30초

# 수동 복구만 사용
ENABLE_AUTO_RECOVERY=False
```

---

## 🧪 테스트 시나리오

### 시나리오 1: API 연결 끊김 복구
```
1. 프로그램 실행 중
2. 키움 서버 일시적 장애 발생
3. 헬스 모니터가 연결 끊김 감지
4. 자동으로 재연결 시도
5. 재연결 성공, 프로그램 계속 실행
```

**예상 결과**: ✅ 무중단 운영

### 시나리오 2: 메모리 과다 사용 감지
```
1. 프로그램 장시간 실행
2. 메모리 사용률 80% 초과
3. 헬스 모니터가 경고 로그 출력
4. 사용자가 프로그램 재시작 결정
```

**예상 결과**: ✅ 조기 감지, 수동 개입

### 시나리오 3: 연속 에러 발생
```
1. 알 수 없는 이유로 연속 에러 5회
2. 헬스 모니터가 모니터링 중지
3. "수동 개입 필요" 로그 출력
4. 사용자가 로그 확인 후 조치
```

**예상 결과**: ✅ 안전 종료, 명확한 알림

---

## 📝 변경 파일 목록

### 신규 파일
1. `health_monitor.py` - 헬스 모니터 시스템

### 수정 파일
1. `kiwoom_api.py` - `reconnect()`, `get_connection_status()` 추가
2. `trading_engine.py` - 헬스 모니터 통합
3. `config.py` - 헬스 모니터 설정 추가
4. `env.template` - 헬스 모니터 설정 추가
5. `requirements_extended.txt` - psutil 추가

---

## 🚀 다음 단계

Phase 4의 남은 작업:
1. ⏳ GUI 차트 기능 (`chart_widget.py`)
2. ⏳ GUI 상세 통계 (`monitor_gui.py` 확장)
3. ⏳ 설정 UI (`settings_dialog.py`)
4. ⏳ 스케줄러 (`scheduler.py`)

---

## 🎓 기대 효과

### 단기 효과
- 💪 API 연결 안정성 향상
- 🔧 일시적 문제 자동 해결
- 📊 프로그램 상태 가시성 확보

### 장기 효과
- 🤖 완전 무인 운영 가능
- 🛡️ 장시간 운영 시 안정성 보장
- 📈 운영 품질 지속적 개선

---

**작성일**: 2025-10-27  
**Phase**: Phase 4-A (에러 복구 & 헬스 모니터)  
**진행률**: Phase 4의 약 40% 완료
**다음 작업**: GUI 개선 (차트, 통계, 설정)

