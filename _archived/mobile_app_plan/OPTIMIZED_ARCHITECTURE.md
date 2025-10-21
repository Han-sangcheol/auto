# 🚀 최적화된 모바일 연동 자동매매 시스템 아키텍처

## 📋 프로젝트 개요

### 목표
- Windows 기반 1차 개발 (서버 + 자동매매 기능)
- 향후 모바일 연동이 용이한 확장 가능한 구조
- 기능별 모듈화를 통한 유지보수성 극대화
- 금융급 보안 체계 구축

### 핵심 차별화 요소
- **계층화된 모듈 구조**: 독립적인 기능 모듈들의 조합
- **API-First 설계**: 모바일 앱 연동을 위한 RESTful API 우선 설계
- **실시간 데이터 처리**: WebSocket 기반 실시간 통신
- **확장 가능한 아키텍처**: 마이크로서비스 지향 설계

## 🏗️ 시스템 아키텍처

### 전체 구조도
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   📱 모바일 앱   │    │  🖥️ Windows     │    │  🔄 실시간      │
│   (향후 개발)   │◄──►│   백엔드 서버    │◄──►│  데이터 수집기  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Flutter UI    │    │ • API Gateway   │    │ • 키움 API      │
│ • 실시간 차트    │    │ • 인증/권한     │    │ • 시세 수집     │
│ • 푸시 알림     │    │ • 자동매매 엔진  │    │ • 실시간 처리   │
│ • 설정 관리     │    │ • 데이터베이스  │    │ • 알림 발송     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  🔐 보안 계층   │    │ 💾 데이터 저장   │    │ 📊 분석 엔진    │
│  (인증/암호화)  │    │ (MongoDB+Redis) │    │ (백테스팅)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🗂️ 모듈별 파일 구조

### 1. 핵심 서버 모듈 (Windows 기반)

```
CleonAI-TradingSystem/
├── 📁 core/                          # 핵심 시스템
│   ├── server.js                     # 메인 서버 (Express)
│   ├── config.js                     # 설정 관리
│   ├── database.js                   # DB 연결 관리
│   └── logger.js                     # 로깅 시스템
│
├── 📁 modules/                       # 기능별 모듈
│   ├── 📁 auth/                      # 인증 모듈
│   │   ├── auth-controller.js        # 인증 컨트롤러
│   │   ├── auth-service.js           # 인증 서비스
│   │   └── auth-middleware.js        # 인증 미들웨어
│   │
│   ├── 📁 trading/                   # 자동매매 모듈
│   │   ├── trading-engine.js         # 매매 엔진
│   │   ├── strategy-manager.js       # 전략 관리
│   │   ├── risk-manager.js           # 리스크 관리
│   │   └── order-processor.js        # 주문 처리
│   │
│   ├── 📁 market/                    # 시장 데이터 모듈
│   │   ├── data-collector.js         # 데이터 수집
│   │   ├── realtime-handler.js       # 실시간 처리
│   │   └── market-analyzer.js        # 시장 분석
│   │
│   ├── 📁 account/                   # 계좌 관리 모듈
│   │   ├── account-controller.js     # 계좌 컨트롤러
│   │   ├── balance-service.js        # 잔고 서비스
│   │   └── position-manager.js       # 포지션 관리
│   │
│   └── 📁 notification/              # 알림 모듈
│       ├── notification-service.js   # 알림 서비스
│       ├── email-sender.js           # 이메일 발송
│       └── sms-sender.js             # SMS 발송
│
├── 📁 api/                           # API 라우터
│   ├── routes/                       # API 라우트
│   │   ├── auth-routes.js
│   │   ├── trading-routes.js
│   │   ├── market-routes.js
│   │   └── account-routes.js
│   └── middleware/                   # API 미들웨어
│       ├── cors.js
│       ├── rate-limit.js
│       └── validation.js
│
├── 📁 kiwoom/                        # 키움 API 연동
│   ├── kiwoom-api.py                 # Python API 래퍼
│   ├── kiwoom-bridge.js              # Node.js 브리지
│   └── data-parser.js                # 데이터 파서
│
├── 📁 database/                      # 데이터베이스
│   ├── models/                       # 데이터 모델
│   │   ├── user.js
│   │   ├── stock.js
│   │   ├── order.js
│   │   └── trading-log.js
│   └── migrations/                   # DB 마이그레이션
│
├── 📁 utils/                         # 유틸리티
│   ├── crypto.js                     # 암호화
│   ├── validator.js                  # 검증
│   └── formatter.js                  # 데이터 포맷팅
│
├── 📁 tests/                         # 테스트
│   ├── unit/                         # 단위 테스트
│   ├── integration/                  # 통합 테스트
│   └── e2e/                          # E2E 테스트
│
├── 📁 docs/                          # 문서
│   ├── api-docs.md                   # API 문서
│   ├── development-guide.md          # 개발 가이드
│   └── deployment-guide.md           # 배포 가이드
│
├── package.json                      # Node.js 패키지
├── requirements.txt                  # Python 패키지
├── docker-compose.yml               # Docker 설정
└── README.md                        # 프로젝트 설명
```

