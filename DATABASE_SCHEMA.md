# 💾 자동매매 시스템 데이터베이스 스키마

## 📋 개요
자동매매 시스템에 최적화된 MongoDB 데이터베이스 스키마 설계 및 구현 가이드입니다.

## 🗄️ 데이터베이스 구조

### 주요 설계 원칙
- **성능 최적화**: 자주 사용되는 쿼리에 최적화된 인덱스 설계
- **확장성**: 향후 데이터 증가를 고려한 샤딩 준비
- **보안성**: 민감한 데이터의 암호화 저장
- **일관성**: 트랜잭션을 통한 데이터 무결성 보장

## 📊 컬렉션 설계

### 1. users (사용자 정보)
```javascript
// 사용자 기본 정보 및 설정
{
  _id: ObjectId("507f1f77bcf86cd799439011"),
  email: "user@example.com",
  passwordHash: "$2b$10$...", // bcrypt 해시
  name: "홍길동",
  phone: "010-1234-5678", // 암호화 저장
  
  // 증권 계좌 정보 (암호화)
  accountInfo: {
    brokerage: "키움증권",
    accountNumber: "1234567890", // 암호화
    accountPassword: "******",   // 암호화
    isConnected: true,
    lastConnectionAt: ISODate("2025-09-22T09:00:00Z")
  },
  
  // 거래 설정
  tradingSettings: {
    isAutoTradingEnabled: true,
    maxDailyLoss: 1000000,      // 일일 최대 손실 한도 (원)
    maxPositionSize: 5000000,   // 단일 포지션 최대 크기 (원)
    riskLevel: 3,               // 위험도 (1-5)
    tradingHours: {
      start: "09:00",
      end: "15:30"
    }
  },
  
  // 알림 설정
  notificationSettings: {
    email: true,
    sms: true,
    push: false,
    tradingSignals: true,
    orderExecution: true,
    dailyReport: true
  },
  
  // 권한 및 구독 정보
  role: "premium", // basic, premium, admin
  permissions: [
    "view:dashboard",
    "place:order", 
    "auto:trading",
    "view:analytics"
  ],
  subscriptionExpiredAt: ISODate("2026-09-22T23:59:59Z"),
  
  // 시스템 필드
  createdAt: ISODate("2025-09-22T00:00:00Z"),
  updatedAt: ISODate("2025-09-22T12:00:00Z"),
  lastLoginAt: ISODate("2025-09-22T08:30:00Z"),
  isActive: true,
  loginAttempts: 0,
  lockedUntil: null
}

// 인덱스
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ "accountInfo.accountNumber": 1 })
db.users.createIndex({ isActive: 1, role: 1 })
```

### 2. stocks (종목 정보)
```javascript
// 주식 종목 마스터 데이터
{
  _id: ObjectId("507f1f77bcf86cd799439012"),
  code: "005930",
  name: "삼성전자",
  market: "KOSPI",
  sector: "반도체",
  industry: "반도체",
  
  // 현재 가격 정보
  currentPrice: 75000,
  changeAmount: 1000,
  changeRate: 1.35,
  volume: 15234567,
  value: 1142597025000,
  
  // 기본 정보
  marketCap: 365000000000000, // 시가총액
  sharesOutstanding: 5969782550, // 발행주식수
  floatingShares: 4480000000, // 유통주식수
  
  // 재무 정보
  financialInfo: {
    per: 12.5,
    pbr: 1.2,
    roe: 9.8,
    eps: 6000,
    bps: 62500,
    dividendYield: 2.1,
    debtRatio: 15.2
  },
  
  // 기술적 지표 (실시간 업데이트)
  technicalIndicators: {
    sma5: 74500,
    sma20: 73800,
    sma60: 72100,
    ema12: 74800,
    ema26: 73200,
    rsi: 65.5,
    stochastic: {
      k: 70.2,
      d: 68.9
    },
    macd: {
      macd: 850,
      signal: 720,
      histogram: 130
    },
    bollingerBands: {
      upper: 76500,
      middle: 74000,
      lower: 71500
    }
  },
  
  // 거래 통계
  tradingStats: {
    averageVolume20: 12500000,
    volatility: 0.25,
    beta: 1.05,
    highPrice52Week: 82000,
    lowPrice52Week: 58000
  },
  
  // 시스템 필드
  isActive: true,
  isTradable: true,
  updatedAt: ISODate("2025-09-22T15:30:00Z"),
  lastTradeAt: ISODate("2025-09-22T15:29:45Z")
}

// 인덱스
db.stocks.createIndex({ code: 1 }, { unique: true })
db.stocks.createIndex({ market: 1, isActive: 1 })
db.stocks.createIndex({ sector: 1 })
db.stocks.createIndex({ "technicalIndicators.rsi": 1 })
db.stocks.createIndex({ currentPrice: 1, volume: -1 })
```

