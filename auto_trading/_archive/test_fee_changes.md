# 모의투자 수수료 수정 완료

## ✅ 수정 완료 사항

### 1. 수수료율 상수 추가 (34-38줄)
```python
# 키움증권 수수료율 (%)
BUY_COMMISSION_RATE = 0.015  # 실계좌 매수 수수료
SELL_COMMISSION_RATE = 0.015  # 실계좌 매도 수수료
SIMULATION_COMMISSION_RATE = 0.35  # 모의투자 수수료 (매수/매도 동일) ← 추가
TRANSACTION_TAX_RATE = 0.23  # 증권거래세 (매도 시, 실계좌만)
```

### 2. 초기화 로그 메시지 수정 (49-51줄)
```python
if use_simulation:
    log.info("📝 수수료 계산기 초기화 (모의투자 모드)")
    log.info(f"   매수/매도 수수료: {self.SIMULATION_COMMISSION_RATE}%")
```

### 3. 매수 수수료 계산 (68-71줄)
```python
if self.use_simulation:
    # 모의투자: 0.35% 수수료 적용
    fee = round(amount * self.SIMULATION_COMMISSION_RATE / 100)
    return fee
```

### 4. 매도 수수료 계산 (88-91줄)
```python
if self.use_simulation:
    # 모의투자: 0.35% 수수료만 (거래세 없음)
    fee = round(amount * self.SIMULATION_COMMISSION_RATE / 100)
    return fee
```

### 5. 손익분기점 계산 (154-158줄)
```python
if self.use_simulation:
    # 모의투자: 매수 0.35% + 매도 0.35% = 0.70%
    total_fee_rate = (self.SIMULATION_COMMISSION_RATE * 2) / 100
    break_even = round(buy_price * (1 + total_fee_rate))
    return break_even
```

### 6. 수수료 정보 출력 (204-219줄)
모의투자 모드에서도 상세한 수수료 정보 표시

## 📊 수수료 계산 예시

### 100만원 거래 시
```
매수 수수료: 3,500원 (1,000,000 × 0.35%)
매도 수수료: 3,500원 (1,000,000 × 0.35%)
총 수수료:   7,000원
```

### 매수가 10,000원 → 손익분기점
```
손익분기점: 10,070원 (+0.70%)
계산: 10,000 × (1 + 0.70%) = 10,070원
```

## 🔄 다음 단계

1. **프로그램 재실행**
   ```
   cd auto_trading
   .\start.bat
   ```

2. **로그 확인**
   ```
   📝 수수료 계산기 초기화 (모의투자 모드)
      매수/매도 수수료: 0.35%
   ```

3. **-301 에러 확인**
   - 여전히 발생하면: 키움 HTS에서 계좌 81131103 비밀번호 재설정 필요
   - 비밀번호를 0000으로 재설정

## ⚠️ 주의사항

- 계좌번호: 81131103 (8자리) - 변경하지 마세요
- 모의투자는 거래세가 없습니다
- 실계좌로 전환 시 수수료는 0.015%로 자동 변경됩니다






