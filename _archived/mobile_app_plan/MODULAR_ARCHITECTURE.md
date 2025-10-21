# 🗂️ 기능별 모듈화 아키텍처 설계

## 📋 개요
CleonAI 자동매매 시스템의 유지보수성과 확장성을 극대화하기 위한 기능별 모듈 분리 설계 및 구현 가이드입니다.

## 🎯 모듈화 설계 원칙

### 1. 단일 책임 원칙 (Single Responsibility Principle)
- 각 모듈은 하나의 명확한 책임만을 가짐
- 변경 사유가 하나로 제한됨
- 높은 응집도와 낮은 결합도 유지

### 2. 의존성 역전 원칙 (Dependency Inversion Principle)
- 고수준 모듈이 저수준 모듈에 의존하지 않음
- 추상화에 의존하여 구체적 구현과 분리
- 인터페이스 기반 설계

### 3. 개방-폐쇄 원칙 (Open-Closed Principle)
- 확장에는 열려있고 수정에는 닫혀있음
- 새로운 기능 추가 시 기존 코드 수정 최소화
- 플러그인 형태의 확장 가능

## 🏗️ 모듈 구조 설계

### 전체 모듈 의존성 그래프
```
┌─────────────────┐
│   API Gateway   │ ←─── 외부 요청 진입점
└─────┬───────────┘
      │
┌─────▼───────────┐
│  Core Modules   │ ←─── 핵심 비즈니스 로직
├─────────────────┤
│ • Auth Module   │
│ • Trading Engine│
│ • Market Data   │
│ • Account Mgmt  │
│ • Risk Manager  │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Service Layer   │ ←─── 서비스 계층
├─────────────────┤
│ • Database      │
│ • Cache         │
│ • Notification  │
│ • External APIs │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Infrastructure  │ ←─── 인프라 계층
├─────────────────┤
│ • Logger        │
│ • Config        │
│ • Utils         │
│ • Error Handler │
└─────────────────┘
```

## 📁 상세 모듈 분리 설계

### 1. 인증 모듈 (Authentication Module)

#### 파일 구조
```
modules/auth/
├── index.js              # 모듈 진입점 및 인터페이스 정의
├── auth-controller.js    # HTTP 요청 처리
├── auth-service.js       # 비즈니스 로직
├── auth-middleware.js    # 인증 미들웨어
├── auth-validator.js     # 입력 검증
├── jwt-manager.js        # JWT 토큰 관리
├── password-hasher.js    # 비밀번호 암호화
├── session-manager.js    # 세션 관리
├── models/               # 데이터 모델
│   ├── user.model.js
│   └── session.model.js
├── __tests__/            # 테스트 파일
│   ├── auth-controller.test.js
│   ├── auth-service.test.js
│   └── jwt-manager.test.js
└── README.md             # 모듈 문서
```

#### 모듈 인터페이스 정의 (modules/auth/index.js)
```javascript
/**
 * 🔐 인증 모듈
 * 
 * 주요 기능:
 * - 사용자 로그인/로그아웃
 * - JWT 토큰 발급/검증
 * - 세션 관리
 * - 비밀번호 암호화
 * - 권한 검증
 * 
 * 의존성:
 * - Database Service
 * - Cache Service (Redis)
 * - Logger
 * - Config
 */

const AuthController = require('./auth-controller');
const AuthService = require('./auth-service');
const AuthMiddleware = require('./auth-middleware');
const JWTManager = require('./jwt-manager');

class AuthModule {
  constructor(dependencies) {
    this.db = dependencies.database;
    this.cache = dependencies.cache;
    this.logger = dependencies.logger;
    this.config = dependencies.config;
    
    // 서비스 초기화
    this.jwtManager = new JWTManager(this.config.jwt);
    this.authService = new AuthService({
      database: this.db,
      cache: this.cache,
      jwtManager: this.jwtManager,
      logger: this.logger
    });
    this.authController = new AuthController(this.authService);
    this.authMiddleware = new AuthMiddleware(this.jwtManager, this.cache);
  }

  // 모듈 초기화
  async initialize() {
    this.logger.info('[AuthModule] 인증 모듈 초기화 시작');
    
    // 필요한 초기화 작업 수행
    await this.authService.initialize();
    
    this.logger.info('[AuthModule] 인증 모듈 초기화 완료');
  }

  // HTTP 라우터 반환
  getRoutes() {
    return this.authController.getRoutes();
  }

  // 미들웨어 반환
  getMiddleware() {
    return {
      authenticate: this.authMiddleware.authenticate.bind(this.authMiddleware),
      authorize: this.authMiddleware.authorize.bind(this.authMiddleware),
      refreshToken: this.authMiddleware.refreshToken.bind(this.authMiddleware)
    };
  }

  // 서비스 인스턴스 반환 (다른 모듈에서 사용)
  getService() {
    return this.authService;
  }

  // 모듈 상태 확인
  async healthCheck() {
    return {
      module: 'auth',
      status: 'healthy',
      dependencies: {
        database: await this.db.healthCheck(),
        cache: await this.cache.ping()
      }
    };
  }

  // 모듈 종료
  async shutdown() {
    this.logger.info('[AuthModule] 인증 모듈 종료');
    // 필요한 정리 작업 수행
  }
}

module.exports = AuthModule;
```

