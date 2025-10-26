# 프론트엔드 계좌 표시 개선

**날짜**: 2025-10-26  
**문제**: 계좌 정보 표시가 부정확함

## 🔍 문제점

### 이전 표시
```
=== 08:52:11 업데이트 ===
✅ 계좌 조회 성공
   브로커: kiwoom
   계좌: 모의투자          ❌ 계좌번호가 아님
   잔고: 10,000,000원
```

**문제**:
- "계좌: 모의투자" - 실제 계좌번호가 표시되지 않음
- 모의투자/실계좌 구분이 불명확

## ✅ 개선 사항

### 현재 표시
```
=== 08:52:11 업데이트 ===
✅ 계좌 조회 성공
   브로커: kiwoom
   계좌번호: 8113110311    ✅ 실제 계좌번호
   계좌타입: 🎮 모의투자    ✅ 명확한 구분
   잔고: 10,000,000원
```

### 대시보드 표시
```
📊 브로커: kiwoom
💳 계좌번호: 8113110311
🎮 모의투자
💰 잔고: 10,000,000원
```

또는 실계좌인 경우:
```
📊 브로커: kiwoom
💳 계좌번호: 1234567890
💼 실계좌
💰 잔고: 50,000,000원
```

## 🔧 수정된 파일

### 1. `backend/test_server.py`
**변경 전**:
```python
{
    "id": 1,
    "broker": "kiwoom",
    "account_number": "모의투자",  # ❌ 잘못된 필드명
    "balance": 10000000
}
```

**변경 후**:
```python
{
    "id": 1,
    "broker": "kiwoom",
    "account_no": "8113110311",        # ✅ 실제 계좌번호
    "account_name": "모의투자계좌",      # ✅ 계좌명
    "account_type": "simulation",       # ✅ simulation 또는 real
    "balance": 10000000,
    "initial_balance": 10000000,
    "is_active": True
}
```

### 2. `frontend/main.py`
**주요 개선**:
```python
# 계좌 타입 표시
account_type = account.get('account_type', 'unknown')
account_type_text = "🎮 모의투자" if account_type == "simulation" else "💼 실계좌"

# 계좌번호 (호환성 유지)
account_no = account.get('account_no') or account.get('account_number', 'N/A')

# 상세 표시
self.result_text.append(f"   브로커: {account.get('broker')}")
self.result_text.append(f"   계좌번호: {account_no}")
self.result_text.append(f"   계좌타입: {account_type_text}")
self.result_text.append(f"   잔고: {account.get('balance'):,}원")
```

## 📊 데이터 구조

### Backend API 응답 형식
```json
{
  "id": 1,
  "broker": "kiwoom",
  "account_no": "8113110311",
  "account_name": "모의투자계좌",
  "account_type": "simulation",
  "balance": 10000000,
  "initial_balance": 10000000,
  "is_active": true
}
```

### 필드 설명
| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `id` | int | 계좌 ID | 1 |
| `broker` | string | 브로커명 | "kiwoom" |
| `account_no` | string | 계좌번호 | "8113110311" |
| `account_name` | string | 계좌명 (선택) | "모의투자계좌" |
| `account_type` | string | 계좌타입 | "simulation" 또는 "real" |
| `balance` | int | 현재 잔고 | 10000000 |
| `initial_balance` | int | 초기 잔고 | 10000000 |
| `is_active` | bool | 활성화 여부 | true |

## 🚀 테스트 방법

### 1. Backend 재시작
```powershell
# 기존 서버 종료 (Ctrl+C)

# 새 터미널에서 Backend 시작
cd backend
python test_server.py
```

### 2. Frontend 재시작
```powershell
# 기존 Frontend 종료 (Ctrl+C)

# 새 터미널에서 Frontend 시작
cd frontend
python main.py
```

### 3. 확인
Frontend 대시보드에서 다음과 같이 표시되어야 합니다:

**대시보드 영역**:
```
📊 브로커: kiwoom
💳 계좌번호: 8113110311
🎮 모의투자
💰 잔고: 10,000,000원
```

**결과 영역** (5초마다 업데이트):
```
=== 09:00:00 업데이트 ===
✅ 계좌 조회 성공
   브로커: kiwoom
   계좌번호: 8113110311
   계좌타입: 🎮 모의투자
   잔고: 10,000,000원
```

## 🔄 호환성

### 이전 API 형식 지원
이전 형식(`account_number`)도 계속 지원됩니다:
```python
# 우선순위: account_no > account_number
account_no = account.get('account_no') or account.get('account_number', 'N/A')
```

### 실계좌 표시
`account_type`이 `"real"`인 경우:
```
💼 실계좌
```

## 💡 추가 개선 사항

### 실시간 데이터 연동 (향후)
자동매매 프로그램에서 실제 계좌 정보를 가져와서 표시:

```python
# auto_trading/main.py 또는 trading_engine.py
# Backend API로 계좌 정보 전송
account_data = {
    "broker": "kiwoom",
    "account_no": kiwoom.account_number,
    "account_type": "simulation" if Config.USE_SIMULATION else "real",
    "balance": balance_info.get('cash', 0)
}
```

### 다중 계좌 지원
여러 계좌를 동시에 표시:
```python
for i, account in enumerate(accounts, 1):
    self.result_text.append(f"\n[계좌 {i}]")
    self.result_text.append(f"   계좌번호: {account['account_no']}")
    self.result_text.append(f"   잔고: {account['balance']:,}원")
```

## 📝 개발자 노트

### account_number vs account_no
- **Old**: `account_number` (테스트용, 비표준)
- **New**: `account_no` (데이터베이스 모델에 맞춤)

데이터베이스 모델(`backend/app/db/models.py`):
```python
class Account(Base):
    account_no = Column(String(50), nullable=False)
    account_type = Column(String(20), nullable=False)  # 'simulation', 'real'
```

### 계좌 타입
- `simulation`: 모의투자 계좌 (🎮)
- `real`: 실계좌 (💼)

## ⚠️ 주의 사항

### 실계좌 사용 시
- 실계좌 번호는 민감 정보입니다
- 로그에 출력할 때 마스킹 고려
- 예: `8113******11` 또는 `8113****`

### 보안 고려사항
```python
# 계좌번호 마스킹 (향후 구현)
def mask_account_no(account_no: str) -> str:
    if len(account_no) > 8:
        return account_no[:4] + "****" + account_no[-4:]
    return "****"
```

## 🎉 결과

이제 Frontend가:
- ✅ 실제 계좌번호를 명확히 표시
- ✅ 모의투자/실계좌를 이모지로 구분
- ✅ 데이터베이스 모델과 일치하는 필드 사용
- ✅ 이전 형식도 호환 지원

**바로 테스트해보세요!** 🚀

---

**작성**: CleonAI 개발팀  
**날짜**: 2025-10-26  
**버전**: v1.3  
**상태**: ✅ 완료

