# 🛠️ 자동매매 앱 기술 스택 선정

## 📋 개요
API 분석 결과를 바탕으로 최적의 기술 스택을 선정하고 아키텍처를 설계한 문서입니다.

## 🏗️ 전체 아키텍처

### 시스템 구성도
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   모바일 앱      │◄──►│   백엔드 서버    │◄──►│  키움 API 서버  │
│   (Flutter)     │    │   (Node.js)     │    │   (Windows)     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • UI/UX         │    │ • API Gateway   │    │ • 키움 Open API │
│ • 상태 관리     │    │ • 인증/인가     │    │ • 실시간 데이터 │
│ • 로컬 캐시     │    │ • 비즈니스 로직 │    │ • 주문 처리     │
│ • 푸시 알림     │    │ • 데이터베이스  │    │ • 계좌 조회     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📱 1. 모바일 앱 (Frontend)

### Flutter 선택 이유
- ✅ **크로스플랫폼**: iOS/Android 동시 개발
- ✅ **성능**: 네이티브 수준의 성능
- ✅ **실시간 UI**: 금융 데이터 표시에 적합
- ✅ **풍부한 차트 라이브러리**: fl_chart, syncfusion_flutter_charts
- ✅ **WebSocket 지원**: 실시간 데이터 처리

### 핵심 패키지
```yaml
# pubspec.yaml
dependencies:
  flutter: 
    sdk: flutter
  
  # 상태 관리
  riverpod: ^2.4.0
  flutter_riverpod: ^2.4.0
  
  # 네트워킹
  dio: ^5.3.0
  web_socket_channel: ^2.4.0
  
  # 로컬 저장
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  
  # 차트
  fl_chart: ^0.64.0
  
  # 보안
  flutter_secure_storage: ^9.0.0
  local_auth: ^2.1.6
  
  # UI
  cupertino_icons: ^1.0.2
  google_fonts: ^6.1.0
```

### 프로젝트 구조
```
lib/
├── main.dart
├── core/
│   ├── constants/
│   ├── utils/
│   └── theme/
├── data/
│   ├── models/
│   ├── repositories/
│   └── services/
├── presentation/
│   ├── screens/
│   ├── widgets/
│   └── providers/
└── domain/
    ├── entities/
    └── usecases/
```

## 🖥️ 2. 백엔드 서버 (Backend)

### Node.js + Express 선택 이유
- ✅ **실시간 처리**: WebSocket 지원
- ✅ **JSON 네이티브**: 모바일 앱과 호환성
- ✅ **빠른 개발**: JavaScript 생태계
- ✅ **확장성**: 마이크로서비스 아키텍처 지원

### 핵심 패키지
```json
{
  "dependencies": {
    "express": "^4.18.2",
    "socket.io": "^4.7.2",
    "mongoose": "^7.5.0",
    "redis": "^4.6.7",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "helmet": "^7.0.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "node-cron": "^3.0.2"
  }
}
```

### API 설계
```javascript
// routes/api.js
const express = require('express');
const router = express.Router();

// 인증
router.post('/auth/login', authController.login);
router.post('/auth/logout', authController.logout);

// 계좌 정보
router.get('/account/balance', accountController.getBalance);
router.get('/account/positions', accountController.getPositions);

// 시세 조회
router.get('/stocks/:code/price', stockController.getPrice);
router.get('/stocks/:code/chart', stockController.getChart);

// 주문
router.post('/orders/buy', orderController.buy);
router.post('/orders/sell', orderController.sell);
router.get('/orders/history', orderController.getHistory);

// 자동매매
router.post('/trading/start', tradingController.start);
router.post('/trading/stop', tradingController.stop);
router.get('/trading/status', tradingController.getStatus);

module.exports = router;
```

## 🪟 3. 키움 API 연동 서버

### Python + PyQt5 선택 이유
- ✅ **키움 API 호환**: COM 인터페이스 지원
- ✅ **안정성**: 검증된 솔루션
- ✅ **커뮤니티**: 풍부한 예제 코드

### 핵심 패키지
```txt
# requirements.txt
PyQt5==5.15.9
pythoncom==228
requests==2.31.0
websockets==11.0.3
redis==4.6.0
schedule==1.2.0
pandas==2.0.3
numpy==1.25.2
```

### 키움 API 래퍼
```python
# kiwoom_wrapper.py
import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *

class KiwoomAPI(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        
    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        
    def comm_connect(self):
        """로그인"""
        self.dynamicCall("CommConnect()")
        
    def send_order(self, rqname, screen_no, acc_no, order_type, 
                   code, quantity, price, hoga, order_no):
        """주문 전송"""
        self.dynamicCall("SendOrder(QString, QString, QString, int, 
                         QString, int, int, QString, QString)", 
                         [rqname, screen_no, acc_no, order_type, 
                          code, quantity, price, hoga, order_no])
```