### 3. orders (주문 정보)
```javascript
// 매수/매도 주문 내역
{
  _id: ObjectId("507f1f77bcf86cd799439013"),
  userId: ObjectId("507f1f77bcf86cd799439011"),
  
  // 주문 기본 정보
  stockCode: "005930",
  stockName: "삼성전자",
  orderType: "BUY", // BUY, SELL
  orderMethod: "LIMIT", // MARKET, LIMIT
  
  // 수량 및 가격
  quantity: 100,
  price: 74500,
  totalAmount: 7450000,
  
  // 주문 상태
  status: "FILLED", // PENDING, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED
  filledQuantity: 100,
  remainingQuantity: 0,
  filledPrice: 74500,
  
  // 수수료 및 세금
  commission: 10400, // 0.14%
  tax: 22350, // 매도 시 증권거래세 0.3%
  netAmount: 7417250,
  
  // 전략 정보
  strategyId: ObjectId("507f1f77bcf86cd799439020"),
  strategyName: "이동평균 크로스오버",
  signalStrength: 0.85,
  reason: "SMA20 상향 돌파",
  
  // 키움 API 정보
  kiwoomOrderId: "KW202509220001",
  originalOrderId: null, // 수정 주문의 경우 원주문 ID
  
  // 시간 정보
  createdAt: ISODate("2025-09-22T10:15:30Z"),
  submittedAt: ISODate("2025-09-22T10:15:31Z"),
  filledAt: ISODate("2025-09-22T10:15:35Z"),
  cancelledAt: null,
  
  // 메타 데이터
  isManual: false, // 수동 주문 여부
  clientIp: "192.168.1.100",
  userAgent: "CleonAI-TradingApp/1.0"
}

// 인덱스
db.orders.createIndex({ userId: 1, createdAt: -1 })
db.orders.createIndex({ stockCode: 1, createdAt: -1 })
db.orders.createIndex({ status: 1, orderType: 1 })
db.orders.createIndex({ strategyId: 1 })
db.orders.createIndex({ kiwoomOrderId: 1 }, { unique: true, sparse: true })
```

