# CleonAI Trading Platform - API 문서

## 개요

CleonAI Trading Platform은 RESTful API와 WebSocket을 통해 자동매매 시스템과 통신합니다.

**Base URL:** `http://localhost:8000`  
**API Version:** v1  
**API Prefix:** `/api/v1`

**Interactive API 문서:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 인증

현재 버전은 기본 인증 없이 작동합니다. 향후 JWT 기반 인증이 추가될 예정입니다.

---

## REST API 엔드포인트

### 1. 계좌 API (Account)

#### 계좌 목록 조회
```http
GET /api/v1/account/
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "broker": "kiwoom",
    "account_number": "8888888888",
    "account_name": "모의투자",
    "initial_balance": 10000000,
    "current_balance": 9850000,
    "created_at": "2025-10-24T10:00:00"
  }
]
```

---

#### 계좌 잔고 조회
```http
GET /api/v1/account/{account_id}/balance
```

**Path Parameters:**
- `account_id` (integer, required): 계좌 ID

**Response:**
```json
{
  "account_id": 1,
  "current_balance": 9850000,
  "stock_value": 3500000,
  "total_value": 13350000,
  "initial_balance": 10000000,
  "profit_loss": 3350000,
  "profit_loss_percent": 33.5
}
```

---

#### 포지션 목록 조회
```http
GET /api/v1/account/{account_id}/positions
```

**Path Parameters:**
- `account_id` (integer, required): 계좌 ID

**Response:**
```json
[
  {
    "id": 1,
    "account_id": 1,
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "quantity": 10,
    "avg_price": 70000,
    "current_price": 72000,
    "profit_loss": 20000,
    "profit_loss_percent": 2.86,
    "created_at": "2025-10-24T10:30:00"
  }
]
```

---

### 2. 매매 API (Trading)

#### 주문 생성
```http
POST /api/v1/trading/order
```

**Request Body:**
```json
{
  "account_id": 1,
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "order_type": "buy",
  "price_type": "limit",
  "quantity": 10,
  "price": 70000
}
```

**Fields:**
- `account_id` (integer, required): 계좌 ID
- `stock_code` (string, required): 종목 코드
- `stock_name` (string, required): 종목명
- `order_type` (string, required): 주문 유형 (`buy` | `sell`)
- `price_type` (string, required): 가격 유형 (`market` | `limit`)
- `quantity` (integer, required): 수량
- `price` (integer, optional): 가격 (지정가 주문 시 필수)

**Response:**
```json
{
  "id": 1,
  "account_id": 1,
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "order_type": "buy",
  "price_type": "limit",
  "quantity": 10,
  "price": 70000,
  "status": "pending",
  "created_at": "2025-10-24T11:00:00"
}
```

---

#### 주문 목록 조회
```http
GET /api/v1/trading/orders/{account_id}
```

**Query Parameters:**
- `status` (string, optional): 주문 상태 필터 (`pending` | `filled` | `cancelled`)
- `limit` (integer, optional): 조회 개수 (기본: 100)

**Response:**
```json
[
  {
    "id": 1,
    "account_id": 1,
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "order_type": "buy",
    "quantity": 10,
    "price": 70000,
    "status": "filled",
    "created_at": "2025-10-24T11:00:00"
  }
]
```

---

#### 주문 취소
```http
DELETE /api/v1/trading/order/{order_id}
```

**Path Parameters:**
- `order_id` (integer, required): 주문 ID

**Response:**
```json
{
  "id": 1,
  "status": "cancelled",
  "message": "주문이 취소되었습니다."
}
```

---

#### 거래 내역 조회
```http
GET /api/v1/trading/trades/{account_id}
```

**Query Parameters:**
- `start_date` (string, optional): 시작 날짜 (ISO 8601)
- `end_date` (string, optional): 종료 날짜 (ISO 8601)
- `limit` (integer, optional): 조회 개수 (기본: 100)