### 2. 모바일 앱 구조 (향후 개발)

```
mobile-app/
├── 📁 lib/
│   ├── 📁 core/                      # 핵심 기능
│   │   ├── api/                      # API 통신
│   │   ├── config/                   # 설정
│   │   └── utils/                    # 유틸리티
│   │
│   ├── 📁 features/                  # 기능별 화면
│   │   ├── 📁 auth/                  # 인증
│   │   ├── 📁 dashboard/             # 대시보드
│   │   ├── 📁 trading/               # 매매
│   │   └── 📁 settings/              # 설정
│   │
│   ├── 📁 shared/                    # 공통 컴포넌트
│   │   ├── widgets/                  # 위젯
│   │   └── providers/                # 상태 관리
│   │
│   └── main.dart                     # 앱 진입점
│
├── android/                          # Android 설정
├── ios/                              # iOS 설정
└── pubspec.yaml                      # Flutter 패키지
```

## 💾 데이터베이스 설계

### MongoDB 스키마 설계

#### 1. 사용자 정보 (users)
```javascript
{
  _id: ObjectId,
  email: String,                      // 이메일 (로그인 ID)
  passwordHash: String,               // 암호화된 비밀번호
  name: String,                       // 사용자 이름
  phone: String,                      // 전화번호 (암호화)
  accountInfo: {                      // 증권계좌 정보 (암호화)
    brokerage: String,                // 증권사
    accountNumber: String,            // 계좌번호
    accountPassword: String           // 계좌비밀번호
  },
  settings: {                         // 개인 설정
    tradingEnabled: Boolean,          // 자동매매 활성화
    riskLevel: Number,                // 위험도 (1-5)
    maxDailyLoss: Number,             // 일일 최대 손실액
    notifications: {                  // 알림 설정
      email: Boolean,
      sms: Boolean,
      push: Boolean
    }
  },
  permissions: [String],              // 권한 목록
  createdAt: Date,
  updatedAt: Date,
  lastLoginAt: Date
}
```

#### 2. 주식 정보 (stocks)
```javascript
{
  _id: ObjectId,
  code: String,                       // 종목코드 (예: 005930)
  name: String,                       // 종목명 (예: 삼성전자)
  market: String,                     // 시장 (KOSPI, KOSDAQ)
  sector: String,                     // 업종
  currentPrice: Number,               // 현재가
  changeAmount: Number,               // 전일대비 변동금액
  changeRate: Number,                 // 변동률 (%)
  volume: Number,                     // 거래량
  marketCap: Number,                  // 시가총액
  per: Number,                        // PER
  pbr: Number,                        // PBR
  technicalIndicators: {              // 기술적 지표
    sma20: Number,                    // 20일 이동평균
    sma60: Number,                    // 60일 이동평균
    rsi: Number,                      // RSI
    macd: {
      macd: Number,
      signal: Number,
      histogram: Number
    }
  },
  updatedAt: Date
}
```

#### 3. 주문 정보 (orders)
```javascript
{
  _id: ObjectId,
  userId: ObjectId,                   // 사용자 ID (ref: users)
  stockCode: String,                  // 종목코드
  stockName: String,                  // 종목명
  orderType: String,                  // 주문유형 (BUY, SELL)
  orderMethod: String,                // 주문방법 (MARKET, LIMIT)
  quantity: Number,                   // 주문수량
  price: Number,                      // 주문가격
  totalAmount: Number,                // 총 주문금액
  status: String,                     // 상태 (PENDING, FILLED, CANCELLED, REJECTED)
  filledQuantity: Number,             // 체결수량
  filledPrice: Number,                // 체결가격
  commission: Number,                 // 수수료
  tax: Number,                        // 세금
  strategy: String,                   // 매매전략
  reason: String,                     // 주문 사유
  kiwoomOrderId: String,              // 키움 주문번호
  createdAt: Date,
  filledAt: Date,
  cancelledAt: Date
}
```