### 4. positions (보유 포지션)
```javascript
// 현재 보유 중인 주식 포지션
{
  _id: ObjectId("507f1f77bcf86cd799439014"),
  userId: ObjectId("507f1f77bcf86cd799439011"),
  
  // 종목 정보
  stockCode: "005930",
  stockName: "삼성전자",
  
  // 포지션 정보
  quantity: 500, // 보유 수량
  availableQuantity: 500, // 매도 가능 수량
  avgBuyPrice: 72800, // 평균 매수가
  totalCost: 36400000, // 총 매수 금액
  
  // 현재 평가
  currentPrice: 75000,
  currentValue: 37500000,
  unrealizedPnL: 1100000, // 평가 손익
  unrealizedPnLRate: 3.02, // 수익률 (%)
  
  // 매수 내역
  purchaseHistory: [
    {
      orderId: ObjectId("507f1f77bcf86cd799439013"),
      quantity: 200,
      price: 73000,
      date: ISODate("2025-09-20T10:15:30Z")
    },
    {
      orderId: ObjectId("507f1f77bcf86cd799439015"),
      quantity: 300,
      price: 72700,
      date: ISODate("2025-09-21T14:30:15Z")
    }
  ],
  
  // 리스크 관리
  stopLossPrice: 69500, // 손절가
  takeProfitPrice: 80000, // 익절가
  trailingStopEnabled: true,
  trailingStopPercent: 3.0,
  
  // 시간 정보
  firstPurchaseAt: ISODate("2025-09-20T10:15:30Z"),
  lastPurchaseAt: ISODate("2025-09-21T14:30:15Z"),
  updatedAt: ISODate("2025-09-22T15:30:00Z")
}

// 인덱스
db.positions.createIndex({ userId: 1 })
db.positions.createIndex({ stockCode: 1 })
db.positions.createIndex({ userId: 1, stockCode: 1 }, { unique: true })
db.positions.createIndex({ unrealizedPnLRate: -1 })
```

### 5. strategies (매매 전략)
```javascript
// 매매 전략 설정
{
  _id: ObjectId("507f1f77bcf86cd799439020"),
  userId: ObjectId("507f1f77bcf86cd799439011"),
  
  // 전략 기본 정보
  name: "이동평균 크로스오버 전략",
  description: "5일 이동평균이 20일 이동평균을 상향 돌파할 때 매수, 하향 돌파할 때 매도",
  type: "SMA_CROSSOVER",
  category: "TREND_FOLLOWING",
  
  // 매수 조건
  buyConditions: [
    {
      indicator: "SMA_CROSSOVER",
      parameters: {
        shortPeriod: 5,
        longPeriod: 20,
        direction: "UP"
      }
    },
    {
      indicator: "VOLUME",
      parameters: {
        minVolumeRatio: 1.2 // 평균 거래량 대비 20% 이상
      }
    }
  ],
  
  // 매도 조건
  sellConditions: [
    {
      indicator: "SMA_CROSSOVER",
      parameters: {
        shortPeriod: 5,
        longPeriod: 20,
        direction: "DOWN"
      }
    },
    {
      indicator: "STOP_LOSS",
      parameters: {
        percentage: 5.0 // 5% 손절매
      }
    },
    {
      indicator: "TAKE_PROFIT",
      parameters: {
        percentage: 10.0 // 10% 익절매
      }
    }
  ],
  
  // 리스크 관리
  riskManagement: {
    maxPositionSize: 5000000, // 최대 포지션 크기 (원)
    maxPositionRatio: 0.2, // 계좌 대비 최대 20%
    stopLoss: 5.0, // 손절매 (%)
    takeProfit: 10.0, // 익절매 (%)
    trailingStop: true,
    trailingStopPercent: 3.0
  },
  
  // 필터링 조건
  stockFilters: {
    markets: ["KOSPI", "KOSDAQ"],
    excludeSectors: ["건설", "조선"],
    minPrice: 1000,
    maxPrice: 200000,
    minMarketCap: 100000000000, // 1000억 원 이상
    minVolume: 100000 // 최소 일거래량
  },
  
  // 백테스팅 결과
  backtestResults: {
    period: {
      startDate: ISODate("2024-01-01T00:00:00Z"),
      endDate: ISODate("2025-08-31T23:59:59Z")
    },
    performance: {
      totalReturn: 15.5, // 총 수익률 (%)
      annualizedReturn: 12.2, // 연환산 수익률 (%)
      volatility: 18.5, // 변동성 (%)
      sharpeRatio: 0.85,
      maxDrawdown: -12.3, // 최대 낙폭 (%)
      winRate: 62.5, // 승률 (%)
      profitFactor: 1.35
    },
    trades: {
      totalTrades: 48,
      winningTrades: 30,
      losingTrades: 18,
      avgProfit: 3.2, // 평균 수익률 (%)
      avgLoss: -2.1, // 평균 손실률 (%)
      avgHoldingPeriod: 12 // 평균 보유 기간 (일)
    }
  },
  
  // 실거래 성과
  livePerformance: {
    startDate: ISODate("2025-09-01T00:00:00Z"),
    totalTrades: 15,
    winningTrades: 10,
    totalReturn: 5.8,
    realizedPnL: 580000
  },
  
  // 상태 관리
  isActive: true,
  isPublic: false, // 다른 사용자에게 공개 여부
  
  // 시간 정보
  createdAt: ISODate("2025-09-01T00:00:00Z"),
  updatedAt: ISODate("2025-09-20T12:00:00Z"),
  lastUsedAt: ISODate("2025-09-22T10:15:30Z")
}

// 인덱스
db.strategies.createIndex({ userId: 1, isActive: 1 })
db.strategies.createIndex({ type: 1, category: 1 })
db.strategies.createIndex({ "backtestResults.performance.totalReturn": -1 })
db.strategies.createIndex({ isPublic: 1, "livePerformance.totalReturn": -1 })
```

