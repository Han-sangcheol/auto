"""
공유 상수 모듈

Frontend, Backend, Trading Engine에서 공통으로 사용하는 상수를 정의합니다.
"""

# 주문 타입
ORDER_TYPE_BUY = "buy"
ORDER_TYPE_SELL = "sell"

# 가격 타입
PRICE_TYPE_MARKET = "market"
PRICE_TYPE_LIMIT = "limit"

# 주문 상태
ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_FILLED = "filled"
ORDER_STATUS_PARTIALLY_FILLED = "partially_filled"
ORDER_STATUS_CANCELLED = "cancelled"
ORDER_STATUS_REJECTED = "rejected"

# 계좌 타입
ACCOUNT_TYPE_SIMULATION = "simulation"
ACCOUNT_TYPE_REAL = "real"

# 브로커
BROKER_KIWOOM = "kiwoom"
BROKER_MOCK = "mock"

# 전략 타입
STRATEGY_TYPE_MA_CROSS = "ma_cross"
STRATEGY_TYPE_RSI = "rsi"
STRATEGY_TYPE_MACD = "macd"
STRATEGY_TYPE_SURGE = "surge"
STRATEGY_TYPE_MULTI = "multi"

# 급등주 상태
SURGE_STATUS_DETECTED = "detected"
SURGE_STATUS_APPROVED = "approved"
SURGE_STATUS_REJECTED = "rejected"
SURGE_STATUS_EXECUTED = "executed"

# 로그 레벨
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# 이벤트 타입
EVENT_PRICE_UPDATE = "price_update"
EVENT_ORDER_FILLED = "order_filled"
EVENT_POSITION_OPENED = "position_opened"
EVENT_POSITION_CLOSED = "position_closed"
EVENT_SURGE_DETECTED = "surge_detected"
EVENT_STRATEGY_SIGNAL = "strategy_signal"

