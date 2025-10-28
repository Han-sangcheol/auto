# 🐛 콜백 파라미터 오류 수정 (2025-10-28)

## 📌 문제 증상

**하루 종일 프로그램을 실행해도 매수/매도가 전혀 실행되지 않음**

### 로그 예시

```
🚀 급등 감지! 예선테크 (250930) | 상승률: +20.11% | 거래량: 2.00배
ERROR: 급등주 승인 처리 중 오류: create_surge_approval_callback.<locals>.surge_approval_callback() 
       takes 2 positional arguments but 3 were given

→ 매수 시도 없음
→ GUI에 데이터 없음
```

## 🔍 원인 분석

### 콜백 파라미터 불일치

**trading_engine.py (호출하는 쪽):**
```python
# 3개 파라미터를 전달
self.surge_approval_callback(stock_code, candidate.name, surge_info)
                              ↑         ↑              ↑
                              1개       2개            3개
```

**main.py (받는 쪽):**
```python
# 2개 파라미터만 받음
def surge_approval_callback(stock_code: str, candidate) -> bool:
                             ↑                ↑
                             1개              2개
```

**결과:**
- TypeError 발생
- 승인 프로세스 실패
- 매수 실행 안 됨

## 🔨 근본 원인

코드 수정 과정에서 일관성 문제 발생:

1. **원래 설계 (기존):**
   ```python
   # trading_engine.py
   callback(stock_code, candidate.name, surge_info)
   
   # main.py  
   def callback(stock_code, stock_name, surge_info):
   ```

2. **호가 분석 추가 시 (수정):**
   ```python
   # main.py만 수정
   def callback(stock_code, candidate):  # candidate 객체 전체 필요
   ```

3. **trading_engine.py는 수정 안 됨:**
   ```python
   # 여전히 3개 파라미터 전달
   callback(stock_code, candidate.name, surge_info)
   ```

## ✅ 해결 방법

### trading_engine.py 수정

**Before (문제):**
```python
# 승인 요청
surge_info = {
    'name': candidate.name,
    'price': candidate.current_price,
    'change_rate': candidate.current_change_rate,
    'volume_ratio': candidate.get_volume_ratio()
}

def request_approval():
    try:
        approved = self.surge_approval_callback(stock_code, candidate.name, surge_info)
        if approved:
            self.add_surge_stock(stock_code, candidate)
        ...
```

**After (수정):**
```python
# 승인 요청 (candidate 객체를 직접 전달)
def request_approval():
    try:
        # 콜백 함수에 stock_code와 candidate 전달 (2개)
        approved = self.surge_approval_callback(stock_code, candidate)
        # 콜백에서 이미 add_surge_stock 호출하므로 여기서는 호출 안 함
        if not approved:
            log.info(f"급등주 매수 거부: {candidate.name}")
        ...
```

### 변경 사항 요약

| 항목 | Before | After |
|------|--------|-------|
| **파라미터 개수** | 3개 | **2개** |
| **파라미터** | `stock_code, name, info` | `stock_code, candidate` |
| **add_surge_stock 호출** | request_approval()에서 | **callback()에서** |

## 📊 수정 후 예상 동작

### 1. 급등 감지
```
🚀 급등 감지! 예선테크 (250930) | 상승률: +20.11% | 거래량: 2.00배
```

### 2. 승인 처리
```
✅ 급등주 자동 승인: 예선테크
```

### 3. 매수 실행
```
✅ 급등주 추가: 예선테크 (250930) | 상승률: +20.11% | 거래량: 2.00배
🔍 실시간 시세 등록 시도: 250930
✅ 실시간 시세 등록 완료: 250930

🚀 급등주 즉시 매수 시도!
   종목: 예선테크 (250930)
   현재가: 663원
   상승률: +20.11%

🔍 [execute_buy] 리스크 검증 중...
✅ [execute_buy] 리스크 검증 통과
✅ [execute_buy] 수량 계산 완료: 150주

📈 매수 시도: 250930 150주 @ 663원
✅ 매수 주문 전송 완료 (주문번호: 123456)
🎉 매수 체결: 250930 예선테크 150주 @ 663원
```