### 6. trading_signals (매매 신호)
```javascript
// 매매 신호 생성 내역
{
  _id: ObjectId("507f1f77bcf86cd799439025"),
  
  // 기본 정보
  stockCode: "005930",
  stockName: "삼성전자",
  userId: ObjectId("507f1f77bcf86cd799439011"),
  strategyId: ObjectId("507f1f77bcf86cd799439020"),
  
  // 신호 정보
  signalType: "BUY", // BUY, SELL, HOLD
  strength: 0.85, // 신호 강도 (0-1)
  confidence: 0.78, // 신뢰도 (0-1)
  
  // 가격 정보
  currentPrice: 74500,
  targetPrice: 79000,
  stopLossPrice: 70700,
  expectedReturn: 6.0, // 예상 수익률 (%)
  
  // 기술적 분석 데이터
  technicalData: {
    sma5: 74200,
    sma20: 72800,
    crossoverPoint: true,
    rsi: 65.5,
    volume: 15234567,
    volumeRatio: 1.25,
    macd: {
      macd: 850,
      signal: 720,
      histogram: 130
    }
  },
  
  // 시장 조건
  marketCondition: {
    trend: "BULLISH", // BULLISH, BEARISH, SIDEWAYS
    volatility: "NORMAL", // LOW, NORMAL, HIGH
    kospiIndex: 2650.5,
    kospiChange: 1.2
  },
  
  // 신호 처리 상태
  status: "EXECUTED", // PENDING, EXECUTED, IGNORED, EXPIRED
  executedOrderId: ObjectId("507f1f77bcf86cd799439013"),
  
  // 메타 데이터
  generatedBy: "ALGORITHM", // ALGORITHM, USER
  algorithm: "SMA_CROSSOVER_V1",
  version: "1.2.3",
  
  // 시간 정보
  createdAt: ISODate("2025-09-22T10:15:25Z"),
  processedAt: ISODate("2025-09-22T10:15:30Z"),
  expiresAt: ISODate("2025-09-22T16:00:00Z")
}

// 인덱스
db.trading_signals.createIndex({ stockCode: 1, createdAt: -1 })
db.trading_signals.createIndex({ userId: 1, status: 1, createdAt: -1 })
db.trading_signals.createIndex({ strategyId: 1, signalType: 1 })
db.trading_signals.createIndex({ createdAt: -1 })
db.trading_signals.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 })
```