#### 인증 서비스 (modules/auth/auth-service.js)
```javascript
/**
 * 🔐 인증 서비스
 * 
 * 비즈니스 로직 처리:
 * - 사용자 인증
 * - 토큰 관리
 * - 세션 관리
 */

const bcrypt = require('bcryptjs');
const { AuthError, ValidationError } = require('../../utils/errors');

class AuthService {
  constructor({ database, cache, jwtManager, logger }) {
    this.db = database;
    this.cache = cache;
    this.jwt = jwtManager;
    this.logger = logger;
  }

  async initialize() {
    // 초기화 로직
    this.logger.info('[AuthService] 서비스 초기화');
  }

  /**
   * 사용자 로그인
   */
  async login(email, password, clientInfo = {}) {
    try {
      this.logger.info('[AuthService] 로그인 시도', { email, ip: clientInfo.ip });

      // 입력 검증
      await this.validateLoginInput(email, password);

      // 사용자 조회
      const user = await this.findUserByEmail(email);
      if (!user) {
        throw new AuthError('이메일 또는 비밀번호가 올바르지 않습니다', 'INVALID_CREDENTIALS');
      }

      // 계정 잠금 확인
      if (user.lockedUntil && user.lockedUntil > new Date()) {
        throw new AuthError('계정이 일시적으로 잠겨있습니다', 'ACCOUNT_LOCKED');
      }

      // 비밀번호 검증
      const isPasswordValid = await bcrypt.compare(password, user.passwordHash);
      if (!isPasswordValid) {
        await this.handleFailedLogin(user._id, clientInfo.ip);
        throw new AuthError('이메일 또는 비밀번호가 올바르지 않습니다', 'INVALID_CREDENTIALS');
      }

      // 성공적인 로그인 처리
      await this.handleSuccessfulLogin(user._id, clientInfo);

      // 토큰 생성
      const tokens = await this.jwt.generateTokenPair({
        userId: user._id,
        email: user.email,
        role: user.role,
        permissions: user.permissions
      });

      // 세션 저장
      await this.saveSession(user._id, tokens.refreshToken, clientInfo);

      // 민감한 정보 제거
      const safeUser = this.sanitizeUser(user);

      this.logger.info('[AuthService] 로그인 성공', { 
        userId: user._id, 
        email: user.email 
      });

      return {
        user: safeUser,
        tokens,
        expiresAt: new Date(Date.now() + 15 * 60 * 1000) // 15분
      };

    } catch (error) {
      this.logger.error('[AuthService] 로그인 실패', { error: error.message, email });
      throw error;
    }
  }

  /**
   * 토큰 갱신
   */
  async refreshToken(refreshToken, clientInfo = {}) {
    try {
      // 토큰 검증
      const decoded = await this.jwt.verifyRefreshToken(refreshToken);
      
      // 세션 확인
      const session = await this.getSession(decoded.userId, refreshToken);
      if (!session) {
        throw new AuthError('유효하지 않은 세션입니다', 'INVALID_SESSION');
      }

      // 사용자 조회
      const user = await this.findUserById(decoded.userId);
      if (!user || !user.isActive) {
        throw new AuthError('사용자를 찾을 수 없습니다', 'USER_NOT_FOUND');
      }

      // 새 토큰 생성
      const newTokens = await this.jwt.generateTokenPair({
        userId: user._id,
        email: user.email,
        role: user.role,
        permissions: user.permissions
      });

      // 세션 업데이트
      await this.updateSession(decoded.userId, refreshToken, newTokens.refreshToken);

      this.logger.info('[AuthService] 토큰 갱신 성공', { userId: user._id });

      return {
        tokens: newTokens,
        expiresAt: new Date(Date.now() + 15 * 60 * 1000)
      };

    } catch (error) {
      this.logger.error('[AuthService] 토큰 갱신 실패', { error: error.message });
      throw error;
    }
  }

  /**
   * 로그아웃
   */
  async logout(userId, refreshToken) {
    try {
      // 세션 삭제
      await this.deleteSession(userId, refreshToken);
      
      // 액세스 토큰을 블랙리스트에 추가 (캐시)
      await this.addToBlacklist(refreshToken);

      this.logger.info('[AuthService] 로그아웃 성공', { userId });

    } catch (error) {
      this.logger.error('[AuthService] 로그아웃 실패', { error: error.message, userId });
      throw error;
    }
  }

  // === Private Methods ===

  async validateLoginInput(email, password) {
    if (!email || !password) {
      throw new ValidationError('이메일과 비밀번호를 입력해주세요');
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new ValidationError('올바른 이메일 형식을 입력해주세요');
    }

    if (password.length < 8) {
      throw new ValidationError('비밀번호는 8자 이상이어야 합니다');
    }
  }

  async findUserByEmail(email) {
    const users = this.db.getDB().collection('users');
    return await users.findOne({ email: email.toLowerCase(), isActive: true });
  }

  async findUserById(userId) {
    const users = this.db.getDB().collection('users');
    return await users.findOne({ _id: userId, isActive: true });
  }

  async handleFailedLogin(userId, ip) {
    const users = this.db.getDB().collection('users');
    
    // 로그인 실패 횟수 증가
    const result = await users.findOneAndUpdate(
      { _id: userId },
      { 
        $inc: { loginAttempts: 1 },
        $set: { lastFailedLoginAt: new Date() }
      },
      { returnDocument: 'after' }
    );

    // 5회 실패 시 계정 잠금 (15분)
    if (result.value && result.value.loginAttempts >= 5) {
      await users.updateOne(
        { _id: userId },
        { 
          $set: { 
            lockedUntil: new Date(Date.now() + 15 * 60 * 1000),
            loginAttempts: 0 
          } 
        }
      );

      this.logger.warn('[AuthService] 계정 잠금', { userId, ip, attempts: result.value.loginAttempts });
    }
  }

  async handleSuccessfulLogin(userId, clientInfo) {
    const users = this.db.getDB().collection('users');
    
    await users.updateOne(
      { _id: userId },
      { 
        $set: { 
          lastLoginAt: new Date(),
          lastLoginIp: clientInfo.ip,
          loginAttempts: 0,
          lockedUntil: null
        } 
      }
    );
  }

  async saveSession(userId, refreshToken, clientInfo) {
    const sessionKey = `session:${userId}:${refreshToken}`;
    const sessionData = {
      userId,
      refreshToken,
      createdAt: new Date(),
      lastAccessAt: new Date(),
      ip: clientInfo.ip,
      userAgent: clientInfo.userAgent
    };

    // 7일 TTL
    await this.cache.setex(sessionKey, 7 * 24 * 60 * 60, JSON.stringify(sessionData));
  }

  async getSession(userId, refreshToken) {
    const sessionKey = `session:${userId}:${refreshToken}`;
    const sessionData = await this.cache.get(sessionKey);
    
    if (sessionData) {
      return JSON.parse(sessionData);
    }
    
    return null;
  }

  async updateSession(userId, oldRefreshToken, newRefreshToken) {
    // 기존 세션 삭제
    await this.deleteSession(userId, oldRefreshToken);
    
    // 새 세션 생성
    const sessionKey = `session:${userId}:${newRefreshToken}`;
    const sessionData = {
      userId,
      refreshToken: newRefreshToken,
      createdAt: new Date(),
      lastAccessAt: new Date()
    };

    await this.cache.setex(sessionKey, 7 * 24 * 60 * 60, JSON.stringify(sessionData));
  }

  async deleteSession(userId, refreshToken) {
    const sessionKey = `session:${userId}:${refreshToken}`;
    await this.cache.del(sessionKey);
  }

  async addToBlacklist(token) {
    const blacklistKey = `blacklist:${token}`;
    // 토큰의 남은 유효시간만큼 TTL 설정
    await this.cache.setex(blacklistKey, 15 * 60, 'true');
  }

  sanitizeUser(user) {
    const { passwordHash, loginAttempts, lockedUntil, ...safeUser } = user;
    return safeUser;
  }
}

module.exports = AuthService;
```

