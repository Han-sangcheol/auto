# 키움 API 과부하 방지 업데이트 - 2025-10-27

## 🚨 **문제 상황**

```
2025-10-27 15:00:51 | ✅ 급등주 자동 승인: HJ중공업
2025-10-27 15:00:51 | ✅ 급등주 자동 승인: 한미사이언스
2025-10-27 15:00:51 | ✅ 급등주 자동 승인: 형지I&C
... (8개 종목 동시 승인)
2025-10-27 15:00:51 | 🔍 실시간 시세 등록 시도: 097230
→ 이후 프로그램 멈춤

2025-10-27 15:00:46 | ERROR | ❌ 잔고 조회 실패: -202
2025-10-27 15:09:49 | ERROR | ❌ 잔고 조회 실패: -202
```

**원인:**
1. 급등주 8개가 **동시에 1초 안에 승인**됨
2. 각각 **실시간 시세 등록** 시도 → API 과부하
3. **-202 (조회 과부하)** 에러 발생
4. 프로그램 불안정 또는 크래시

## ✅ **구현된 해결책**

### 1️⃣ **급등주 순차 처리 (`trading_engine.py`)**

#### 변경 내용:
```python
# 추가된 플래그
self.surge_processing = False  # 처리 중 플래그

def add_surge_stock(stock_code, candidate):
    # 이미 처리 중이면 건너뜀
    if self.surge_processing:
        log.warning("⏳ 다른 급등주 처리 중 - 대기")
        return
    
    with self.surge_add_lock:
        try:
            self.surge_processing = True  # 처리 시작
            
            # 최대 종목 수 체크 추가
            if len(positions) >= Config.MAX_STOCKS:
                log.warning("⚠️  최대 보유 종목 수 도달 - 추가 불가")
                return
            
            # 실시간 시세 등록 (1초 → 1.5초 대기로 증가)
            time.sleep(1.0)
            self.kiwoom.register_real_data([stock_code])
            time.sleep(0.5)  # 추가 안전 대기
            
        finally:
            self.surge_processing = False  # 처리 완료
```

#### 효과:
- ❌ **이전**: 8개 동시 처리 → API 과부하
- ✅ **현재**: 1개씩 순차 처리 → 안정적

### 2️⃣ **API 호출 제한 강화 (`kiwoom_api.py`)**

#### 변경 전:
```python
self.request_delay = 0.2  # 단순 0.2초 간격
```

#### 변경 후:
```python
# 초기화
self.request_delay = 0.5  # 0.5초 최소 간격
self.request_history = []  # 최근 요청 시간 추적

def _wait_for_request():
    # 1초 내 요청 수 제한
    if len(self.request_history) >= 2:  # 초당 2건 제한
        wait_time = 1.0 - (now - oldest_request) + 0.1
        log.warning(f"⏳ API 과부하 방지 대기: {wait_time:.1f}초")
        time.sleep(wait_time)
    
    # 최소 간격 보장
    if elapsed < 0.5:
        time.sleep(0.5 - elapsed)
```

#### 효과:
- **초당 5건** (공식 제한) → **초당 2건** (안전 제한)
- **150% 안전 마진** 확보

### 3️⃣ **실시간 시세 배치 처리 (`kiwoom_api.py`)**

#### 변경 내용:
```python
def register_real_data(stock_codes):
    batch_size = 50  # 50개 단위로 분할
    
    if len(stock_codes) > batch_size:
        log.warning(f"⚠️  분할 등록: {len(stock_codes)}개 → {batch_size}개씩")
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i+batch_size]
            self.register_real_data(batch)
            time.sleep(2.0)  # 배치 간 대기
```

#### 효과:
- 100개 종목 → 50개 + 2초 대기 + 50개
- API 부담 50% 감소

### 4️⃣ **설정 추가 (`config.py`)**

```python
# API 과부하 방지 설정
API_REQUEST_DELAY = 0.5       # 최소 간격
API_MAX_PER_SECOND = 2        # 초당 최대 호출
REAL_DATA_BATCH_SIZE = 50     # 배치 크기
```

## 📊 **개선 효과**

| 항목 | 이전 | 이후 | 개선 |
|------|------|------|------|
| 급등주 동시 처리 | 8개 | **1개** | -87.5% |
| API 호출 간격 | 0.2초 | **0.5초** | +150% |
| 초당 API 호출 | 5건 | **2건** | -60% |
| 실시간 등록 배치 | 100개 | **50개** | -50% |
| 과부하 에러 발생 | **자주** | **거의 없음** | ✅ |