### 7. price_history (가격 이력) - 시계열 컬렉션
```javascript
// 주식 가격 시계열 데이터
{
  _id: ObjectId("507f1f77bcf86cd799439030"),
  stockCode: "005930",
  
  // OHLCV 데이터
  timestamp: ISODate("2025-09-22T10:15:00Z"),
  open: 74300,
  high: 74800,
  low: 74100,
  close: 74500,
  volume: 125000,
  value: 9312500000,
  
  // 시간 단위
  timeframe: "1m", // 1m, 5m, 15m, 1h, 1d
  
  // 기술적 지표 (계산된 값)
  indicators: {
    sma5: 74200,
    sma20: 72800,
    ema12: 74350,
    rsi: 65.5,
    macd: 850
  }
}

// 시계열 컬렉션 설정
db.createCollection("price_history", {
  timeseries: {
    timeField: "timestamp",
    metaField: "stockCode",
    granularity: "minutes"
  }
})

// 인덱스
db.price_history.createIndex({ stockCode: 1, timestamp: -1 })
db.price_history.createIndex({ timeframe: 1, timestamp: -1 })
```

### 8. trading_logs (거래 로그)
```javascript
// 시스템 및 거래 로그
{
  _id: ObjectId("507f1f77bcf86cd799439035"),
  
  // 로그 기본 정보
  level: "INFO", // DEBUG, INFO, WARN, ERROR, FATAL
  type: "TRADING", // TRADING, SYSTEM, AUTH, API
  category: "ORDER_EXECUTION",
  
  // 메시지
  message: "매수 주문 체결 완료",
  details: "삼성전자 100주 74,500원에 매수 주문이 체결되었습니다",
  
  // 관련 데이터
  userId: ObjectId("507f1f77bcf86cd799439011"),
  orderId: ObjectId("507f1f77bcf86cd799439013"),
  stockCode: "005930",
  
  // 컨텍스트 데이터
  context: {
    sessionId: "sess_507f1f77bcf86cd799439040",
    requestId: "req_20250922101530_001",
    clientIp: "192.168.1.100",
    userAgent: "CleonAI-TradingEngine/1.0",
    strategyId: ObjectId("507f1f77bcf86cd799439020")
  },
  
  // 성능 메트릭
  metrics: {
    executionTime: 45, // 실행 시간 (ms)
    memoryUsage: 125000000, // 메모리 사용량 (bytes)
    cpuUsage: 12.5 // CPU 사용률 (%)
  },
  
  // 에러 정보 (에러 로그의 경우)
  error: null,
  
  // 태그
  tags: ["trading", "order", "buy", "success"],
  
  // 시간 정보
  timestamp: ISODate("2025-09-22T10:15:35.123Z"),
  serverTime: ISODate("2025-09-22T10:15:35.125Z")
}

// 인덱스
db.trading_logs.createIndex({ timestamp: -1 })
db.trading_logs.createIndex({ level: 1, type: 1, timestamp: -1 })
db.trading_logs.createIndex({ userId: 1, timestamp: -1 })
db.trading_logs.createIndex({ orderId: 1 })
```

### 9. account_snapshots (계좌 스냅샷)
```javascript
// 일별 계좌 현황 스냅샷
{
  _id: ObjectId("507f1f77bcf86cd799439040"),
  userId: ObjectId("507f1f77bcf86cd799439011"),
  
  // 스냅샷 날짜
  snapshotDate: ISODate("2025-09-22T00:00:00Z"),
  
  // 계좌 잔고
  balance: {
    cash: 15000000, // 현금
    totalAssets: 52500000, // 총 자산
    totalStocks: 37500000, // 주식 평가액
    availableCash: 14500000, // 매수 가능 현금
    marginDebt: 0, // 신용 대출 잔액
    netAssets: 52500000 // 순자산
  },
  
  // 손익 현황
  pnl: {
    dailyPnL: 750000, // 당일 손익
    dailyPnLRate: 1.45, // 당일 수익률 (%)
    totalPnL: 2500000, // 총 손익
    totalPnLRate: 5.0, // 총 수익률 (%)
    realizedPnL: 1200000, // 실현 손익
    unrealizedPnL: 1300000 // 평가 손익
  },
  
  // 포지션 요약
  positions: [
    {
      stockCode: "005930",
      stockName: "삼성전자",
      quantity: 500,
      avgPrice: 72800,
      currentPrice: 75000,
      value: 37500000,
      pnl: 1100000,
      pnlRate: 3.02,
      weight: 71.4 // 포트폴리오 비중 (%)
    }
  ],
  
  // 거래 통계
  tradingStats: {
    totalTrades: 25, // 총 거래 횟수
    winningTrades: 18, // 익절 거래
    losingTrades: 7, // 손절 거래
    winRate: 72.0, // 승률 (%)
    avgProfit: 2.5, // 평균 수익률 (%)
    maxDrawdown: -3.2, // 최대 낙폭 (%)
    commission: 156000, // 총 수수료
    tax: 89000 // 총 세금
  },
  
  // 리스크 메트릭
  riskMetrics: {
    portfolioBeta: 1.05,
    sharpeRatio: 1.25,
    volatility: 18.5,
    var95: -1.2, // 95% VaR (%)
    maxPositionWeight: 71.4 // 최대 포지션 비중 (%)
  },
  
  // 시간 정보
  createdAt: ISODate("2025-09-22T15:30:00Z"),
  lastUpdatedAt: ISODate("2025-09-22T15:30:00Z")
}

// 인덱스
db.account_snapshots.createIndex({ userId: 1, snapshotDate: -1 })
db.account_snapshots.createIndex({ snapshotDate: -1 })
```