### 2. 자동매매 엔진 모듈 (Trading Engine Module)

#### 파일 구조
```
modules/trading/
├── index.js                    # 모듈 진입점
├── trading-controller.js       # HTTP 컨트롤러
├── trading-engine.js           # 핵심 매매 엔진
├── strategy-manager.js         # 전략 관리자
├── signal-generator.js         # 매매 신호 생성기
├── risk-manager.js             # 리스크 관리자
├── order-processor.js          # 주문 처리기
├── portfolio-manager.js        # 포트폴리오 관리
├── performance-tracker.js      # 성과 추적
├── strategies/                 # 매매 전략들
│   ├── base-strategy.js        # 기본 전략 클래스
│   ├── sma-crossover.js        # 이동평균 크로스오버
│   ├── rsi-strategy.js         # RSI 기반 전략
│   ├── macd-strategy.js        # MACD 전략
│   └── custom-strategy.js      # 커스텀 전략
├── indicators/                 # 기술적 지표
│   ├── sma.js                  # 단순 이동평균
│   ├── ema.js                  # 지수 이동평균
│   ├── rsi.js                  # RSI
│   ├── macd.js                 # MACD
│   └── bollinger-bands.js      # 볼린저 밴드
├── models/
│   ├── strategy.model.js
│   ├── signal.model.js
│   └── trade.model.js
├── __tests__/
└── README.md
```

