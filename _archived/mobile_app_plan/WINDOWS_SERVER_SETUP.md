# 🪟 Windows 기반 자동매매 서버 구축 가이드

## 📋 개요
Windows 환경에서 자동매매 시스템을 구축하기 위한 완성도 높은 개발 환경 설정 및 서버 구조 설계 가이드입니다.

## 🎯 Windows 환경 선택 이유
- **키움 API 호환성**: 키움증권 OpenAPI는 Windows 전용 COM 인터페이스
- **안정성**: Windows Server 2022의 향상된 안정성과 보안
- **관리 편의성**: GUI 기반 서버 관리 및 모니터링
- **개발 효율성**: Visual Studio Code와 Windows 개발 도구 활용

## 🏗️ 서버 아키텍처 설계

### 시스템 구성도
```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Server 2022                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Node.js       │   Python 3.11   │   MongoDB Community     │
│   (Express API) │   (키움 API)     │   (데이터 저장)         │
├─────────────────┼─────────────────┼─────────────────────────┤
│   Redis         │   PM2           │   Windows Services      │
│   (캐싱)        │   (프로세스 관리) │   (서비스 등록)         │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 포트 할당 계획
```
- 3000: Node.js API Server (HTTP)
- 3001: WebSocket Server (실시간 통신)
- 27017: MongoDB Database
- 6379: Redis Cache
- 8080: 관리자 웹 인터페이스
- 9000: 키움 API Bridge (Python)
```

## 💻 개발 환경 구축

### 1. 기본 소프트웨어 설치

#### Node.js 설치 (LTS 버전)
```powershell
# Chocolatey를 통한 설치 (권장)
Set-ExecutionPolicy Bypass -Scope Process -Force; 
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; 
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Node.js 설치
choco install nodejs -y

# 설치 확인
node --version
npm --version
```

#### Python 3.11 설치
```powershell
# Python 3.11 설치
choco install python --version=3.11.0 -y

# pip 업그레이드
python -m pip install --upgrade pip

# 가상환경 생성
python -m venv venv
venv\Scripts\activate

# 설치 확인
python --version
pip --version
```

#### MongoDB Community 설치
```powershell
# MongoDB 설치
choco install mongodb -y

# MongoDB Compass (GUI 도구) 설치
choco install mongodb-compass -y

# 서비스 시작
net start MongoDB

# 연결 테스트
mongo --eval "db.adminCommand('ismaster')"
```

#### Redis 설치 (Windows 포트)
```powershell
# Redis Windows 버전 설치
choco install redis-64 -y

# 서비스 시작
redis-server --service-install
redis-server --service-start

# 연결 테스트
redis-cli ping
```

### 2. 프로젝트 구조 생성

#### 프로젝트 디렉토리 생성 스크립트
```powershell
# setup-project.ps1
Write-Host "🚀 CleonAI 자동매매 시스템 프로젝트 생성" -ForegroundColor Green

# 메인 프로젝트 디렉토리 생성
New-Item -ItemType Directory -Path "C:\CleonAI-Trading" -Force
Set-Location "C:\CleonAI-Trading"

# 프로젝트 구조 생성
$directories = @(
    "core",
    "modules\auth",
    "modules\trading",
    "modules\market",
    "modules\account", 
    "modules\notification",
    "api\routes",
    "api\middleware",
    "kiwoom",
    "database\models",
    "database\migrations",
    "utils",
    "tests\unit",
    "tests\integration",
    "tests\e2e",
    "docs",
    "logs",
    "config",
    "scripts",
    "public"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force
    Write-Host "✅ 디렉토리 생성: $dir" -ForegroundColor Yellow
}

Write-Host "🎉 프로젝트 구조 생성 완료!" -ForegroundColor Green
```

### 3. 환경 설정 파일

#### .env 설정 파일
```bash
# .env
# 서버 설정
NODE_ENV=development
PORT=3000
WEBSOCKET_PORT=3001

# 데이터베이스 설정
MONGODB_URL=mongodb://localhost:27017/cleonai_trading
REDIS_URL=redis://localhost:6379

# 보안 설정
JWT_ACCESS_SECRET=your-super-secret-access-key-here-min-32-chars
JWT_REFRESH_SECRET=your-super-secret-refresh-key-here-min-32-chars
ENCRYPTION_KEY=your-32-byte-hex-encryption-key-here

# 키움 API 설정
KIWOOM_USER_ID=your_kiwoom_user_id
KIWOOM_USER_PASSWORD=your_kiwoom_password
KIWOOM_CERT_PASSWORD=your_cert_password
KIWOOM_ACCOUNT_NUMBER=your_account_number
KIWOOM_ACCOUNT_PASSWORD=your_account_password

# 로깅 설정
LOG_LEVEL=info
LOG_FILE_PATH=./logs/trading.log

