# 단타 매매 실시간 모니터링 업데이트

**날짜**: 2025-10-27  
**목적**: 단타 매매에서 매수/매도 시점을 실시간으로 명확하게 확인  
**상태**: ✅ 완료

---

## 📋 변경 요청

> "단타로 매수 매도 하는 시스템입니다. 언제 매수하고 언제 매도하는지 실시간 확인이 되어야합니다."

**문제점**:
- 신호 체크가 60초(1분)마다 → 단타에 너무 느림
- 매수/매도 로그가 간단 → 추적이 어려움
- 실시간 가격 표시가 부족 → 시장 상황 파악 어려움
- 손절/익절 로그가 불명확 → 리스크 관리 확인 어려움

---

## 🔧 주요 변경 사항

### 1. 신호 체크 주기 단축 (60초 → 10초)

**파일**: `auto_trading/trading_engine.py` (381-387번 라인)

**변경 전**:
```python
# 너무 자주 체크하지 않도록 (1분에 1번)
now = time.time()
last_check = self.last_check_time.get(stock_code, 0)
if now - last_check < 60:  # 60초
    return
```

**변경 후**:
```python
# 단타 매매를 위한 빠른 신호 체크 (10초마다)
now = time.time()
last_check = self.last_check_time.get(stock_code, 0)
if now - last_check < 10:  # 10초
    return
```

**효과**:
- ✅ 6배 빠른 신호 감지
- ✅ 단타 매매에 적합한 반응 속도
- ✅ 급변하는 시장 대응력 향상

---

### 2. 매수/매도 신호 발생 시 명확한 알림

**파일**: `auto_trading/trading_engine.py` (415-432번 라인)

**변경 후**:
```python
# 매수 신호
if signal == SignalType.BUY:
    log.warning("=" * 70)
    log.warning(f"🔔 매수 신호 발생! {stock_code}")
    log.warning(f"   현재가: {current_price:,}원")
    log.warning(f"   신호 강도: {signal_result['strength']:.2f}")
    log.warning(f"   사유: {signal_result['reason']}")
    log.warning("=" * 70)
    self.execute_buy(stock_code, current_price, signal_result)

# 매도 신호
elif signal == SignalType.SELL:
    log.warning("=" * 70)
    log.warning(f"🔔 매도 신호 발생! {stock_code}")
    log.warning(f"   현재가: {current_price:,}원")
    log.warning(f"   신호 강도: {signal_result['strength']:.2f}")
    log.warning(f"   사유: {signal_result['reason']}")
    log.warning("=" * 70)
    self.execute_sell(stock_code, current_price, signal_result)
```

**효과**:
- ✅ 신호 발생 즉시 명확한 알림
- ✅ 신호 강도와 사유 명시
- ✅ 눈에 잘 띄는 구분선

---

### 3. 매수 체결 로그 상세화

**파일**: `auto_trading/trading_engine.py` (486-500번 라인)

**변경 후**:
```python
if position:
    total_cost = current_price * quantity
    log.success("=" * 70)
    log.success(f"✅ 매수 체결 완료!")
    log.success(f"   종목: {stock_code}")
    log.success(f"   수량: {quantity}주")
    log.success(f"   체결가: {current_price:,}원")
    log.success(f"   총 금액: {total_cost:,}원")
    log.success(f"   사유: {signal_result['reason']}")
    log.success(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
    log.success("=" * 70)
```

**효과**:
- ✅ 체결 시각 명확히 표시
- ✅ 총 투자 금액 표시
- ✅ 매수 사유 기록

---

### 4. 매도 체결 로그 상세화

**파일**: `auto_trading/trading_engine.py` (547-560번 라인)

**변경 후**:
```python
if profit_loss is not None:
    total_amount = current_price * position.quantity
    profit_rate = (profit_loss / (position.buy_price * position.quantity)) * 100
    log.success("=" * 70)
    log.success(f"✅ 매도 체결 완료!")
    log.success(f"   종목: {stock_code}")
    log.success(f"   수량: {position.quantity}주")
    log.success(f"   매수가: {position.buy_price:,}원")
    log.success(f"   매도가: {current_price:,}원")
    log.success(f"   총 금액: {total_amount:,}원")
    log.success(f"   손익: {profit_loss:+,}원 ({profit_rate:+.2f}%)")
    log.success(f"   사유: {signal_result['reason']}")
    log.success(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
    log.success("=" * 70)
```

**효과**:
- ✅ 매수가와 매도가 비교
- ✅ 손익 금액과 수익률 표시
- ✅ 체결 시각 명확히 표시

---

### 5. 실시간 가격 표시 주기 개선

**파일**: `auto_trading/trading_engine.py` (367-372번 라인)

**변경 전**:
```python
# 관심 종목의 실시간 가격 표시 (10번째 업데이트마다)
if len(self.price_history[stock_code]) % 10 == 0:
```