#### 매매 엔진 핵심 클래스 (modules/trading/trading-engine.js)
```javascript
/**
 * 🤖 자동매매 엔진
 * 
 * 핵심 기능:
 * - 매매 전략 실행
 * - 실시간 신호 처리
 * - 포트폴리오 관리
 * - 리스크 관리
 * - 성과 추적
 */

const EventEmitter = require('events');
const StrategyManager = require('./strategy-manager');
const SignalGenerator = require('./signal-generator');
const RiskManager = require('./risk-manager');
const OrderProcessor = require('./order-processor');
const PortfolioManager = require('./portfolio-manager');
const PerformanceTracker = require('./performance-tracker');

class TradingEngine extends EventEmitter {
  constructor(dependencies) {
    super();
    
    this.db = dependencies.database;
    this.cache = dependencies.cache;
    this.logger = dependencies.logger;
    this.config = dependencies.config;
    this.kiwoomAPI = dependencies.kiwoomAPI;
    
    // 상태 관리
    this.isRunning = false;
    this.activeUsers = new Map();
    this.marketData = new Map();
    
    // 하위 모듈 초기화
    this.strategyManager = new StrategyManager(dependencies);
    this.signalGenerator = new SignalGenerator(dependencies);
    this.riskManager = new RiskManager(dependencies);
    this.orderProcessor = new OrderProcessor(dependencies);
    this.portfolioManager = new PortfolioManager(dependencies);
    this.performanceTracker = new PerformanceTracker(dependencies);
    
    this.setupEventHandlers();
  }

  async initialize() {
    this.logger.info('[TradingEngine] 자동매매 엔진 초기화 시작');
    
    // 하위 모듈 초기화
    await Promise.all([
      this.strategyManager.initialize(),
      this.signalGenerator.initialize(),
      this.riskManager.initialize(),
      this.orderProcessor.initialize(),
      this.portfolioManager.initialize(),
      this.performanceTracker.initialize()
    ]);
    
    // 실시간 데이터 수신 설정
    await this.setupRealTimeData();
    
    // 활성 사용자 로드
    await this.loadActiveUsers();
    
    this.logger.info('[TradingEngine] 자동매매 엔진 초기화 완료');
  }

  /**
   * 사용자별 자동매매 시작
   */
  async startTrading(userId, strategyIds = []) {
    try {
      this.logger.info('[TradingEngine] 자동매매 시작', { userId, strategyIds });

      // 사용자 권한 확인
      await this.validateUserPermissions(userId);

      // 전략 유효성 검사
      const strategies = await this.strategyManager.getStrategies(userId, strategyIds);
      if (strategies.length === 0) {
        throw new Error('활성화된 매매 전략이 없습니다');
      }

      // 리스크 검증
      const riskAssessment = await this.riskManager.assessUserRisk(userId);
      if (!riskAssessment.approved) {
        throw new Error(`리스크 검증 실패: ${riskAssessment.reason}`);
      }

      // 포트폴리오 초기화
      await this.portfolioManager.initializePortfolio(userId);

      // 활성 사용자 등록
      this.activeUsers.set(userId, {
        userId,
        strategies,
        startedAt: new Date(),
        lastSignalAt: null,
        isActive: true,
        performance: {
          totalTrades: 0,
          winningTrades: 0,
          totalPnL: 0,
          currentDrawdown: 0
        }
      });

      // 실시간 신호 생성 시작
      await this.signalGenerator.startSignalGeneration(userId, strategies);

      // 상태 업데이트
      await this.updateTradingStatus(userId, 'RUNNING');

      this.emit('tradingStarted', { userId, strategies });
      
      this.logger.info('[TradingEngine] 자동매매 시작 완료', { userId, strategyCount: strategies.length });

      return {
        success: true,
        message: '자동매매가 시작되었습니다',
        strategies: strategies.map(s => ({
          id: s._id,
          name: s.name,
          type: s.type
        }))
      };

    } catch (error) {
      this.logger.error('[TradingEngine] 자동매매 시작 실패', { userId, error: error.message });
      throw error;
    }
  }

  /**
   * 사용자별 자동매매 중지
   */
  async stopTrading(userId) {
    try {
      this.logger.info('[TradingEngine] 자동매매 중지', { userId });

      if (!this.activeUsers.has(userId)) {
        throw new Error('실행 중인 자동매매가 없습니다');
      }

      // 신호 생성 중지
      await this.signalGenerator.stopSignalGeneration(userId);

      // 미체결 주문 취소 (옵션)
      const pendingOrders = await this.orderProcessor.getPendingOrders(userId);
      if (pendingOrders.length > 0) {
        this.logger.info('[TradingEngine] 미체결 주문 취소', { userId, orderCount: pendingOrders.length });
        await this.orderProcessor.cancelPendingOrders(userId);
      }

      // 최종 성과 계산
      const finalPerformance = await this.performanceTracker.calculateFinalPerformance(userId);

      // 활성 사용자 제거
      this.activeUsers.delete(userId);

      // 상태 업데이트
      await this.updateTradingStatus(userId, 'STOPPED');

      this.emit('tradingStopped', { userId, finalPerformance });
      
      this.logger.info('[TradingEngine] 자동매매 중지 완료', { userId, finalPerformance });

      return {
        success: true,
        message: '자동매매가 중지되었습니다',
        performance: finalPerformance
      };

    } catch (error) {
      this.logger.error('[TradingEngine] 자동매매 중지 실패', { userId, error: error.message });
      throw error;
    }
  }

  /**
   * 매매 신호 처리
   */
  async processSignal(signal) {
    try {
      const { userId, stockCode, signalType, strategy, strength, currentPrice } = signal;

      this.logger.info('[TradingEngine] 매매 신호 처리', { userId, stockCode, signalType, strength });

      // 사용자 활성 상태 확인
      if (!this.activeUsers.has(userId)) {
        this.logger.warn('[TradingEngine] 비활성 사용자 신호 무시', { userId });
        return;
      }

      // 리스크 검증
      const riskCheck = await this.riskManager.validateSignal(signal);
      if (!riskCheck.approved) {
        this.logger.warn('[TradingEngine] 리스크 검증 실패', { userId, reason: riskCheck.reason });
        return;
      }

      // 포트폴리오 제약 확인
      const portfolioCheck = await this.portfolioManager.validatePosition(userId, stockCode, signalType);
      if (!portfolioCheck.approved) {
        this.logger.warn('[TradingEngine] 포트폴리오 제약 위반', { userId, reason: portfolioCheck.reason });
        return;
      }

      // 주문 생성 및 전송
      const orderResult = await this.orderProcessor.processSignal(signal);
      
      if (orderResult.success) {
        // 포트폴리오 업데이트
        await this.portfolioManager.updatePosition(userId, orderResult.order);
        
        // 성과 추적 업데이트
        await this.performanceTracker.recordTrade(userId, orderResult.order);
        
        // 사용자 통계 업데이트
        this.updateUserStats(userId, orderResult.order);
        
        this.emit('signalProcessed', { userId, signal, order: orderResult.order });
        
        this.logger.info('[TradingEngine] 매매 신호 처리 완료', { 
          userId, 
          orderId: orderResult.order._id,
          stockCode,
          signalType 
        });
      }

    } catch (error) {
      this.logger.error('[TradingEngine] 매매 신호 처리 실패', { signal, error: error.message });
      this.emit('signalProcessingError', { signal, error });
    }
  }

  /**
   * 실시간 시세 업데이트 처리
   */
  async updateMarketData(stockCode, priceData) {
    try {
      // 시세 데이터 캐싱
      this.marketData.set(stockCode, {
        ...priceData,
        updatedAt: new Date()
      });

      // Redis에 캐싱 (10초 TTL)
      await this.cache.setex(`price:${stockCode}`, 10, JSON.stringify(priceData));

      // 활성 사용자들에게 신호 생성 요청
      for (const [userId, userData] of this.activeUsers) {
        const relevantStrategies = userData.strategies.filter(strategy => 
          strategy.stockFilters.includes(stockCode) || strategy.stockFilters.length === 0
        );

        if (relevantStrategies.length > 0) {
          await this.signalGenerator.checkSignals(userId, stockCode, priceData, relevantStrategies);
        }
      }

      this.emit('marketDataUpdated', { stockCode, priceData });

    } catch (error) {
      this.logger.error('[TradingEngine] 시세 업데이트 실패', { stockCode, error: error.message });
    }
  }

  // === Private Methods ===

  setupEventHandlers() {
    // 신호 생성기 이벤트
    this.signalGenerator.on('signalGenerated', this.processSignal.bind(this));
    
    // 주문 처리기 이벤트
    this.orderProcessor.on('orderFilled', this.handleOrderFilled.bind(this));
    this.orderProcessor.on('orderCancelled', this.handleOrderCancelled.bind(this));
    
    // 리스크 관리자 이벤트
    this.riskManager.on('riskLimitExceeded', this.handleRiskLimit.bind(this));
    
    // 포트폴리오 관리자 이벤트
    this.portfolioManager.on('positionClosed', this.handlePositionClosed.bind(this));
  }

  async setupRealTimeData() {
    // 키움 API 실시간 데이터 콜백 설정
    if (this.kiwoomAPI) {
      this.kiwoomAPI.setRealDataCallback((data) => {
        this.updateMarketData(data.stock_code, {
          currentPrice: data.current_price,
          changeAmount: data.change_amount,
          changeRate: data.change_rate,
          volume: data.volume,
          timestamp: data.timestamp
        });
      });
    }
  }

  async loadActiveUsers() {
    try {
      const users = this.db.getDB().collection('users');
      const activeUsers = await users.find({
        'tradingSettings.isAutoTradingEnabled': true,
        isActive: true
      }).toArray();

      this.logger.info('[TradingEngine] 활성 사용자 로드', { count: activeUsers.length });

      // 시스템 재시작 시 자동으로 매매 재개하지 않음 (안전성)
      // 사용자가 명시적으로 시작해야 함

    } catch (error) {
      this.logger.error('[TradingEngine] 활성 사용자 로드 실패', { error: error.message });
    }
  }

  async validateUserPermissions(userId) {
    const users = this.db.getDB().collection('users');
    const user = await users.findOne({ _id: userId });
    
    if (!user) {
      throw new Error('사용자를 찾을 수 없습니다');
    }
    
    if (!user.isActive) {
      throw new Error('비활성화된 계정입니다');
    }
    
    if (!user.permissions.includes('auto:trading')) {
      throw new Error('자동매매 권한이 없습니다');
    }
    
    if (!user.tradingSettings.isAutoTradingEnabled) {
      throw new Error('자동매매가 비활성화되어 있습니다');
    }
    
    // 구독 만료 확인
    if (user.subscriptionExpiredAt && user.subscriptionExpiredAt < new Date()) {
      throw new Error('구독이 만료되었습니다');
    }
  }

  async updateTradingStatus(userId, status) {
    const users = this.db.getDB().collection('users');
    await users.updateOne(
      { _id: userId },
      { 
        $set: { 
          'tradingSettings.lastTradingStatus': status,
          'tradingSettings.lastTradingAt': new Date()
        }
      }
    );
  }

  updateUserStats(userId, order) {
    const userData = this.activeUsers.get(userId);
    if (userData) {
      userData.performance.totalTrades += 1;
      userData.lastSignalAt = new Date();
      
      if (order.orderType === 'SELL' && order.pnl > 0) {
        userData.performance.winningTrades += 1;
      }
      
      userData.performance.totalPnL += (order.pnl || 0);
    }
  }

  async handleOrderFilled(orderData) {
    this.logger.info('[TradingEngine] 주문 체결 처리', { orderId: orderData._id });
    this.emit('orderFilled', orderData);
  }

  async handleOrderCancelled(orderData) {
    this.logger.info('[TradingEngine] 주문 취소 처리', { orderId: orderData._id });
    this.emit('orderCancelled', orderData);
  }

  async handleRiskLimit(riskData) {
    const { userId, riskType, message } = riskData;
    this.logger.warn('[TradingEngine] 리스크 한도 초과', { userId, riskType, message });
    
    // 자동매매 일시 중지
    await this.pauseTrading(userId, riskType);
    
    this.emit('riskLimitExceeded', riskData);
  }

  async handlePositionClosed(positionData) {
    this.logger.info('[TradingEngine] 포지션 청산', { userId: positionData.userId, stockCode: positionData.stockCode });
    this.emit('positionClosed', positionData);
  }

  async pauseTrading(userId, reason) {
    if (this.activeUsers.has(userId)) {
      const userData = this.activeUsers.get(userId);
      userData.isActive = false;
      userData.pauseReason = reason;
      userData.pausedAt = new Date();
      
      await this.signalGenerator.pauseSignalGeneration(userId);
      
      this.logger.warn('[TradingEngine] 자동매매 일시 중지', { userId, reason });
    }
  }

  // 외부 인터페이스 메서드들
  getActiveUsers() {
    return Array.from(this.activeUsers.keys());
  }

  getUserStatus(userId) {
    return this.activeUsers.get(userId) || null;
  }

  getMarketData(stockCode) {
    return this.marketData.get(stockCode);
  }

  async getEngineStatus() {
    return {
      isRunning: this.isRunning,
      activeUsers: this.activeUsers.size,
      totalStrategies: await this.strategyManager.getTotalStrategiesCount(),
      marketDataCount: this.marketData.size,
      uptime: process.uptime()
    };
  }

  async shutdown() {
    this.logger.info('[TradingEngine] 자동매매 엔진 종료 시작');
    
    // 모든 활성 사용자 매매 중지
    for (const userId of this.activeUsers.keys()) {
      await this.stopTrading(userId);
    }
    
    // 하위 모듈 종료
    await Promise.all([
      this.strategyManager.shutdown(),
      this.signalGenerator.shutdown(),
      this.riskManager.shutdown(),
      this.orderProcessor.shutdown(),
      this.portfolioManager.shutdown(),
      this.performanceTracker.shutdown()
    ]);
    
    this.isRunning = false;
    this.logger.info('[TradingEngine] 자동매매 엔진 종료 완료');
  }
}

module.exports = TradingEngine;
```