# 알림 설정
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password

SMS_API_KEY=your_sms_api_key
SMS_API_SECRET=your_sms_api_secret

# 외부 서비스
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
RATE_LIMIT_WINDOW=900000
RATE_LIMIT_MAX=100

# Windows 서비스 설정
SERVICE_NAME=CleonAI-Trading-Service
SERVICE_DISPLAY_NAME=CleonAI 자동매매 서비스
```

#### config/development.json
```json
{
  "server": {
    "host": "localhost",
    "port": 3000,
    "websocketPort": 3001,
    "timeout": 30000
  },
  "database": {
    "mongodb": {
      "url": "mongodb://localhost:27017/cleonai_trading",
      "options": {
        "maxPoolSize": 10,
        "serverSelectionTimeoutMS": 5000,
        "socketTimeoutMS": 45000
      }
    },
    "redis": {
      "url": "redis://localhost:6379",
      "options": {
        "retryDelayOnFailover": 100,
        "maxRetriesPerRequest": 3
      }
    }
  },
  "trading": {
    "maxPositions": 10,
    "maxDailyLoss": 5000000,
    "tradingHours": {
      "start": "09:00",
      "end": "15:30"
    },
    "cooldownPeriod": 300000
  },
  "security": {
    "tokenExpiry": {
      "access": "15m",
      "refresh": "7d"
    },
    "rateLimiting": {
      "windowMs": 900000,
      "maxRequests": 1000
    }
  },
  "logging": {
    "level": "info",
    "maxFiles": 10,
    "maxSize": "10m"
  }
}
```

## 🔧 핵심 서버 모듈 구현

### 1. 메인 서버 (core/server.js)
```javascript
/**
 * 🚀 CleonAI 자동매매 시스템 메인 서버
 * 
 * 기능:
 * - Express API 서버 구동
 * - WebSocket 실시간 통신
 * - 미들웨어 설정
 * - 에러 핸들링
 * - graceful shutdown
 */

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');

const config = require('./config');
const logger = require('./logger');
const database = require('./database');
const authRoutes = require('../api/routes/auth-routes');
const tradingRoutes = require('../api/routes/trading-routes');
const marketRoutes = require('../api/routes/market-routes');
const accountRoutes = require('../api/routes/account-routes');

class TradingServer {
  constructor() {
    this.app = express();
    this.server = http.createServer(this.app);
    this.io = new Server(this.server, {
      cors: {
        origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
        methods: ['GET', 'POST']
      }
    });
    this.port = process.env.PORT || 3000;
  }

  async initialize() {
    logger.info('🚀 서버 초기화 시작...');
    
    // 데이터베이스 연결
    await this.connectDatabase();
    
    // 미들웨어 설정
    this.setupMiddleware();
    
    // API 라우트 설정
    this.setupRoutes();
    
    // WebSocket 설정
    this.setupWebSocket();
    
    // 에러 핸들링
    this.setupErrorHandling();
    
    // Graceful shutdown 설정
    this.setupGracefulShutdown();
    
    logger.info('✅ 서버 초기화 완료');
  }

  async connectDatabase() {
    try {
      await database.connect();
      logger.info('✅ 데이터베이스 연결 성공');
    } catch (error) {
      logger.error('❌ 데이터베이스 연결 실패:', error);
      process.exit(1);
    }
  }