## 🔧 데이터베이스 초기화 스크립트

### init_database.js
```javascript
// MongoDB 데이터베이스 초기화 스크립트

// 데이터베이스 연결
const { MongoClient } = require('mongodb');
const bcrypt = require('bcryptjs');
const { encrypt } = require('./utils/crypto');

async function initializeDatabase() {
  const client = new MongoClient(process.env.MONGODB_URL);
  await client.connect();
  
  const db = client.db('cleonai_trading');
  
  console.log('🚀 데이터베이스 초기화 시작...');
  
  // 1. 컬렉션 생성 및 인덱스 설정
  await createCollectionsAndIndexes(db);
  
  // 2. 기본 데이터 삽입
  await insertInitialData(db);
  
  // 3. 시계열 컬렉션 설정
  await setupTimeseriesCollections(db);
  
  console.log('✅ 데이터베이스 초기화 완료!');
  
  await client.close();
}

async function createCollectionsAndIndexes(db) {
  console.log('📊 컬렉션 및 인덱스 생성...');
  
  // users 컬렉션 인덱스
  await db.collection('users').createIndexes([
    { key: { email: 1 }, unique: true },
    { key: { 'accountInfo.accountNumber': 1 } },
    { key: { isActive: 1, role: 1 } },
    { key: { createdAt: -1 } }
  ]);
  
  // stocks 컬렉션 인덱스
  await db.collection('stocks').createIndexes([
    { key: { code: 1 }, unique: true },
    { key: { market: 1, isActive: 1 } },
    { key: { sector: 1 } },
    { key: { 'technicalIndicators.rsi': 1 } },
    { key: { currentPrice: 1, volume: -1 } }
  ]);
  
  // orders 컬렉션 인덱스
  await db.collection('orders').createIndexes([
    { key: { userId: 1, createdAt: -1 } },
    { key: { stockCode: 1, createdAt: -1 } },
    { key: { status: 1, orderType: 1 } },
    { key: { strategyId: 1 } },
    { key: { kiwoomOrderId: 1 }, unique: true, sparse: true }
  ]);
  
  // positions 컬렉션 인덱스
  await db.collection('positions').createIndexes([
    { key: { userId: 1 } },
    { key: { stockCode: 1 } },
    { key: { userId: 1, stockCode: 1 }, unique: true },
    { key: { unrealizedPnLRate: -1 } }
  ]);
  
  // strategies 컬렉션 인덱스
  await db.collection('strategies').createIndexes([
    { key: { userId: 1, isActive: 1 } },
    { key: { type: 1, category: 1 } },
    { key: { 'backtestResults.performance.totalReturn': -1 } },
    { key: { isPublic: 1, 'livePerformance.totalReturn': -1 } }
  ]);
  
  // trading_signals 컬렉션 인덱스
  await db.collection('trading_signals').createIndexes([
    { key: { stockCode: 1, createdAt: -1 } },
    { key: { userId: 1, status: 1, createdAt: -1 } },
    { key: { strategyId: 1, signalType: 1 } },
    { key: { createdAt: -1 } },
    { key: { expiresAt: 1 }, expireAfterSeconds: 0 }
  ]);
  
  // trading_logs 컬렉션 인덱스
  await db.collection('trading_logs').createIndexes([
    { key: { timestamp: -1 } },
    { key: { level: 1, type: 1, timestamp: -1 } },
    { key: { userId: 1, timestamp: -1 } },
    { key: { orderId: 1 } }
  ]);
  
  // account_snapshots 컬렉션 인덱스
  await db.collection('account_snapshots').createIndexes([
    { key: { userId: 1, snapshotDate: -1 } },
    { key: { snapshotDate: -1 } }
  ]);
  
  console.log('✅ 인덱스 생성 완료');
}

async function insertInitialData(db) {
  console.log('📝 초기 데이터 삽입...');
  
  // 관리자 계정 생성
  const adminUser = {
    email: 'admin@cleonai.com',
    passwordHash: await bcrypt.hash('admin123!@#', 12),
    name: '시스템 관리자',
    phone: encrypt('010-0000-0000'),
    accountInfo: {
      brokerage: '키움증권',
      accountNumber: encrypt('0000000000'),
      accountPassword: encrypt('0000'),
      isConnected: false,
      lastConnectionAt: new Date()
    },
    tradingSettings: {
      isAutoTradingEnabled: false,
      maxDailyLoss: 10000000,
      maxPositionSize: 50000000,
      riskLevel: 5,
      tradingHours: { start: '09:00', end: '15:30' }
    },
    notificationSettings: {
      email: true, sms: false, push: false,
      tradingSignals: true, orderExecution: true, dailyReport: true
    },
    role: 'admin',
    permissions: [
      'view:dashboard', 'place:order', 'auto:trading',
      'view:analytics', 'admin:users', 'admin:system'
    ],
    subscriptionExpiredAt: new Date('2030-12-31'),
    createdAt: new Date(),
    updatedAt: new Date(),
    lastLoginAt: null,
    isActive: true,
    loginAttempts: 0,
    lockedUntil: null
  };
  
  await db.collection('users').insertOne(adminUser);
  
  // 주요 종목 데이터
  const majorStocks = [
    {
      code: '005930', name: '삼성전자', market: 'KOSPI', sector: '반도체',
      currentPrice: 75000, changeAmount: 1000, changeRate: 1.35,
      volume: 15234567, marketCap: 365000000000000,
      isActive: true, isTradable: true, updatedAt: new Date()
    },
    {
      code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '반도체',
      currentPrice: 125000, changeAmount: -2000, changeRate: -1.57,
      volume: 8945623, marketCap: 91000000000000,
      isActive: true, isTradable: true, updatedAt: new Date()
    },
    {
      code: '035420', name: 'NAVER', market: 'KOSPI', sector: '인터넷',
      currentPrice: 180000, changeAmount: 3500, changeRate: 1.98,
      volume: 1234567, marketCap: 29500000000000,
      isActive: true, isTradable: true, updatedAt: new Date()
    }
  ];
  
  await db.collection('stocks').insertMany(majorStocks);
  
  // 기본 매매 전략
  const defaultStrategy = {
    userId: adminUser._id,
    name: '기본 이동평균 전략',
    description: '5일선과 20일선의 크로스오버를 이용한 기본 전략',
    type: 'SMA_CROSSOVER',
    category: 'TREND_FOLLOWING',
    buyConditions: [
      {
        indicator: 'SMA_CROSSOVER',
        parameters: { shortPeriod: 5, longPeriod: 20, direction: 'UP' }
      }
    ],
    sellConditions: [
      {
        indicator: 'SMA_CROSSOVER',
        parameters: { shortPeriod: 5, longPeriod: 20, direction: 'DOWN' }
      }
    ],
    riskManagement: {
      maxPositionSize: 5000000,
      maxPositionRatio: 0.2,
      stopLoss: 5.0,
      takeProfit: 10.0,
      trailingStop: true,
      trailingStopPercent: 3.0
    },
    isActive: true,
    isPublic: true,
    createdAt: new Date(),
    updatedAt: new Date()
  };
  
  await db.collection('strategies').insertOne(defaultStrategy);
  
  console.log('✅ 초기 데이터 삽입 완료');
}

async function setupTimeseriesCollections(db) {
  console.log('⏰ 시계열 컬렉션 설정...');
  
  // 가격 이력 시계열 컬렉션 생성
  try {
    await db.createCollection('price_history', {
      timeseries: {
        timeField: 'timestamp',
        metaField: 'stockCode',
        granularity: 'minutes'
      }
    });
    
    await db.collection('price_history').createIndexes([
      { key: { stockCode: 1, timestamp: -1 } },
      { key: { timeframe: 1, timestamp: -1 } }
    ]);
    
    console.log('✅ 시계열 컬렉션 설정 완료');
  } catch (error) {
    console.log('⚠️ 시계열 컬렉션이 이미 존재합니다');
  }
}

// 스크립트 실행
if (require.main === module) {
  initializeDatabase().catch(console.error);
}

module.exports = { initializeDatabase };
```