#### 4. 포지션 정보 (positions)
```javascript
{
  _id: ObjectId,
  userId: ObjectId,                   // 사용자 ID
  stockCode: String,                  // 종목코드
  stockName: String,                  // 종목명
  quantity: Number,                   // 보유수량
  avgPrice: Number,                   // 평균매수가
  currentPrice: Number,               // 현재가
  totalCost: Number,                  // 총 매수금액
  currentValue: Number,               // 현재 평가금액
  unrealizedPnL: Number,              // 평가손익
  unrealizedPnLRate: Number,          // 평가손익률
  createdAt: Date,
  updatedAt: Date
}
```

#### 5. 매매 전략 (strategies)
```javascript
{
  _id: ObjectId,
  userId: ObjectId,                   // 사용자 ID
  name: String,                       // 전략명
  description: String,                // 전략 설명
  type: String,                       // 전략 유형 (SMA, RSI, MACD, CUSTOM)
  parameters: {                       // 전략 파라미터
    buyConditions: [Object],          // 매수 조건
    sellConditions: [Object],         // 매도 조건
    riskManagement: {                 // 리스크 관리
      stopLoss: Number,               // 손절매 (%)
      takeProfit: Number,             // 익절매 (%)
      maxPosition: Number             // 최대 포지션 크기
    }
  },
  isActive: Boolean,                  // 활성화 여부
  performanceMetrics: {               // 성과 지표
    totalTrades: Number,              // 총 거래 수
    winRate: Number,                  // 승률
    avgProfit: Number,                // 평균 수익률
    maxDrawdown: Number               // 최대 낙폭
  },
  createdAt: Date,
  updatedAt: Date
}
```

#### 6. 거래 로그 (trading_logs)
```javascript
{
  _id: ObjectId,
  userId: ObjectId,                   // 사용자 ID
  type: String,                       // 로그 타입 (ORDER, SIGNAL, ERROR, SYSTEM)
  level: String,                      // 로그 레벨 (INFO, WARNING, ERROR)
  message: String,                    // 로그 메시지
  data: Object,                       // 추가 데이터
  timestamp: Date
}
```

#### 7. 시세 데이터 (price_history) - 시계열 컬렉션
```javascript
{
  _id: ObjectId,
  stockCode: String,                  // 종목코드
  timestamp: Date,                    // 시각
  open: Number,                       // 시가
  high: Number,                       // 고가
  low: Number,                        // 저가
  close: Number,                      // 종가
  volume: Number,                     // 거래량
  timeframe: String                   // 시간단위 (1m, 5m, 1h, 1d)
}
```

### Redis 캐시 설계

```javascript
// 캐시 키 구조
const CACHE_KEYS = {
  // 실시간 주가 (10초 TTL)
  STOCK_PRICE: 'stock:price:{stockCode}',
  
  // 사용자 세션 (30분 TTL)  
  USER_SESSION: 'session:{userId}',
  
  // 매매 신호 (1분 TTL)
  TRADING_SIGNAL: 'signal:{stockCode}:{strategy}',
  
  // 시장 상태 (5분 TTL)
  MARKET_STATUS: 'market:status',
  
  // API 호출 제한 (1시간 TTL)
  API_RATE_LIMIT: 'rate:{userId}:{endpoint}'
};
```

## 🔧 핵심 기능 모듈 설계

### 1. 자동매매 엔진 (trading-engine.js)
```javascript
/**
 * 🤖 자동매매 엔진
 * 
 * 주요 기능:
 * - 매매 전략 실행
 * - 리스크 관리
 * - 주문 처리
 * - 성과 추적
 */

class TradingEngine {
  constructor(userId, strategyId) {
    this.userId = userId;
    this.strategyId = strategyId;
    this.isRunning = false;
    this.positions = new Map();
    this.riskManager = new RiskManager(userId);
  }

  // 매매 시작
  async start() {
    this.isRunning = true;
    logger.info(`자동매매 시작: 사용자 ${this.userId}`);
    
    // 실시간 데이터 구독
    await this.subscribeMarketData();
    
    // 매매 전략 실행
    this.executeStrategy();
  }

  // 매매 신호 처리
  async processSignal(signal) {
    // 리스크 검증
    const riskCheck = await this.riskManager.validateSignal(signal);
    if (!riskCheck.isValid) {
      logger.warn(`리스크 검증 실패: ${riskCheck.reason}`);
      return;
    }

    // 주문 실행
    await this.executeOrder(signal);
  }
}
```