  setupMiddleware() {
    // 보안 헤더
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"]
        }
      }
    }));

    // CORS 설정
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    }));

    // 압축
    this.app.use(compression());

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15분
      max: 1000, // 최대 1000 요청
      message: {
        error: '요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.',
        retryAfter: '15분'
      },
      standardHeaders: true,
      legacyHeaders: false
    });
    this.app.use('/api/', limiter);

    // JSON 파싱
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // 요청 로깅
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        requestId: req.id
      });
      next();
    });

    logger.info('✅ 미들웨어 설정 완료');
  }

  setupRoutes() {
    // 헬스체크
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: require('../package.json').version
      });
    });

    // API 라우트
    this.app.use('/api/v1/auth', authRoutes);
    this.app.use('/api/v1/trading', tradingRoutes);
    this.app.use('/api/v1/market', marketRoutes);
    this.app.use('/api/v1/account', accountRoutes);

    // 정적 파일 서빙
    this.app.use('/static', express.static('public'));

    // 404 처리
    this.app.use('*', (req, res) => {
      res.status(404).json({
        success: false,
        error: {
          message: '요청하신 리소스를 찾을 수 없습니다',
          code: 'NOT_FOUND',
          path: req.originalUrl
        }
      });
    });

    logger.info('✅ API 라우트 설정 완료');
  }

  setupWebSocket() {
    this.io.use((socket, next) => {
      // WebSocket 인증
      const token = socket.handshake.auth.token;
      if (!token) {
        return next(new Error('인증 토큰이 필요합니다'));
      }
      // JWT 검증 로직...
      next();
    });

    this.io.on('connection', (socket) => {
      logger.info(`클라이언트 연결: ${socket.id}`);

      socket.on('subscribe', (data) => {
        const { stockCodes } = data;
        stockCodes.forEach(code => {
          socket.join(`stock_${code}`);
        });
        logger.info(`주식 구독: ${stockCodes.join(', ')}`);
      });

      socket.on('unsubscribe', (data) => {
        const { stockCodes } = data;
        stockCodes.forEach(code => {
          socket.leave(`stock_${code}`);
        });
        logger.info(`주식 구독 해제: ${stockCodes.join(', ')}`);
      });

      socket.on('disconnect', () => {
        logger.info(`클라이언트 연결 해제: ${socket.id}`);
      });
    });

    logger.info('✅ WebSocket 설정 완료');
  }

  setupErrorHandling() {
    // 일반 에러 핸들러
    this.app.use((error, req, res, next) => {
      logger.error('API 에러:', error);

      // 개발환경에서만 스택 트레이스 포함
      const isDevelopment = process.env.NODE_ENV === 'development';
      
      res.status(error.statusCode || 500).json({
        success: false,
        error: {
          message: error.message || '서버 내부 오류가 발생했습니다',
          code: error.code || 'INTERNAL_SERVER_ERROR',
          ...(isDevelopment && { stack: error.stack })
        },
        timestamp: new Date().toISOString(),
        requestId: req.id
      });
    });

    // 처리되지 않은 Promise 거부
    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
    });

    // 처리되지 않은 예외
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught Exception:', error);
      // 안전한 종료
      this.shutdown();
    });

    logger.info('✅ 에러 핸들링 설정 완료');
  }

  setupGracefulShutdown() {
    const shutdown = async (signal) => {
      logger.info(`${signal} 신호 수신. 서버 종료 시작...`);
      
      this.server.close(async () => {
        logger.info('HTTP 서버 종료');
        
        try {
          await database.close();
          logger.info('데이터베이스 연결 종료');
          
          logger.info('서버 종료 완료');
          process.exit(0);
        } catch (error) {
          logger.error('종료 중 오류:', error);
          process.exit(1);
        }
      });

      // 30초 후 강제 종료
      setTimeout(() => {
        logger.error('강제 종료');
        process.exit(1);
      }, 30000);
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));
  }

  async start() {
    await this.initialize();
    
    this.server.listen(this.port, () => {
      logger.info(`🚀 서버가 포트 ${this.port}에서 실행중입니다`);
      logger.info(`📊 Health check: http://localhost:${this.port}/health`);
      logger.info(`📡 WebSocket: ws://localhost:${this.port}`);
    });
  }

  async shutdown() {
    logger.info('서버 종료 시작...');
    
    if (this.server) {
      this.server.close();
    }
    
    await database.close();
    process.exit(0);
  }
}

module.exports = TradingServer;

// 직접 실행 시
if (require.main === module) {
  const server = new TradingServer();
  server.start().catch((error) => {
    console.error('서버 시작 실패:', error);
    process.exit(1);
  });
}
```

### 2. 로거 설정 (core/logger.js)
```javascript
/**
 * 📝 로깅 시스템
 * 
 * 기능:
 * - 파일 기반 로깅 (회전)
 * - 콘솔 출력
 * - 구조화된 로그 포맷
 * - 에러 추적
 */

const winston = require('winston');
const path = require('path');

// 로그 디렉토리 생성
const logDir = path.join(process.cwd(), 'logs');
require('fs').mkdirSync(logDir, { recursive: true });

// 커스텀 포맷 정의
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss.SSS'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.prettyPrint()
);

// 콘솔용 포맷
const consoleFormat = winston.format.combine(
  winston.format.colorize({ all: true }),
  winston.format.timestamp({
    format: 'HH:mm:ss'
  }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let msg = `${timestamp} [${level}]: ${message}`;
    
    if (Object.keys(meta).length > 0) {
      msg += `\n${JSON.stringify(meta, null, 2)}`;
    }
    
    return msg;
  })
);

// 로거 생성
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: {
    service: 'cleonai-trading',
    version: require('../package.json').version,
    environment: process.env.NODE_ENV
  },
  transports: [
    // 에러 로그 파일
    new winston.transports.File({
      filename: path.join(logDir, 'error.log'),
      level: 'error',
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    }),

    // 전체 로그 파일
    new winston.transports.File({
      filename: path.join(logDir, 'combined.log'),
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 10,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    }),

    // 거래 로그 파일 (별도)
    new winston.transports.File({
      filename: path.join(logDir, 'trading.log'),
      level: 'info',
      maxsize: 50 * 1024 * 1024, // 50MB
      maxFiles: 20,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json(),
        winston.format((info) => {
          // 거래 관련 로그만 필터링
          return info.category === 'trading' ? info : false;
        })()
      )
    })
  ],
  // 예외 처리
  exceptionHandlers: [
    new winston.transports.File({
      filename: path.join(logDir, 'exceptions.log'),
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    })
  ],
  rejectionHandlers: [
    new winston.transports.File({
      filename: path.join(logDir, 'rejections.log'),
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    })
  ]
});