### package.json 스크립트
```json
{
  "scripts": {
    "db:init": "node database/init_database.js",
    "db:seed": "node database/seed_data.js",
    "db:backup": "node database/backup.js",
    "db:restore": "node database/restore.js"
  }
}
```

## 🔒 데이터 보안 설정

### 민감 정보 암호화
```javascript
// utils/crypto.js
const crypto = require('crypto');

const ENCRYPTION_KEY = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');
const ALGORITHM = 'aes-256-gcm';

function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipher(ALGORITHM, ENCRYPTION_KEY);
  
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  const authTag = cipher.getAuthTag();
  
  return {
    encrypted,
    iv: iv.toString('hex'),
    authTag: authTag.toString('hex')
  };
}

function decrypt(encryptedData) {
  const decipher = crypto.createDecipher(ALGORITHM, ENCRYPTION_KEY);
  decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
  
  let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
}

module.exports = { encrypt, decrypt };
```

## 📊 성능 최적화

### 1. 인덱스 전략
- **복합 인덱스**: 자주 함께 사용되는 필드들 조합
- **부분 인덱스**: 조건에 맞는 문서만 인덱싱
- **TTL 인덱스**: 자동으로 만료되는 임시 데이터

### 2. 쿼리 최적화
- **프로젝션**: 필요한 필드만 조회
- **집계 파이프라인**: 복잡한 분석 쿼리 최적화
- **읽기 선호도**: 보조 복제본 활용

### 3. 데이터 아카이빙
- **날짜 기반 파티셔닝**: 오래된 데이터 별도 보관
- **압축**: 사용 빈도가 낮은 데이터 압축 저장

## 💾 백업 및 복구

### 백업 전략
```bash
# 일일 백업 스크립트
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/mongodb"

# 전체 데이터베이스 백업
mongodump --uri="mongodb://localhost:27017/cleonai_trading" \
          --out="$BACKUP_DIR/full_$DATE"

# 중요 컬렉션만 백업
mongodump --uri="mongodb://localhost:27017/cleonai_trading" \
          --collection=users \
          --collection=orders \
          --collection=positions \
          --out="$BACKUP_DIR/critical_$DATE"

# S3에 백업 파일 업로드
aws s3 sync "$BACKUP_DIR" s3://cleonai-backup/mongodb/
```

---

**작성일**: 2025년 9월 22일  
**상태**: 데이터베이스 스키마 설계 완료  
**다음 단계**: 실제 MongoDB 인스턴스 구축 및 초기화