### 2. 실시간 데이터 수집기 (data-collector.js)
```javascript
/**
 * 📊 실시간 데이터 수집기
 * 
 * 주요 기능:
 * - 키움 API를 통한 시세 수집
 * - 데이터 정규화 및 저장
 * - WebSocket을 통한 실시간 전송
 */

class DataCollector {
  constructor() {
    this.kiwoomAPI = new KiwoomAPI();
    this.redis = new Redis();
    this.mongodb = new MongoDB();
  }

  // 실시간 시세 수집
  async collectRealTimeData(stockCodes) {
    for (const stockCode of stockCodes) {
      // 키움 API에서 실시간 데이터 요청
      const priceData = await this.kiwoomAPI.getRealTimePrice(stockCode);
      
      // 데이터 정규화
      const normalizedData = this.normalizeData(priceData);
      
      // Redis 캐시에 저장
      await this.redis.setex(
        `stock:price:${stockCode}`, 
        10, 
        JSON.stringify(normalizedData)
      );
      
      // MongoDB에 이력 저장
      await this.mongodb.collection('price_history').insertOne({
        ...normalizedData,
        timestamp: new Date()
      });
      
      // WebSocket으로 클라이언트에게 전송
      io.emit(`stock_${stockCode}`, normalizedData);
    }
  }
}
```

### 3. API 게이트웨이 (api-gateway.js)
```javascript
/**
 * 🚪 API 게이트웨이
 * 
 * 주요 기능:
 * - 인증 및 권한 검증
 * - 요청 라우팅
 * - 응답 형식 표준화
 * - 에러 처리
 */

class APIGateway {
  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    // 보안 헤더
    this.app.use(helmet());
    
    // CORS 설정
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true
    }));
    
    // Rate Limiting
    this.app.use('/api/', createRateLimit({
      windowMs: 15 * 60 * 1000, // 15분
      max: 1000 // 최대 1000 요청
    }));
    
    // JSON 파싱
    this.app.use(express.json({ limit: '10mb' }));
    
    // 로깅
    this.app.use(morgan('combined'));
  }

  setupRoutes() {
    // 모바일 앱용 API 라우트
    this.app.use('/api/v1/auth', require('./api/routes/auth-routes'));
    this.app.use('/api/v1/trading', require('./api/routes/trading-routes'));
    this.app.use('/api/v1/market', require('./api/routes/market-routes'));
    this.app.use('/api/v1/account', require('./api/routes/account-routes'));
    
    // 에러 핸들러
    this.app.use(this.errorHandler);
  }

  errorHandler(error, req, res, next) {
    logger.error('API 에러:', error);
    
    res.status(error.statusCode || 500).json({
      success: false,
      error: {
        message: error.message,
        code: error.code
      },
      timestamp: new Date().toISOString(),
      requestId: req.id
    });
  }
}
```

## 🔐 보안 강화 방안

### 1. API 보안
- **JWT 토큰 기반 인증**: Access/Refresh 토큰 분리
- **API Rate Limiting**: IP/사용자별 요청 제한
- **입력 값 검증**: Joi 스키마 기반 검증
- **SQL Injection 방지**: Parameterized Query 사용

### 2. 데이터 보안
- **민감정보 암호화**: AES-256-GCM으로 계좌정보 암호화
- **통신 암호화**: HTTPS/WSS 강제 사용
- **데이터 마스킹**: 로그에서 민감정보 제거

### 3. 시스템 보안
- **서버 강화**: Windows Defender, 방화벽 설정
- **접근 제어**: VPN 기반 관리자 접근
- **모니터링**: 실시간 보안 로그 분석

## 📱 모바일 연동 설계