**Response:**
```json
[
  {
    "id": 1,
    "account_id": 1,
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "trade_type": "buy",
    "quantity": 10,
    "price": 70000,
    "total_amount": 700000,
    "profit_loss": 0,
    "created_at": "2025-10-24T11:01:00"
  }
]
```

---

### 3. 시세 API (Market)

#### 종목 정보 조회
```http
GET /api/v1/market/stocks/{stock_code}
```

**Path Parameters:**
- `stock_code` (string, required): 종목 코드

**Response:**
```json
{
  "stock_code": "005930",
  "name": "삼성전자",
  "price": 72000,
  "change": 1000,
  "change_percent": 1.41,
  "volume": 5000000,
  "high": 73000,
  "low": 71000,
  "market_cap": "429조"
}
```

---

#### 차트 데이터 조회
```http
GET /api/v1/market/stocks/{stock_code}/chart
```

**Query Parameters:**
- `days` (integer, optional): 조회 일수 (기본: 7)
- `interval` (string, optional): 간격 (`1min` | `5min` | `1day`, 기본: `1day`)

**Response:**
```json
{
  "stock_code": "005930",
  "interval": "1day",
  "candles": [
    {
      "timestamp": "2025-10-24T00:00:00",
      "open": 70000,
      "high": 73000,
      "low": 69500,
      "close": 72000,
      "volume": 8000000
    }
  ]
}
```

---

#### 급등주 목록 조회
```http
GET /api/v1/market/surge
```

**Query Parameters:**
- `limit` (integer, optional): 조회 개수 (기본: 20)
- `min_change_rate` (float, optional): 최소 상승률 (기본: 5.0)

**Response:**
```json
{
  "surge_stocks": [
    {
      "stock_code": "000660",
      "stock_name": "SK하이닉스",
      "price": 125000,
      "change_rate": 7.5,
      "volume_ratio": 3.2,
      "detected_at": "2025-10-24T11:30:00"
    }
  ],
  "total_count": 15
}
```

---

### 4. 로그 API (Logs)

#### 로그 조회
```http
GET /api/v1/logs
```

