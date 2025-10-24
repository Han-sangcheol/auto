# CleonAI Trading Platform - 빠른 시작 가이드

## 🚀 10분 안에 시작하기

### 1. Docker 서비스 시작

```powershell
# PostgreSQL + Redis 시작
docker-compose up -d postgres redis

# 로그 확인
docker-compose logs -f postgres redis
```

### 2. Backend 설정 및 실행

```powershell
# 자동 설정 스크립트 실행
.\scripts\setup_backend.ps1

# 또는 수동 설정
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Backend 시작
python app/main.py
```

**Backend가 시작되면:**
- API 서버: http://localhost:8000
- Swagger 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. API 테스트

```powershell
# PowerShell에서 테스트
.\scripts\test_backend.ps1

# 또는 브라우저에서
# http://localhost:8000/docs 열기
```

### 4. API 사용 예시

#### 계좌 조회
```bash
GET http://localhost:8000/api/v1/account/
```

#### 계좌 잔고 확인
```bash
GET http://localhost:8000/api/v1/account/1/balance
```

#### 포지션 목록
```bash
GET http://localhost:8000/api/v1/account/1/positions
```

#### 주문 실행
```bash
POST http://localhost:8000/api/v1/trading/order
Content-Type: application/json

{
  "account_id": 1,
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "order_type": "buy",
  "price_type": "market",
  "quantity": 10
}
```

## 📊 현재 구현 상태

### ✅ 완료된 기능
- [x] Docker 환경 (PostgreSQL, Redis)
- [x] Database 스키마 (11개 테이블)
- [x] Backend FastAPI 서버
- [x] Repository 패턴 (5개)
- [x] REST API (20+ 엔드포인트)
  - 계좌 관리
  - 주문/거래
  - 시세/급등주

### 🚧 개발 중
- [ ] WebSocket 실시간 통신
- [ ] Frontend (PySide6 GUI)
- [ ] Trading Engine (매매 로직)
- [ ] 키움 API 연동

## 🔧 문제 해결

### Docker 서비스가 시작되지 않음
```powershell
# Docker Desktop이 실행 중인지 확인
docker ps

# 컨테이너 재시작
docker-compose down
docker-compose up -d postgres redis
```

### Backend가 시작되지 않음
```powershell
# 가상환경 활성화 확인
.\venv\Scripts\Activate.ps1

# 패키지 재설치
pip install --upgrade pip
pip install -r requirements.txt

# 데이터베이스 연결 확인
# .env 파일의 DATABASE_URL 확인
```

### API 호출 시 404 오류
- Backend가 실행 중인지 확인: http://localhost:8000/health
- API 경로 확인: `/api/v1/` 프리픽스 필요

## 📖 추가 문서

- **아키텍처**: `docs/ARCHITECTURE.md`
- **구현 상황**: `IMPLEMENTATION_STATUS.md`
- **전체 가이드**: `README_ENTERPRISE.md`

## 🎯 다음 단계

1. **Backend 완성**: WebSocket 추가
2. **Frontend 시작**: PySide6 GUI 개발
3. **Trading Engine**: 매매 로직 리팩토링
4. **통합**: 전체 시스템 연결

---

**질문이나 문제가 있으신가요?**
- GitHub Issues에 문의
- `IMPLEMENTATION_STATUS.md`에서 진행 상황 확인

