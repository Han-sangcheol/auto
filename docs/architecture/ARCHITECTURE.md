# CleonAI Trading Platform 아키텍처

## 시스템 개요

CleonAI Trading Platform은 마이크로서비스 아키텍처를 기반으로 한 엔터프라이즈급 자동매매 시스템입니다.

## 시스템 구성

### 1. Frontend (PySide6)
- **역할**: 사용자 인터페이스
- **기술**: PySide6, pyqtgraph, asyncio
- **주요 기능**:
  - 대시보드 (포지션, 수익, 실시간 차트)
  - 매매 화면 (주문, 체결 내역)
  - 급등주 모니터
  - 설정 및 로그 뷰어

### 2. Backend (FastAPI)
- **역할**: API 서버 및 비즈니스 로직
- **기술**: FastAPI, SQLAlchemy, Redis
- **주요 기능**:
  - REST API 제공
  - WebSocket 실시간 데이터 스트림
  - 데이터베이스 관리
  - 인증 및 권한 관리
  - Trading Engine과 통신

### 3. Trading Engine (Python 32bit)
- **역할**: 순수 매매 로직 실행
- **기술**: asyncio, PyQt5 (키움 API)
- **주요 기능**:
  - 키움 API 연동
  - 전략 실행
  - 주문 관리
  - 리스크 관리
  - 이벤트 발행

### 4. Database
- **PostgreSQL**: 주 데이터베이스
  - 계좌, 포지션, 주문, 거래 내역
  - 전략 설정
- **TimescaleDB**: 시계열 데이터
  - 시세 데이터 (OHLCV)
- **Redis**: 캐싱 및 실시간 데이터
  - 실시간 시세 캐시
  - Pub/Sub 메시징

## 데이터 흐름

```
1. 시세 데이터 수신
   Trading Engine (키움 API) → Redis Pub/Sub → Backend → WebSocket → Frontend

2. 주문 실행
   Frontend → Backend API → Redis Queue → Trading Engine → 키움 API

3. 전략 신호
   Trading Engine (전략) → Redis Event → Backend → Database → WebSocket → Frontend
```

## API 설계

### REST API Endpoints

#### 계좌 관리
- `GET /api/v1/account/balance` - 잔고 조회
- `GET /api/v1/account/positions` - 포지션 목록
- `POST /api/v1/account` - 계좌 생성

#### 매매
- `POST /api/v1/trading/order` - 주문 실행
- `DELETE /api/v1/trading/order/{id}` - 주문 취소
- `GET /api/v1/trading/orders` - 주문 목록
- `GET /api/v1/trading/trades` - 거래 내역

#### 시세
- `GET /api/v1/market/stocks/{code}` - 종목 정보
- `GET /api/v1/market/surge` - 급등주 목록

#### 전략
- `GET /api/v1/strategy/list` - 전략 목록
- `PUT /api/v1/strategy/{id}/config` - 전략 설정
- `POST /api/v1/strategy/{id}/activate` - 전략 활성화

### WebSocket Channels
- `/ws/market` - 실시간 시세
- `/ws/orders` - 주문 체결
- `/ws/positions` - 포지션 업데이트
- `/ws/surge` - 급등주 알림

## 보안

### 인증
- JWT 토큰 기반 인증
- 액세스 토큰 (30분 유효)
- 리프레시 토큰 (7일 유효)

### 권한
- 일반 사용자: 본인 계좌만 접근
- 관리자: 모든 계좌 접근

## 확장성

### 수평 확장
- Backend: 로드 밸런서 뒤에 여러 인스턴스 배포
- Redis: Sentinel을 통한 HA 구성
- PostgreSQL: Read Replica 구성

### 수직 확장
- 각 서비스의 리소스 증설

## 모니터링

### 로그
- 시스템 로그: database (system_logs 테이블)
- 애플리케이션 로그: 파일 (logs/)

### 메트릭
- API 응답 시간
- 데이터베이스 쿼리 성능
- Trading Engine 처리량

## 배포

### Development
```bash
docker-compose up -d
```

### Production
- Docker Swarm 또는 Kubernetes
- CI/CD 파이프라인 (GitHub Actions)