**변경 후**:
```python
# 관심 종목의 실시간 가격 표시 (5번째 업데이트마다) - 단타에 적합
if len(self.price_history[stock_code]) % 5 == 0:
```

**효과**:
- ✅ 2배 많은 가격 정보
- ✅ 시장 상황 파악 용이
- ✅ 단타 매매 타이밍 포착

---

### 6. 손절매 조건 감지 로그 강화

**파일**: `auto_trading/trading_engine.py` (576-590번 라인)

**변경 후**:
```python
if self.risk_manager.check_stop_loss(position):
    loss_rate = ((position.current_price - position.buy_price) / position.buy_price) * 100
    log.warning("=" * 70)
    log.warning(f"🚨 손절매 조건 감지!")
    log.warning(f"   종목: {stock_code}")
    log.warning(f"   매수가: {position.buy_price:,}원")
    log.warning(f"   현재가: {position.current_price:,}원")
    log.warning(f"   손실률: {loss_rate:.2f}%")
    log.warning(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
    log.warning("=" * 70)
    self.execute_exit(stock_code, position.current_price, "손절매")
```

**효과**:
- ✅ 손절매 조건 즉시 명확히 표시
- ✅ 손실률 명시
- ✅ 리스크 관리 추적 용이

---

### 7. 익절매 조건 감지 로그 강화

**파일**: `auto_trading/trading_engine.py` (593-607번 라인)

**변경 후**:
```python
elif self.risk_manager.check_take_profit(position):
    profit_rate = ((position.current_price - position.buy_price) / position.buy_price) * 100
    log.warning("=" * 70)
    log.warning(f"🎯 익절매 조건 감지!")
    log.warning(f"   종목: {stock_code}")
    log.warning(f"   매수가: {position.buy_price:,}원")
    log.warning(f"   현재가: {position.current_price:,}원")
    log.warning(f"   수익률: {profit_rate:.2f}%")
    log.warning(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
    log.warning("=" * 70)
    self.execute_exit(stock_code, position.current_price, "익절매")
```

**효과**:
- ✅ 익절매 목표 달성 즉시 표시
- ✅ 수익률 명시
- ✅ 이익 실현 타이밍 명확

---

### 8. 청산 체결 로그 상세화

**파일**: `auto_trading/trading_engine.py` (642-656번 라인)

**변경 후**:
```python
if profit_loss is not None:
    total_amount = sell_price * position.quantity
    profit_rate = (profit_loss / (position.buy_price * position.quantity)) * 100
    emoji = "✅" if profit_loss >= 0 else "❌"
    log.success("=" * 70)
    log.success(f"{emoji} 청산 체결 완료! ({reason})")
    log.success(f"   종목: {stock_code}")
    log.success(f"   수량: {position.quantity}주")
    log.success(f"   매수가: {position.buy_price:,}원")
    log.success(f"   매도가: {sell_price:,}원")
    log.success(f"   총 금액: {total_amount:,}원")
    log.success(f"   손익: {profit_loss:+,}원 ({profit_rate:+.2f}%)")
    log.success(f"   사유: {reason}")
    log.success(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
    log.success("=" * 70)
```

**효과**:
- ✅ 청산 사유 명확 (손절/익절)
- ✅ 최종 손익 상세 표시
- ✅ 수익/손실에 따른 이모지

---

## 📊 실시간 모니터링 예시

### 전체 흐름 (삼성전자 단타 매매)

```
2025-10-27 09:15:35 | INFO  | 📊 실시간: 005930 73,500원 (+1.23%) | 데이터: 45개
2025-10-27 09:15:40 | INFO  | 📊 실시간: 005930 73,600원 (+1.37%) | 데이터: 50개
2025-10-27 09:15:45 | INFO  | 📊 실시간: 005930 73,700원 (+1.50%) | 데이터: 55개

======================================================================
🔔 매수 신호 발생! 005930
   현재가: 73,700원
   신호 강도: 2.50
   사유: 이동평균선 골든크로스, RSI 상승 반전
======================================================================

2025-10-27 09:15:46 | INFO  | 📈 매수 시도: 005930 13주 @ 73,700원 | 신호 강도: 2.50

======================================================================
✅ 매수 체결 완료!
   종목: 005930
   수량: 13주
   체결가: 73,700원
   총 금액: 958,100원
   사유: 이동평균선 골든크로스, RSI 상승 반전
   시각: 09:15:47
======================================================================

2025-10-27 09:20:15 | INFO  | 📊 실시간: 005930 74,200원 (+1.91%) | 데이터: 60개
2025-10-27 09:23:30 | INFO  | 📊 실시간: 005930 74,800원 (+2.73%) | 데이터: 65개
2025-10-27 09:26:45 | INFO  | 📊 실시간: 005930 75,200원 (+3.28%) | 데이터: 70개

======================================================================
🔔 매도 신호 발생! 005930
   현재가: 75,200원
   신호 강도: 2.00
   사유: MACD 데드크로스
======================================================================

2025-10-27 09:26:46 | INFO  | 📉 매도 시도: 005930 13주 @ 75,200원 | 신호 강도: 2.00

======================================================================
✅ 매도 체결 완료!
   종목: 005930
   수량: 13주
   매수가: 73,700원
   매도가: 75,200원
   총 금액: 977,600원
   손익: +19,500원 (+2.04%)
   사유: MACD 데드크로스
   시각: 09:26:47
======================================================================
```