// 개발환경에서는 콘솔에도 출력
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: consoleFormat,
    level: 'debug'
  }));
}

// 거래 전용 로거 메서드 추가
logger.trading = (message, data = {}) => {
  logger.info(message, {
    category: 'trading',
    ...data
  });
};

// 성능 측정 헬퍼
logger.profile = (name) => {
  const start = Date.now();
  return {
    end: () => {
      const duration = Date.now() - start;
      logger.info(`성능 측정: ${name}`, {
        category: 'performance',
        duration: `${duration}ms`
      });
    }
  };
};

module.exports = logger;
```

### 3. 데이터베이스 연결 (core/database.js)
```javascript
/**
 * 💾 데이터베이스 연결 관리
 * 
 * 기능:
 * - MongoDB 연결 관리
 * - Redis 연결 관리
 * - 연결 풀 관리
 * - 자동 재연결
 */

const { MongoClient } = require('mongodb');
const redis = require('redis');
const logger = require('./logger');

class DatabaseManager {
  constructor() {
    this.mongodb = null;
    this.redisClient = null;
    this.isConnected = false;
  }

  async connect() {
    await Promise.all([
      this.connectMongoDB(),
      this.connectRedis()
    ]);
    
    this.isConnected = true;
    logger.info('✅ 모든 데이터베이스 연결 완료');
  }

  async connectMongoDB() {
    try {
      const mongoUrl = process.env.MONGODB_URL || 'mongodb://localhost:27017/cleonai_trading';
      
      this.mongodb = new MongoClient(mongoUrl, {
        maxPoolSize: 10,
        serverSelectionTimeoutMS: 5000,
        socketTimeoutMS: 45000,
        maxIdleTimeMS: 30000,
        minPoolSize: 2
      });

      await this.mongodb.connect();
      
      // 연결 확인
      await this.mongodb.db().admin().ping();
      
      logger.info('✅ MongoDB 연결 성공');

      // 연결 이벤트 리스너
      this.mongodb.on('connectionPoolCreated', () => {
        logger.info('MongoDB 연결 풀 생성됨');
      });

      this.mongodb.on('connectionPoolClosed', () => {
        logger.warn('MongoDB 연결 풀 종료됨');
      });

    } catch (error) {
      logger.error('❌ MongoDB 연결 실패:', error);
      throw error;
    }
  }

  async connectRedis() {
    try {
      const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
      
      this.redisClient = redis.createClient({
        url: redisUrl,
        socket: {
          reconnectStrategy: (retries) => {
            logger.warn(`Redis 재연결 시도 #${retries}`);
            return Math.min(retries * 100, 3000);
          }
        }
      });

      // 에러 이벤트 리스너
      this.redisClient.on('error', (error) => {
        logger.error('Redis 에러:', error);
      });

      this.redisClient.on('connect', () => {
        logger.info('Redis 연결 시작');
      });

      this.redisClient.on('ready', () => {
        logger.info('✅ Redis 연결 완료');
      });

      this.redisClient.on('reconnecting', () => {
        logger.warn('Redis 재연결 중...');
      });

      await this.redisClient.connect();
      
      // 연결 테스트
      await this.redisClient.ping();
      
    } catch (error) {
      logger.error('❌ Redis 연결 실패:', error);
      throw error;
    }
  }

  // MongoDB 데이터베이스 인스턴스 반환
  getDB(name = 'cleonai_trading') {
    if (!this.mongodb) {
      throw new Error('MongoDB가 연결되지 않았습니다');
    }
    return this.mongodb.db(name);
  }

  // Redis 클라이언트 반환
  getRedis() {
    if (!this.redisClient) {
      throw new Error('Redis가 연결되지 않았습니다');
    }
    return this.redisClient;
  }

  // 연결 상태 확인
  isHealthy() {
    return this.isConnected && this.mongodb && this.redisClient?.isReady;
  }

  // 연결 종료
  async close() {
    const closePromises = [];

    if (this.mongodb) {
      closePromises.push(
        this.mongodb.close().then(() => {
          logger.info('MongoDB 연결 종료');
        })
      );
    }

    if (this.redisClient) {
      closePromises.push(
        this.redisClient.quit().then(() => {
          logger.info('Redis 연결 종료');
        })
      );
    }

    await Promise.all(closePromises);
    this.isConnected = false;
  }