### RESTful API 설계
```javascript
// API 엔드포인트 구조
const API_ENDPOINTS = {
  // 인증
  AUTH: {
    LOGIN: 'POST /api/v1/auth/login',
    LOGOUT: 'POST /api/v1/auth/logout',
    REFRESH: 'POST /api/v1/auth/refresh',
    PROFILE: 'GET /api/v1/auth/profile'
  },
  
  // 계좌
  ACCOUNT: {
    BALANCE: 'GET /api/v1/account/balance',
    POSITIONS: 'GET /api/v1/account/positions',
    HISTORY: 'GET /api/v1/account/history'
  },
  
  // 매매
  TRADING: {
    START: 'POST /api/v1/trading/start',
    STOP: 'POST /api/v1/trading/stop',
    STATUS: 'GET /api/v1/trading/status',
    STRATEGIES: 'GET /api/v1/trading/strategies'
  },
  
  // 시장
  MARKET: {
    STOCKS: 'GET /api/v1/market/stocks',
    PRICE: 'GET /api/v1/market/price/:code',
    CHART: 'GET /api/v1/market/chart/:code'
  }
};
```

### WebSocket 이벤트 설계
```javascript
// 실시간 이벤트
const WS_EVENTS = {
  // 클라이언트 → 서버
  SUBSCRIBE_STOCK: 'subscribe_stock',
  UNSUBSCRIBE_STOCK: 'unsubscribe_stock',
  
  // 서버 → 클라이언트
  STOCK_PRICE_UPDATE: 'stock_price_update',
  TRADING_SIGNAL: 'trading_signal',
  ORDER_UPDATE: 'order_update',
  ACCOUNT_UPDATE: 'account_update'
};
```

## 🚀 배포 및 운영

### Windows 서버 환경
```batch
REM 개발 환경 설정 스크립트
@echo off

echo "=== CleonAI 자동매매 시스템 설치 ==="

echo "1. Node.js 설치 확인..."
node --version
npm --version

echo "2. Python 설치 확인..."
python --version
pip --version

echo "3. MongoDB 설치 및 실행..."
mongod --version
net start MongoDB

echo "4. Redis 설치 및 실행..."
redis-server --version
redis-server --service-start

echo "5. 프로젝트 의존성 설치..."
npm install
pip install -r requirements.txt

echo "6. 환경 변수 설정..."
copy .env.example .env
echo "Please edit .env file with your configurations"

echo "7. 데이터베이스 초기화..."
npm run db:init

echo "=== 설치 완료 ==="
echo "Run 'npm start' to start the server"
```

### Docker 컨테이너화 (선택사항)
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - mongodb
      - redis
    networks:
      - trading-network

  mongodb:
    image: mongo:5.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - trading-network

  redis:
    image: redis:7.0
    ports:
      - "6379:6379"
    networks:
      - trading-network

volumes:
  mongodb_data:

networks:
  trading-network:
    driver: bridge
```

## 📈 성능 최적화

### 1. 데이터베이스 최적화
- **인덱싱**: 자주 조회되는 필드에 복합 인덱스 생성
- **샤딩**: 대용량 시세 데이터 분산 저장
- **캐싱**: Redis를 통한 빈번한 조회 데이터 캐싱

### 2. API 성능 최적화
- **응답 압축**: gzip 압축 적용
- **페이지네이션**: 대량 데이터 조회 시 페이징 처리
- **비동기 처리**: 시간이 오래 걸리는 작업은 Queue 처리

### 3. 실시간 처리 최적화
- **WebSocket 풀링**: 연결 풀 관리
- **이벤트 버퍼링**: 빈번한 이벤트는 배치 처리
- **메모리 관리**: 가비지 컬렉션 최적화

## 💰 예상 비용 및 일정

### 개발 비용 (3개월)
- **개발자 1명**: 800만원 × 3개월 = 2,400만원
- **서버 및 인프라**: 150만원
- **도구 및 라이센스**: 100만원
- **총 개발비**: **2,650만원**

### 운영 비용 (월간)
- **Windows 서버**: 50만원/월
- **데이터베이스**: 30만원/월
- **CDN 및 보안**: 20만원/월
- **기타 운영비**: 15만원/월
- **총 운영비**: **115만원/월**

### 개발 일정 (16주)
- **Week 1-2**: 환경 구축 및 기본 구조 설계
- **Week 3-6**: 키움 API 연동 및 데이터 수집
- **Week 7-10**: 자동매매 엔진 개발
- **Week 11-12**: API 서버 및 보안 구현
- **Week 13-14**: 통합 테스트 및 최적화
- **Week 15-16**: 배포 및 문서화

---

**작성일**: 2025년 9월 22일  
**상태**: 아키텍처 설계 완료  
**다음 단계**: 데이터베이스 스키마 구현 시작