**결과**:
- ⏱️ 보유 시간: **11분** (09:15:47 ~ 09:26:47)
- 💰 수익: **+19,500원 (+2.04%)**
- ✅ **단타 매매 성공!**

---

## 📈 성능 비교

| 항목 | 변경 전 | 변경 후 | 개선 |
|------|---------|---------|------|
| **신호 체크** | 60초 | 10초 | 6배 빠름 |
| **가격 표시** | 10번째마다 | 5번째마다 | 2배 많음 |
| **매수/매도 로그** | 간단 | 상세 (9개 항목) | 명확함 |
| **손절/익절 로그** | 기본 | 상세 (사유, 시각) | 추적 용이 |
| **체결 시각** | 없음 | 명시 | 타이밍 확인 |
| **손익률** | 금액만 | 금액 + 퍼센트 | 성과 평가 |

---

## 🎯 단타 매매 권장 설정

### .env 파일 최적화

```ini
# ==========================================
# 단타 매매 최적화 설정
# ==========================================

# 최대 보유 종목 수 (단타는 집중 투자)
MAX_STOCKS=2

# 종목당 투자 비율 (단타는 큰 포지션)
POSITION_SIZE_PERCENT=15

# 손절매 비율 (단타는 타이트하게)
STOP_LOSS_PERCENT=3

# 익절매 비율 (단타는 빠르게)
TAKE_PROFIT_PERCENT=5

# 일일 손실 한도 (단타는 여유있게)
DAILY_LOSS_LIMIT_PERCENT=5

# 신호 강도 (단타는 민감하게)
MIN_SIGNAL_STRENGTH=2
```

---

## 🔍 실시간 모니터링 방법

### 1. 콘솔 실시간 확인 (권장)

```powershell
cd auto_trading
python main.py
```

**장점**:
- ✅ 실시간 즉시 확인
- ✅ 색상 코딩
- ✅ 매수/매도 알림

---

### 2. 로그 파일 추적

```powershell
# 실시간 로그 추적
Get-Content auto_trading\logs\trading.log -Wait -Tail 50

# 매수/매도만 필터링
Get-Content auto_trading\logs\trading.log | Select-String "체결 완료"

# 손익만 확인
Get-Content auto_trading\logs\trading.log | Select-String "손익:"
```

---

## ✅ 적용 방법

### 즉시 적용

프로그램을 재시작하면 바로 적용됩니다:

```cmd
cd auto_trading
python main.py
```

또는

```cmd
cd auto_trading
start.bat
```

---

## 🎉 결과

### 개선 사항 요약

1. ✅ **신호 체크 주기 6배 단축** (60초 → 10초)
2. ✅ **실시간 가격 표시 2배 증가** (10번째 → 5번째)
3. ✅ **매수/매도 로그 상세화** (시각, 금액, 사유)
4. ✅ **손절/익절 로그 강화** (조건 감지 즉시 알림)
5. ✅ **체결 시각 명시** (정확한 타이밍 추적)
6. ✅ **손익률 표시** (금액 + 퍼센트)

### 단타 매매 최적화

- ✅ 10초마다 신호 체크 → 빠른 대응
- ✅ 명확한 알림 → 놓치지 않음
- ✅ 상세한 로그 → 정확한 추적
- ✅ 자동 손절/익절 → 리스크 관리

---

## 📝 관련 파일

1. `auto_trading/trading_engine.py` - 핵심 로직 수정
2. `auto_trading/DAYTRADING_REALTIME_MONITOR.md` - 상세 가이드
3. `auto_trading/README.md` - 문서 링크 추가

---

## 🚀 다음 단계

### 향후 개선 계획

1. **GUI 실시간 차트** - 매수/매도 시점 시각화
2. **소리 알림** - 체결 완료 시 알림음
3. **카카오톡 알림** - 중요 이벤트 알림
4. **성과 대시보드** - 일일/주간 성과 요약

---

**작성**: CleonAI 개발팀  
**날짜**: 2025-10-27  
**버전**: v1.3  
**상태**: ✅ 완료

**단타 매매에 최적화된 실시간 모니터링!**

언제 매수하고 언제 매도하는지 명확하게 확인할 수 있습니다.  
10초마다 신호 체크, 상세한 체결 로그, 자동 손절/익절까지!

---