### 3. 시장 데이터 모듈 (Market Data Module)

#### 파일 구조
```
modules/market/
├── index.js                    # 모듈 진입점
├── market-controller.js        # HTTP 컨트롤러
├── data-collector.js           # 데이터 수집기
├── realtime-handler.js         # 실시간 데이터 처리
├── price-calculator.js         # 가격 계산기
├── technical-analyzer.js       # 기술적 분석
├── market-analyzer.js          # 시장 분석
├── data-normalizer.js          # 데이터 정규화
├── websocket-server.js         # WebSocket 서버
├── models/
│   ├── stock.model.js
│   ├── price-history.model.js
│   └── market-status.model.js
├── __tests__/
└── README.md
```

## 🔗 모듈 간 통신 및 의존성 관리

### 의존성 주입 컨테이너 (core/container.js)
```javascript
/**
 * 🏗️ 의존성 주입 컨테이너
 * 
 * 기능:
 * - 모듈 간 의존성 관리
 * - 싱글톤 인스턴스 관리
 * - 순환 의존성 방지
 * - 모듈 생명주기 관리
 */

class DIContainer {
  constructor() {
    this.dependencies = new Map();
    this.singletons = new Map();
    this.initializing = new Set();
  }

  // 의존성 등록
  register(name, factory, options = {}) {
    this.dependencies.set(name, {
      factory,
      singleton: options.singleton !== false,
      dependencies: options.dependencies || []
    });
  }

  // 의존성 해결
  async resolve(name) {
    // 이미 생성된 싱글톤 반환
    if (this.singletons.has(name)) {
      return this.singletons.get(name);
    }

    // 순환 의존성 검사
    if (this.initializing.has(name)) {
      throw new Error(`순환 의존성 감지: ${name}`);
    }

    const dependency = this.dependencies.get(name);
    if (!dependency) {
      throw new Error(`등록되지 않은 의존성: ${name}`);
    }

    try {
      this.initializing.add(name);

      // 하위 의존성 해결
      const resolvedDeps = {};
      for (const depName of dependency.dependencies) {
        resolvedDeps[depName] = await this.resolve(depName);
      }

      // 인스턴스 생성
      const instance = await dependency.factory(resolvedDeps);

      // 싱글톤으로 캐싱
      if (dependency.singleton) {
        this.singletons.set(name, instance);
      }

      return instance;

    } finally {
      this.initializing.delete(name);
    }
  }

  // 모든 모듈 초기화
  async initializeAll() {
    const initPromises = [];
    
    for (const [name, _] of this.dependencies) {
      initPromises.push(this.resolve(name));
    }

    await Promise.all(initPromises);
  }

  // 컨테이너 정리
  async shutdown() {
    for (const [_, instance] of this.singletons) {
      if (instance.shutdown && typeof instance.shutdown === 'function') {
        await instance.shutdown();
      }
    }
    
    this.singletons.clear();
    this.dependencies.clear();
  }
}

module.exports = DIContainer;
```