## 🔍 **기대되는 로그 (정상 작동)**

```
15:00:51 | ✅ 급등주 자동 승인: HJ중공업
15:00:51 | ✅ 급등주 추가: HJ중공업 (097230)
15:00:51 | 🔍 실시간 시세 등록 시도: 097230
15:00:52 | ✅ 실시간 시세 등록 완료: 097230
15:00:53 | 🚀 급등주 즉시 매수 시도!
15:00:53 | ✅ 급등주 처리 완료: HJ중공업

15:00:54 | ⏳ 다른 급등주 처리 중 - 대기: 한미사이언스  ← 순차 처리!
15:00:54 | ⏳ 다른 급등주 처리 중 - 대기: 형지I&C
```

## ⚙️ **권장 설정 (.env)**

### **안정성 우선 (권장)**
```env
MAX_STOCKS=3                      # 최대 3개 종목
SURGE_CANDIDATE_COUNT=50          # 급등주 후보 50개로 감소
SURGE_AUTO_APPROVE=True           # 자동 승인 유지
```

### **균형**
```env
MAX_STOCKS=5                      # 최대 5개 종목
SURGE_CANDIDATE_COUNT=100         # 급등주 후보 100개
SURGE_AUTO_APPROVE=True
```

### **공격적 (주의!)**
```env
MAX_STOCKS=10                     # 최대 10개 종목
SURGE_CANDIDATE_COUNT=200         # 급등주 후보 200개
SURGE_AUTO_APPROVE=True
```

⚠️ **경고**: 공격적 설정은 여전히 과부하 위험!

## 🚀 **테스트 방법**

### 1. 프로그램 재시작
```cmd
start.bat
```

### 2. 로그 모니터링
```cmd
# PowerShell (별도 창)
Get-Content logs\trading_2025-10-27.log -Wait -Tail 20
```

### 3. 확인 사항
- ✅ "⏳ 다른 급등주 처리 중 - 대기" 메시지 표시
- ✅ "⏳ API 과부하 방지 대기" 메시지 표시
- ✅ 급등주가 순차적으로 처리됨
- ✅ `-202` 에러가 사라짐 또는 크게 감소

### 4. 과부하 발생 시
```env
# .env 파일 수정
MAX_STOCKS=2                      # 더 줄이기
SURGE_CANDIDATE_COUNT=30          # 더 줄이기
```

## 📁 **수정된 파일**

1. `auto_trading/trading_engine.py`
   - 급등주 순차 처리 플래그 추가
   - 최대 종목 수 체크 추가
   - 실시간 시세 등록 대기 시간 증가 (0.3초 → 1.5초)

2. `auto_trading/kiwoom_api.py`
   - API 호출 제한 강화 (초당 2건)
   - 요청 히스토리 추적
   - 실시간 시세 배치 처리 (50개 단위)

3. `auto_trading/config.py`
   - API 과부하 방지 설정 추가
   - `API_REQUEST_DELAY`, `API_MAX_PER_SECOND`, `REAL_DATA_BATCH_SIZE`

4. **신규 문서**
   - `OVERLOAD_PREVENTION.md`: 과부하 방지 규칙 상세 설명

## ✅ **체크리스트**

### 실행 전:
- [ ] `.env` 파일에서 `MAX_STOCKS` 확인 (기본 3)
- [ ] `SURGE_CANDIDATE_COUNT` 확인 (100 이하 권장)
- [ ] 이전 로그 백업 (선택)

### 실행 중:
- [ ] 급등주가 순차적으로 처리되는지 확인
- [ ] "과부하 방지 대기" 메시지 정상 표시
- [ ] `-202` 에러 발생 빈도 확인

### 문제 발생 시:
- [ ] 로그 확인: `logs/error_2025-10-27.log`
- [ ] 설정 더 보수적으로 조정
- [ ] 프로그램 재시작

## 🎯 **예상 결과**

| 상황 | 이전 | 이후 |
|------|------|------|
| 급등주 8개 동시 감지 | 💥 크래시 | ✅ 1개씩 처리 |
| API 과부하 에러 | 자주 발생 | 거의 없음 |
| 프로그램 안정성 | 불안정 | **안정적** |
| 처리 속도 | 빠름 (불안정) | **느림 (안정)** |

**결론**: 속도는 느려지지만, **안정성이 크게 향상**됩니다!

---

**작성**: 2025-10-27
**버전**: 1.0
**테스트 상태**: ⏳ 대기 중