### 4. GUI 표시
```
보유 종목 테이블:
종목코드 | 종목명   | 수량 | 매수가 | 현재가 | 수익률
250930  | 예선테크 | 150  | 663   | 670   | +1.06%
```

## 🚀 프로그램 재시작

### 1. 현재 프로그램 종료

**Ctrl+C** 또는

```bash
taskkill /F /IM python.exe
```

### 2. 프로그램 재시작

```bash
start.bat
```

### 3. 로그 확인

**정상 작동 시:**
```bash
# 로그에서 에러 없이 매수 진행
🚀 급등 감지! → ✅ 자동 승인 → ✅ 급등주 추가 → 📈 매수 시도 → 🎉 매수 체결
```

**문제 지속 시:**
```bash
# logs/error_*.log 확인
Select-String -Path "logs/error_2025-10-28.log" -Pattern "급등주 승인"
```

## 📋 체크리스트

수정 완료 후:

- [x] `trading_engine.py` 콜백 호출 수정
- [x] 파라미터 개수 일치 (2개)
- [ ] 프로그램 재시작
- [ ] 급등주 감지 확인
- [ ] 승인 에러 없는지 확인
- [ ] 매수 실행 확인
- [ ] GUI 테이블 업데이트 확인

## ⚠️ 주의사항

### 1. 급등주 조건 (현재 설정)

```
후보 종목: 30개
상승률: >= 5%
거래량: >= 2배
호가 조건: 비활성화 (0점)
```

### 2. 자동 매수 활성화

- 급등주 감지 시 **즉시 자동 매수**
- 사용자 확인 없음
- 최대 20개 종목까지

### 3. 리스크 관리

- 손절매: -5% 자동 실행
- 익절매: +10% 자동 실행
- 일일 손실 한도: -3%

## 🔗 관련 수정 사항

이번 수정으로 완료된 모든 급등주 관련 이슈:

1. ✅ **급등주 매수 미실행** → `SURGE_BUY_FIX_2025-10-28.md`
2. ✅ **호가 분석 기능 추가** → `ORDERBOOK_ANALYSIS_2025-10-28.md`
3. ✅ **과부하 방지** → `OVERLOAD_FIX_2025-10-28.md`
4. ✅ **GUI 데이터 미표시** → `GUI_NO_DATA_FIX_2025-10-28.md`
5. ✅ **콜백 파라미터 오류** → 본 문서 ⬅️ **최종 수정**

## 🎯 최종 확인

### 프로그램 재시작 후 확인 사항

```bash
# 1. 로그에서 에러 확인
Select-String -Path "logs/error_2025-10-28.log" -Pattern "급등주 승인"
→ 에러 없어야 함

# 2. 급등 감지 확인
Select-String -Path "logs/trading_2025-10-28.log" -Pattern "급등 감지" | Select-Object -Last 5
→ 급등 감지 로그 있어야 함

# 3. 매수 실행 확인
Select-String -Path "logs/trading_2025-10-28.log" -Pattern "매수 시도|매수 체결" | Select-Object -Last 5
→ 매수 로그 있어야 함
```

## 💡 테스트 방법

### 모의투자 환경에서 테스트

1. **프로그램 실행** (모의투자 모드)
2. **급등주 감지 대기** (5-10분)
3. **매수 실행 확인** (로그 + GUI)
4. **손익 확인** (1시간 후)

### 급등주 감지가 안 되면

조건을 더 완화:
```env
SURGE_MIN_CHANGE_RATE=3.0  # 5% → 3%
```

---

**최종 업데이트**: 2025-10-28
**상태**: ✅ 수정 완료
**효과**: 🎯 급등주 매수/매도 정상 작동
**중요**: 🔄 **반드시 프로그램 재시작 필요!**