### 모듈 팩토리 (core/module-factory.js)
```javascript
/**
 * 🏭 모듈 팩토리
 * 
 * 모든 모듈의 생성과 설정을 담당
 */

const DIContainer = require('./container');
const Logger = require('./logger');
const Database = require('./database');
const ConfigManager = require('./config');

// 모듈 임포트
const AuthModule = require('../modules/auth');
const TradingModule = require('../modules/trading');
const MarketModule = require('../modules/market');
const AccountModule = require('../modules/account');
const NotificationModule = require('../modules/notification');

class ModuleFactory {
  constructor() {
    this.container = new DIContainer();
    this.setupDependencies();
  }

  setupDependencies() {
    // 핵심 서비스 등록
    this.container.register('logger', () => Logger, { singleton: true });
    this.container.register('config', () => new ConfigManager(), { singleton: true });
    
    this.container.register('database', async (deps) => {
      const db = new Database();
      await db.connect();
      return db;
    }, { 
      singleton: true,
      dependencies: ['logger', 'config'] 
    });

    this.container.register('cache', async (deps) => {
      return deps.database.getRedis();
    }, {
      singleton: true,
      dependencies: ['database']
    });

    // 비즈니스 모듈 등록
    this.container.register('authModule', async (deps) => {
      const module = new AuthModule(deps);
      await module.initialize();
      return module;
    }, {
      singleton: true,
      dependencies: ['database', 'cache', 'logger', 'config']
    });

    this.container.register('tradingModule', async (deps) => {
      const module = new TradingModule(deps);
      await module.initialize();
      return module;
    }, {
      singleton: true,
      dependencies: ['database', 'cache', 'logger', 'config', 'authModule']
    });

    this.container.register('marketModule', async (deps) => {
      const module = new MarketModule(deps);
      await module.initialize();
      return module;
    }, {
      singleton: true,
      dependencies: ['database', 'cache', 'logger', 'config']
    });

    this.container.register('accountModule', async (deps) => {
      const module = new AccountModule(deps);
      await module.initialize();
      return module;
    }, {
      singleton: true,
      dependencies: ['database', 'cache', 'logger', 'config', 'authModule']
    });

    this.container.register('notificationModule', async (deps) => {
      const module = new NotificationModule(deps);
      await module.initialize();
      return module;
    }, {
      singleton: true,
      dependencies: ['database', 'cache', 'logger', 'config']
    });
  }

  async createAllModules() {
    await this.container.initializeAll();
    return this.container;
  }

  async shutdown() {
    await this.container.shutdown();
  }
}

module.exports = ModuleFactory;
```