  // 헬스체크
  async healthCheck() {
    const health = {
      mongodb: false,
      redis: false,
      overall: false
    };

    try {
      if (this.mongodb) {
        await this.mongodb.db().admin().ping();
        health.mongodb = true;
      }
    } catch (error) {
      logger.error('MongoDB 헬스체크 실패:', error);
    }

    try {
      if (this.redisClient?.isReady) {
        await this.redisClient.ping();
        health.redis = true;
      }
    } catch (error) {
      logger.error('Redis 헬스체크 실패:', error);
    }

    health.overall = health.mongodb && health.redis;
    return health;
  }
}

// 싱글톤 인스턴스 생성
const databaseManager = new DatabaseManager();

module.exports = databaseManager;
```

## 🛠️ 키움 API 연동 모듈

### Python 기반 키움 API 래퍼 (kiwoom/kiwoom_api.py)
```python
"""
🔌 키움 Open API Plus 연동 모듈

주요 기능:
- 로그인 및 인증
- 실시간 시세 수신
- 주문 처리 (매수/매도)
- 계좌 정보 조회
- 잔고 및 보유 종목 조회
"""

import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable

from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer, pyqtSignal, QObject

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/kiwoom_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class KiwoomAPI(QAxWidget):
    """키움증권 Open API Plus 연동 클래스"""
    
    def __init__(self):
        super().__init__()
        
        # 키움 API 인스턴스 생성
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 이벤트 연결
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        self.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        
        # 상태 변수
        self.connected = False
        self.account_list = []
        self.login_event_loop = QEventLoop()
        
        # 콜백 함수들
        self.real_data_callback = None
        self.chejan_callback = None
        
        # TR 요청 관리
        self.tr_event_loop = QEventLoop()
        self.tr_data = {}
        
        logger.info("키움 API 초기화 완료")

    def login(self) -> bool:
        """키움증권 로그인"""
        try:
            logger.info("키움증권 로그인 시작...")
            
            # 로그인 요청
            ret = self.dynamicCall("CommConnect()")
            if ret != 0:
                logger.error(f"로그인 요청 실패: {ret}")
                return False
            
            # 로그인 완료까지 대기
            self.login_event_loop.exec_()
            
            if self.connected:
                # 계좌 정보 조회
                accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO").split(';')[:-1]
                self.account_list = accounts
                
                logger.info(f"로그인 성공. 계좌 목록: {accounts}")
                return True
            else:
                logger.error("로그인 실패")
                return False
                
        except Exception as e:
            logger.error(f"로그인 중 오류: {e}")
            return False

    def _on_event_connect(self, err_code):
        """로그인 결과 이벤트 핸들러"""
        if err_code == 0:
            self.connected = True
            logger.info("키움증권 로그인 성공")
        else:
            self.connected = False
            logger.error(f"키움증권 로그인 실패: {err_code}")
        
        self.login_event_loop.exit()

    def get_stock_price(self, stock_code: str) -> Dict:
        """현재 주가 조회"""
        try:
            self.tr_data = {}
            
            # TR 요청 설정
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
            
            # TR 요청
            ret = self.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "주식기본정보요청", "opt10001", 0, "0101"
            )
            
            if ret != 0:
                logger.error(f"주가 조회 요청 실패: {ret}")
                return {}
            
            # 응답 대기
            self.tr_event_loop.exec_()
            
            return self.tr_data.get('opt10001', {})
            
        except Exception as e:
            logger.error(f"주가 조회 중 오류: {e}")
            return {}

    def send_order(self, order_type: str, stock_code: str, quantity: int, 
                   price: int, account: str) -> str:
        """주문 전송"""
        try:
            # 주문 유형 변환
            order_type_map = {
                'BUY': 1,   # 신규매수
                'SELL': 2,  # 신규매도
                'CANCEL': 3, # 매수취소
                'MODIFY': 5  # 매수정정
            }
            
            order_type_code = order_type_map.get(order_type, 1)
            hoga_type = "03" if price == 0 else "00"  # 시장가/지정가
            
            # 주문 전송
            ret = self.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                "주식주문",     # 사용자 구분명
                "0101",        # 화면번호
                account,       # 계좌번호
                order_type_code,  # 주문유형
                stock_code,    # 종목코드
                quantity,      # 주문수량
                price,         # 주문가격
                hoga_type,     # 거래구분
                ""             # 원주문번호
            )
            
            if ret == 0:
                order_id = f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                logger.info(f"주문 전송 성공: {order_id}")
                return order_id
            else:
                logger.error(f"주문 전송 실패: {ret}")
                return ""
                
        except Exception as e:
            logger.error(f"주문 전송 중 오류: {e}")
            return ""

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next):
        """TR 데이터 수신 이벤트 핸들러"""
        try:
            if trcode == "opt10001":  # 주식기본정보
                data = {
                    "stock_code": self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                 trcode, "", 0, "종목코드").strip(),
                    "stock_name": self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                 trcode, "", 0, "종목명").strip(),
                    "current_price": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                        trcode, "", 0, "현재가").strip()),
                    "change_amount": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                        trcode, "", 0, "전일대비").strip()),
                    "change_rate": float(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                        trcode, "", 0, "등락율").strip()),
                    "volume": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                 trcode, "", 0, "거래량").strip()),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.tr_data[trcode] = data
                
        except Exception as e:
            logger.error(f"TR 데이터 처리 중 오류: {e}")
        finally:
            self.tr_event_loop.exit()

    def _on_receive_real_data(self, stock_code, real_type, real_data):
        """실시간 데이터 수신 이벤트 핸들러"""
        try:
            if real_type == "주식체결":
                data = {
                    "stock_code": stock_code,
                    "current_price": int(self.dynamicCall("GetCommRealData(QString, int)", stock_code, 10)),
                    "change_amount": int(self.dynamicCall("GetCommRealData(QString, int)", stock_code, 11)),
                    "change_rate": float(self.dynamicCall("GetCommRealData(QString, int)", stock_code, 12)),
                    "volume": int(self.dynamicCall("GetCommRealData(QString, int)", stock_code, 13)),
                    "timestamp": datetime.now().isoformat()
                }
                
                # 콜백 함수 호출
                if self.real_data_callback:
                    self.real_data_callback(data)
                    
        except Exception as e:
            logger.error(f"실시간 데이터 처리 중 오류: {e}")

    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결/잔고 데이터 수신 이벤트 핸들러"""
        try:
            if gubun == "0":  # 주문체결
                order_data = {
                    "order_no": self.dynamicCall("GetChejanData(int)", 9203),
                    "stock_code": self.dynamicCall("GetChejanData(int)", 9001),
                    "stock_name": self.dynamicCall("GetChejanData(int)", 302),
                    "order_type": self.dynamicCall("GetChejanData(int)", 905),
                    "order_quantity": int(self.dynamicCall("GetChejanData(int)", 900)),
                    "order_price": int(self.dynamicCall("GetChejanData(int)", 901)),
                    "filled_quantity": int(self.dynamicCall("GetChejanData(int)", 911)),
                    "filled_price": int(self.dynamicCall("GetChejanData(int)", 910)),
                    "order_status": self.dynamicCall("GetChejanData(int)", 913),
                    "timestamp": datetime.now().isoformat()
                }
                
                # 콜백 함수 호출
                if self.chejan_callback:
                    self.chejan_callback(order_data)
                    
        except Exception as e:
            logger.error(f"체결 데이터 처리 중 오류: {e}")

    def register_real_data(self, stock_codes: List[str], callback: Callable):
        """실시간 데이터 등록"""
        try:
            self.real_data_callback = callback
            
            # 실시간 등록
            stock_codes_str = ";".join(stock_codes)
            ret = self.dynamicCall(
                "SetRealReg(QString, QString, QString, QString)",
                "1000",  # 화면번호
                stock_codes_str,
                "9001;10;11;12;27;28",  # 실시간 타입
                "1"  # 등록타입 (0: 등록, 1: 삭제 후 등록)
            )
            
            if ret == 0:
                logger.info(f"실시간 데이터 등록 성공: {stock_codes}")
            else:
                logger.error(f"실시간 데이터 등록 실패: {ret}")
                
        except Exception as e:
            logger.error(f"실시간 데이터 등록 중 오류: {e}")

    def set_chejan_callback(self, callback: Callable):
        """체결 콜백 함수 설정"""
        self.chejan_callback = callback


class KiwoomAPIManager:
    """키움 API 매니저 클래스"""
    
    def __init__(self):
        self.app = None
        self.kiwoom = None
        
    def initialize(self):
        """키움 API 초기화"""
        try:
            # QApplication 생성 (이미 존재하면 기존 것 사용)
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
            
            # 키움 API 인스턴스 생성
            self.kiwoom = KiwoomAPI()
            
            logger.info("키움 API 매니저 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"키움 API 초기화 실패: {e}")
            return False
    
    def login(self) -> bool:
        """로그인"""
        if not self.kiwoom:
            return False
        return self.kiwoom.login()
    
    def get_api(self) -> KiwoomAPI:
        """API 인스턴스 반환"""
        return self.kiwoom
    
    def run(self):
        """이벤트 루프 실행"""
        if self.app:
            self.app.exec_()


if __name__ == "__main__":
    # 테스트 코드
    manager = KiwoomAPIManager()
    
    if manager.initialize():
        if manager.login():
            api = manager.get_api()
            
            # 삼성전자 현재가 조회 테스트
            price_data = api.get_stock_price("005930")
            print(f"삼성전자 현재가: {price_data}")
            
        manager.run()
```

## 🚀 Windows 서비스 등록

### 서비스 설치 스크립트 (scripts/install-service.ps1)
```powershell
# install-service.ps1
# 관리자 권한으로 실행 필요

param(
    [string]$ServiceName = "CleonAI-Trading",
    [string]$ServiceDisplayName = "CleonAI 자동매매 서비스",
    [string]$ServiceDescription = "CleonAI 자동매매 시스템 백엔드 서비스",
    [string]$ProjectPath = "C:\CleonAI-Trading"
)

Write-Host "🚀 CleonAI 자동매매 서비스 설치" -ForegroundColor Green

# 관리자 권한 확인
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ 관리자 권한이 필요합니다. PowerShell을 관리자로 실행해주세요." -ForegroundColor Red
    exit 1
}

# PM2 설치 확인
try {
    pm2 --version | Out-Null
} catch {
    Write-Host "📦 PM2 설치 중..." -ForegroundColor Yellow
    npm install -g pm2
    npm install -g pm2-windows-service
}

# 프로젝트 디렉토리로 이동
Set-Location $ProjectPath

# PM2 설정 파일 생성
$pm2Config = @"
{
  "apps": [{
    "name": "$ServiceName",
    "script": "core/server.js",
    "cwd": "$ProjectPath",
    "env": {
      "NODE_ENV": "production",
      "PORT": 3000
    },
    "instances": 1,
    "autorestart": true,
    "watch": false,
    "max_memory_restart": "1G",
    "error_file": "./logs/pm2-error.log",
    "out_file": "./logs/pm2-out.log",
    "log_file": "./logs/pm2-combined.log",
    "time": true
  },
  {
    "name": "$ServiceName-Kiwoom",
    "script": "kiwoom/kiwoom_bridge.py",
    "interpreter": "python",
    "cwd": "$ProjectPath",
    "env": {
      "PYTHONPATH": "$ProjectPath"
    },
    "instances": 1,
    "autorestart": true,
    "watch": false,
    "error_file": "./logs/kiwoom-error.log",
    "out_file": "./logs/kiwoom-out.log",
    "log_file": "./logs/kiwoom-combined.log",
    "time": true
  }]
}
"@

$pm2Config | Out-File -FilePath "ecosystem.config.json" -Encoding UTF8

# PM2로 앱 시작
Write-Host "📊 PM2로 애플리케이션 시작..." -ForegroundColor Yellow
pm2 start ecosystem.config.json

# PM2 저장
pm2 save

# Windows 서비스로 등록
Write-Host "🔧 Windows 서비스 등록..." -ForegroundColor Yellow
pm2-service-install -n $ServiceName --serviceName $ServiceDisplayName

# 서비스 시작
Write-Host "▶️ 서비스 시작..." -ForegroundColor Yellow
Start-Service -Name $ServiceName

# 서비스 상태 확인
$service = Get-Service -Name $ServiceName
if ($service.Status -eq "Running") {
    Write-Host "✅ 서비스가 성공적으로 설치되고 실행 중입니다!" -ForegroundColor Green
    Write-Host "서비스 이름: $ServiceName" -ForegroundColor Cyan
    Write-Host "표시 이름: $ServiceDisplayName" -ForegroundColor Cyan
    Write-Host "상태: Running" -ForegroundColor Cyan
} else {
    Write-Host "❌ 서비스 설치는 완료되었지만 실행에 실패했습니다." -ForegroundColor Red
    Write-Host "서비스 상태: $($service.Status)" -ForegroundColor Red
}

Write-Host "`n🎉 설치 완료!" -ForegroundColor Green
Write-Host "다음 명령어로 서비스를 관리할 수 있습니다:" -ForegroundColor White
Write-Host "  Start-Service -Name $ServiceName" -ForegroundColor Gray
Write-Host "  Stop-Service -Name $ServiceName" -ForegroundColor Gray
Write-Host "  Restart-Service -Name $ServiceName" -ForegroundColor Gray
Write-Host "  pm2 list" -ForegroundColor Gray
Write-Host "  pm2 logs" -ForegroundColor Gray
```

### 서비스 제거 스크립트 (scripts/uninstall-service.ps1)
```powershell
# uninstall-service.ps1
param(
    [string]$ServiceName = "CleonAI-Trading"
)

Write-Host "🗑️ CleonAI 자동매매 서비스 제거" -ForegroundColor Yellow

# 관리자 권한 확인
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ 관리자 권한이 필요합니다." -ForegroundColor Red
    exit 1
}

try {
    # 서비스 중지
    Write-Host "⏹️ 서비스 중지 중..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    
    # PM2 앱 중지
    pm2 stop all
    pm2 delete all
    
    # Windows 서비스 제거
    Write-Host "🗑️ Windows 서비스 제거 중..." -ForegroundColor Yellow
    pm2-service-uninstall
    
    Write-Host "✅ 서비스가 성공적으로 제거되었습니다!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ 서비스 제거 중 오류 발생: $_" -ForegroundColor Red
}
```

## 📊 모니터링 및 관리

### 시스템 모니터링 스크립트 (scripts/monitor.ps1)
```powershell
# monitor.ps1
Write-Host "📊 CleonAI 자동매매 시스템 모니터링" -ForegroundColor Green

while ($true) {
    Clear-Host
    Write-Host "=== CleonAI 자동매매 시스템 상태 ===" -ForegroundColor Cyan
    Write-Host "시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
    Write-Host ""
    
    # 서비스 상태
    Write-Host "📋 서비스 상태:" -ForegroundColor Yellow
    try {
        $service = Get-Service -Name "CleonAI-Trading" -ErrorAction SilentlyContinue
        if ($service) {
            $statusColor = if ($service.Status -eq "Running") { "Green" } else { "Red" }
            Write-Host "  CleonAI Trading Service: $($service.Status)" -ForegroundColor $statusColor
        } else {
            Write-Host "  CleonAI Trading Service: 설치되지 않음" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  서비스 상태 확인 실패" -ForegroundColor Red
    }
    
    # PM2 프로세스 상태
    Write-Host "`n🔧 PM2 프로세스:" -ForegroundColor Yellow
    try {
        pm2 list
    } catch {
        Write-Host "  PM2가 설치되지 않았거나 실행되지 않음" -ForegroundColor Red
    }
    
    # 포트 사용 현황
    Write-Host "`n🌐 포트 사용 현황:" -ForegroundColor Yellow
    $ports = @(3000, 3001, 27017, 6379, 9000)
    foreach ($port in $ports) {
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connection) {
            Write-Host "  포트 $port : 사용 중 ($($connection.State))" -ForegroundColor Green
        } else {
            Write-Host "  포트 $port : 사용 안함" -ForegroundColor Gray
        }
    }
    
    # 메모리 사용량
    Write-Host "`n💾 시스템 리소스:" -ForegroundColor Yellow
    $mem = Get-CimInstance -ClassName Win32_OperatingSystem
    $totalMem = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
    $freeMem = [math]::Round($mem.FreePhysicalMemory / 1MB, 2)
    $usedMem = [math]::Round($totalMem - $freeMem, 2)
    $memPercent = [math]::Round(($usedMem / $totalMem) * 100, 1)
    
    Write-Host "  메모리: $usedMem GB / $totalMem GB ($memPercent%)" -ForegroundColor Cyan
    
    # CPU 사용량
    $cpu = Get-CimInstance -ClassName Win32_Processor | Measure-Object -Property LoadPercentage -Average
    Write-Host "  CPU: $([math]::Round($cpu.Average, 1))%" -ForegroundColor Cyan
    
    Write-Host "`n새로고침: 10초 | 종료: Ctrl+C" -ForegroundColor Gray
    Start-Sleep -Seconds 10
}
```

## 📝 자동화 스크립트

### 전체 시스템 시작 스크립트 (start-system.bat)
```batch
@echo off
echo ==========================================
echo  CleonAI 자동매매 시스템 시작
echo ==========================================

echo.
echo 1. MongoDB 시작...
net start MongoDB
if errorlevel 1 (
    echo MongoDB 시작 실패
    pause
    exit /b 1
)

echo 2. Redis 시작...
redis-server --service-start
if errorlevel 1 (
    echo Redis 시작 실패
    pause
    exit /b 1
)

echo 3. Node.js 서버 시작...
cd /d C:\CleonAI-Trading
npm start

echo.
echo 시스템이 성공적으로 시작되었습니다!
echo 서버 주소: http://localhost:3000
echo 관리자 페이지: http://localhost:8080
pause
```

### 전체 시스템 종료 스크립트 (stop-system.bat)
```batch
@echo off
echo ==========================================
echo  CleonAI 자동매매 시스템 종료
echo ==========================================

echo.
echo 1. Node.js 프로세스 종료...
taskkill /f /im node.exe 2>nul

echo 2. Python 프로세스 종료...
taskkill /f /im python.exe 2>nul

echo 3. Redis 종료...
redis-cli shutdown

echo 4. MongoDB 종료...
net stop MongoDB

echo.
echo 시스템이 성공적으로 종료되었습니다!
pause
```

---

**작성일**: 2025년 9월 22일  
**상태**: Windows 서버 구축 가이드 완료  
**다음 단계**: 기능별 파일 분리 구조 설계