## 🗄️ 4. 데이터베이스

### MongoDB 선택 이유
- ✅ **JSON 호환**: Node.js와 완벽 호환
- ✅ **스키마 유연성**: 주식 데이터 구조 변화 대응
- ✅ **시계열 데이터**: 주가 데이터 저장에 적합

### 데이터 스키마
```javascript
// models/Stock.js
const stockSchema = new mongoose.Schema({
  code: { type: String, required: true, unique: true },
  name: { type: String, required: true },
  market: { type: String, enum: ['KOSPI', 'KOSDAQ'] },
  currentPrice: Number,
  changeRate: Number,
  volume: Number,
  updatedAt: { type: Date, default: Date.now }
});

// models/Order.js
const orderSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  stockCode: String,
  orderType: { type: String, enum: ['BUY', 'SELL'] },
  quantity: Number,
  price: Number,
  status: { type: String, enum: ['PENDING', 'FILLED', 'CANCELLED'] },
  createdAt: { type: Date, default: Date.now }
});
```

### Redis (캐싱 및 세션)
```javascript
// config/redis.js
const redis = require('redis');
const client = redis.createClient({
  host: process.env.REDIS_HOST,
  port: process.env.REDIS_PORT
});

// 실시간 데이터 캐싱
async function cacheStockPrice(code, data) {
  await client.setex(`stock:${code}`, 10, JSON.stringify(data));
}
```

## 🔒 5. 보안 및 인증

### JWT + OAuth 2.0
```javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');

function generateToken(user) {
  return jwt.sign(
    { userId: user._id, email: user.email },
    process.env.JWT_SECRET,
    { expiresIn: '7d' }
  );
}

function verifyToken(req, res, next) {
  const token = req.header('Authorization')?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({ message: '토큰이 없습니다' });
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    res.status(401).json({ message: '유효하지 않은 토큰입니다' });
  }
}
```

### 데이터 암호화
```dart
// Flutter 앱에서 민감 데이터 저장
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: IOSAccessibility.first_unlock_this_device,
    ),
  );
  
  static Future<void> storeToken(String token) async {
    await _storage.write(key: 'auth_token', value: token);
  }
  
  static Future<String?> getToken() async {
    return await _storage.read(key: 'auth_token');
  }
}
```

## ☁️ 6. 클라우드 인프라

### AWS 아키텍처
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   API Gateway   │    │      Lambda     │
│   (CDN/SSL)     │◄──►│  (API 관리)     │◄──►│   (서버리스)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      S3         │    │      RDS        │    │   ElastiCache   │
│  (정적 파일)     │    │   (메타데이터)  │    │    (캐시)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Docker 컨테이너화
```dockerfile
# backend/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

USER node

CMD ["node", "server.js"]
```

## 📊 7. 모니터링 및 로깅

### 로깅 시스템
```javascript
// utils/logger.js
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

module.exports = logger;
```

## 💰 개발 비용 추정

### 1차 개발 (3개월)
- **개발자 1명**: 800만원 × 3 = 2,400만원
- **서버 비용**: 50만원 × 3 = 150만원  
- **도구 및 라이센스**: 100만원
- **총 비용**: **2,650만원**

### 운영 비용 (월간)
- **AWS 서비스**: 80만원/월
- **Windows VM**: 30만원/월
- **도메인/SSL**: 5만원/월
- **총 운영비**: **115만원/월**

## 🚀 개발 일정

### Phase 1: 환경 구축 (2주)
- [ ] 개발환경 셋업
- [ ] 키움 API 연동 테스트
- [ ] 기본 아키텍처 구현

### Phase 2: 백엔드 개발 (4주)
- [ ] API 서버 구축
- [ ] 데이터베이스 설계
- [ ] 실시간 데이터 처리

### Phase 3: 모바일 앱 개발 (6주)
- [ ] UI/UX 구현
- [ ] 상태관리 구현
- [ ] API 연동

### Phase 4: 자동매매 로직 (4주)
- [ ] 매매 알고리즘 구현
- [ ] 백테스팅 시스템
- [ ] 리스크 관리

### Phase 5: 테스트 및 배포 (2주)
- [ ] 통합 테스트
- [ ] 성능 최적화
- [ ] 프로덕션 배포

## 📝 다음 단계 액션 아이템

1. ✅ **프로젝트 기획서 작성** (완료)
2. ✅ **법적 제약사항 조사** (완료) 
3. ✅ **API 분석** (완료)
4. ✅ **기술 스택 선정** (완료)
5. 🔲 **보안 아키텍처 설계** (다음)
6. 🔲 **매매 알고리즘 설계** (대기)
7. 🔲 **UI/UX 설계** (대기)

---

**작성일**: 2025년 9월 12일  
**기술검토**: 주요 기술 스택 검증 완료  
**상태**: 개발 준비 단계