## 📊 모듈 성능 모니터링

### 모듈 메트릭 수집기 (utils/metrics-collector.js)
```javascript
/**
 * 📊 모듈 성능 메트릭 수집기
 */

class MetricsCollector {
  constructor() {
    this.metrics = new Map();
    this.timers = new Map();
  }

  // 카운터 증가
  incrementCounter(name, labels = {}) {
    const key = this.createMetricKey(name, labels);
    const current = this.metrics.get(key) || 0;
    this.metrics.set(key, current + 1);
  }

  // 게이지 설정
  setGauge(name, value, labels = {}) {
    const key = this.createMetricKey(name, labels);
    this.metrics.set(key, value);
  }

  // 히스토그램 기록
  recordHistogram(name, value, labels = {}) {
    const key = this.createMetricKey(name, labels);
    const existing = this.metrics.get(key) || [];
    existing.push(value);
    this.metrics.set(key, existing);
  }

  // 타이머 시작
  startTimer(name, labels = {}) {
    const key = this.createMetricKey(name, labels);
    this.timers.set(key, process.hrtime.bigint());
    
    return {
      end: () => {
        const start = this.timers.get(key);
        if (start) {
          const duration = Number(process.hrtime.bigint() - start) / 1000000; // ms
          this.recordHistogram(`${name}_duration_ms`, duration, labels);
          this.timers.delete(key);
          return duration;
        }
        return 0;
      }
    };
  }

  // 메트릭 조회
  getMetrics() {
    const result = {};
    for (const [key, value] of this.metrics) {
      result[key] = Array.isArray(value) ? this.calculateStats(value) : value;
    }
    return result;
  }

  // 메트릭 초기화
  reset() {
    this.metrics.clear();
    this.timers.clear();
  }

  createMetricKey(name, labels) {
    const labelStr = Object.entries(labels)
      .map(([k, v]) => `${k}="${v}"`)
      .join(',');
    return labelStr ? `${name}{${labelStr}}` : name;
  }

  calculateStats(values) {
    if (values.length === 0) return { count: 0 };
    
    values.sort((a, b) => a - b);
    const count = values.length;
    const sum = values.reduce((a, b) => a + b, 0);
    const avg = sum / count;
    const p50 = values[Math.floor(count * 0.5)];
    const p95 = values[Math.floor(count * 0.95)];
    const p99 = values[Math.floor(count * 0.99)];
    
    return {
      count,
      sum,
      avg: Math.round(avg * 100) / 100,
      min: values[0],
      max: values[count - 1],
      p50,
      p95,
      p99
    };
  }
}

// 글로벌 메트릭 수집기
const globalMetrics = new MetricsCollector();

module.exports = { MetricsCollector, globalMetrics };
```