**Query Parameters:**
- `limit` (integer, optional): 조회 개수 (기본: 1000, 최대: 10000)
- `level` (string, optional): 로그 레벨 (`DEBUG` | `INFO` | `WARNING` | `ERROR`)
- `module` (string, optional): 모듈 필터
- `start_time` (string, optional): 시작 시간 (ISO 8601)

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2025-10-24T11:00:00",
    "level": "INFO",
    "module": "trading_engine",
    "message": "자동매매 시작"
  }
]
```

---

#### 로그 생성
```http
POST /api/v1/logs
```

**Request Body:**
```json
{
  "level": "INFO",
  "module": "trading_engine",
  "message": "주문 체결: 005930 10주"
}
```

---

#### 로그 통계
```http
GET /api/v1/logs/stats
```

**Response:**
```json
{
  "total_count": 5000,
  "level_counts": {
    "DEBUG": 1000,
    "INFO": 3500,
    "WARNING": 400,
    "ERROR": 100
  },
  "recent_24h_count": 2000
}
```

---

### 5. Trading Engine 제어 API

#### Engine 상태 조회
```http
GET /api/v1/engine/status
```

**Response:**
```json
{
  "is_running": true,
  "pid": 12345,
  "status": "running"
}
```

---

#### Engine 시작
```http
POST /api/v1/engine/start
```

**Request Body (optional):**
```json
{
  "use_simulation": true,
  "auto_trading": false,
  "strategies": ["ma_crossover", "rsi", "macd"]
}
```

**Response:**
```json
{
  "message": "Trading Engine started successfully",
  "pid": 12345,
  "status": "running"
}
```

---

#### Engine 중지
```http
POST /api/v1/engine/stop
```

**Response:**
```json
{
  "message": "Trading Engine stopped successfully",
  "pid": 12345,
  "status": "stopped"
}
```

---

#### Engine 재시작
```http
POST /api/v1/engine/restart
```

**Response:**
```json
{
  "message": "Trading Engine restarted successfully",
  "pid": 12346,
  "status": "running"
}
```

---

## WebSocket API

### 연결

```javascript
// JavaScript 예시
const ws = new WebSocket('ws://localhost:8000/ws/market');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onerror = (error) => {
  console.error('Error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

### 채널

#### 1. 실시간 시세 (`/ws/market`)

**메시지 형식:**
```json
{
  "event_type": "MARKET_DATA",
  "timestamp": "2025-10-24T11:00:00",
  "data": {
    "stock_code": "005930",
    "price": 72000,
    "change": 1000,
    "change_percent": 1.41,
    "volume": 5000000
  }
}
```

---

#### 2. 주문 체결 (`/ws/orders`)

**메시지 형식:**
```json
{
  "event_type": "ORDER_FILLED",
  "timestamp": "2025-10-24T11:01:00",
  "data": {
    "order_id": 1,
    "stock_code": "005930",
    "quantity": 10,
    "price": 70000,
    "status": "filled"
  }
}
```

---

#### 3. 포지션 업데이트 (`/ws/positions`)

**메시지 형식:**
```json
{
  "event_type": "POSITION_UPDATED",
  "timestamp": "2025-10-24T11:02:00",
  "data": {
    "stock_code": "005930",
    "quantity": 10,
    "avg_price": 70000,
    "current_price": 72000,
    "profit_loss": 20000,
    "profit_loss_percent": 2.86
  }
}
```

---

#### 4. 급등주 알림 (`/ws/surge`)

**메시지 형식:**
```json
{
  "event_type": "SURGE_DETECTED",
  "timestamp": "2025-10-24T11:30:00",
  "data": {
    "stock_code": "000660",
    "stock_name": "SK하이닉스",
    "change_rate": 7.5,
    "volume_ratio": 3.2,
    "price": 125000
  }
}
```

---

## 오류 코드

### HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 422 | Unprocessable Entity | 유효성 검증 실패 |
| 500 | Internal Server Error | 서버 오류 |

### 오류 응답 형식

```json
{
  "detail": "Error message here",
  "status_code": 400
}
```

---

## Rate Limiting

현재 버전에는 Rate Limiting이 적용되지 않습니다. 향후 추가될 예정입니다.

**예정된 제한:**
- REST API: 100 requests/minute
- WebSocket: 1000 messages/minute

---

## 예제 코드

### Python (requests)

```python
import requests

# API 클라이언트
class CleonAIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"
    
    def get_accounts(self):
        response = requests.get(f"{self.api_v1}/account/")
        return response.json()
    
    def create_order(self, account_id, stock_code, stock_name, 
                     order_type, quantity, price=None):
        data = {
            "account_id": account_id,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "order_type": order_type,
            "price_type": "market" if price is None else "limit",
            "quantity": quantity,
            "price": price
        }
        response = requests.post(f"{self.api_v1}/trading/order", json=data)
        return response.json()

# 사용 예시
client = CleonAIClient()
accounts = client.get_accounts()
print(accounts)

order = client.create_order(
    account_id=1,
    stock_code="005930",
    stock_name="삼성전자",
    order_type="buy",
    quantity=10,
    price=70000
)
print(order)
```

---

### Python (WebSocket)

```python
import asyncio
import websockets
import json

async def market_data_stream():
    uri = "ws://localhost:8000/ws/market"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to market data stream")
        
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

# 실행
asyncio.run(market_data_stream())
```

---

## 변경 이력

### v1.0.0 (2025-10-24)
- 초기 API 릴리스
- REST API 30+ 엔드포인트
- WebSocket 4개 채널

---

## 지원

- **문서**: https://github.com/yourusername/cleonai-trading-platform/docs
- **이슈**: https://github.com/yourusername/cleonai-trading-platform/issues
- **이메일**: support@cleonai.com

---

**작성일**: 2025-10-24  
**버전**: 1.0  
**담당자**: CleonAI Development Team