## 🧪 모듈 테스트 전략

### 테스트 유틸리티 (tests/test-utils.js)
```javascript
/**
 * 🧪 테스트 유틸리티
 */

const { MongoMemoryServer } = require('mongodb-memory-server');
const { MongoClient } = require('mongodb');
const redis = require('redis-mock');

class TestEnvironment {
  constructor() {
    this.mongoServer = null;
    this.mongoClient = null;
    this.redisClient = null;
  }

  async setup() {
    // MongoDB 메모리 서버 시작
    this.mongoServer = await MongoMemoryServer.create();
    const mongoUri = this.mongoServer.getUri();
    this.mongoClient = new MongoClient(mongoUri);
    await this.mongoClient.connect();

    // Redis 목업 클라이언트
    this.redisClient = redis.createClient();

    return {
      mongodb: this.mongoClient.db('test'),
      redis: this.redisClient
    };
  }

  async teardown() {
    if (this.mongoClient) {
      await this.mongoClient.close();
    }
    if (this.mongoServer) {
      await this.mongoServer.stop();
    }
    if (this.redisClient) {
      this.redisClient.end(true);
    }
  }

  // 테스트 데이터 생성 헬퍼
  createMockUser(overrides = {}) {
    return {
      _id: new ObjectId(),
      email: 'test@example.com',
      passwordHash: '$2b$12$test',
      name: '테스트 사용자',
      role: 'premium',
      permissions: ['view:dashboard', 'place:order', 'auto:trading'],
      isActive: true,
      createdAt: new Date(),
      ...overrides
    };
  }

  createMockStock(overrides = {}) {
    return {
      code: '005930',
      name: '삼성전자',
      market: 'KOSPI',
      currentPrice: 75000,
      changeAmount: 1000,
      changeRate: 1.35,
      volume: 1000000,
      ...overrides
    };
  }

  createMockOrder(overrides = {}) {
    return {
      _id: new ObjectId(),
      userId: new ObjectId(),
      stockCode: '005930',
      orderType: 'BUY',
      quantity: 100,
      price: 75000,
      status: 'PENDING',
      createdAt: new Date(),
      ...overrides
    };
  }
}

module.exports = TestEnvironment;
```

---

**작성일**: 2025년 9월 22일  
**상태**: 기능별 모듈화 구조 설계 완료  
**다음 단계**: 자동매매 핵심 엔진 구현

