# CleonAI Trading Platform - Enterprise Edition

## 개요

PySide6 GUI, FastAPI 백엔드, PostgreSQL/Redis를 사용하는 엔터프라이즈급 자동매매 플랫폼입니다.

## 아키텍처

```
Frontend (PySide6) <---> Backend (FastAPI) <---> Trading Engine (키움 API)
                              |
                              v
                    Database (PostgreSQL + Redis)
```

## 시작하기

### 사전 요구사항

- Docker & Docker Compose
- Python 3.11+ (64비트) - Frontend & Backend
- Python 3.11+ (32비트) - Trading Engine (키움 API)
- Node.js 18+ (옵션, 개발 도구)

### 1. Docker 서비스 시작

```bash
# PostgreSQL, Redis 시작
docker-compose up -d postgres redis

# 로그 확인
docker-compose logs -f
```

### 2. 백엔드 실행

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 시작
uvicorn app.main:app --reload
```

서버: http://localhost:8000
API 문서: http://localhost:8000/docs

### 3. Trading Engine 실행

```bash
cd trading-engine
# 32비트 Python 환경 사용 필수
python32 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

python engine/main.py
```

### 4. Frontend 실행

```bash
cd frontend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

## 프로젝트 구조

```
cleonAI/
├── frontend/           # PySide6 GUI
├── backend/            # FastAPI 서버
├── trading-engine/     # 매매 엔진 (32비트)
├── shared/             # 공유 라이브러리
├── database/           # DB 스키마
├── docker/             # Docker 설정
├── docs/               # 문서
├── tests/              # 테스트
└── docker-compose.yml  # Docker Compose
```

## 개발 가이드

### API 개발

1. `backend/app/api/v1/`에 엔드포인트 추가
2. `backend/app/schemas/`에 Pydantic 스키마 정의
3. `backend/app/db/repositories/`에 Repository 추가
4. `backend/app/services/`에 비즈니스 로직 구현

### 전략 추가

1. `trading-engine/engine/strategies/`에 새 전략 파일 생성
2. `BaseStrategy` 상속
3. `generate_signal()` 메서드 구현
4. 엔진에 등록

### GUI 화면 추가

1. `frontend/views/`에 새 뷰 클래스 생성
2. `frontend/main.py`에서 등록
3. API 클라이언트 연결

## 테스트

```bash
# 백엔드 테스트
cd backend
pytest

# 엔진 테스트
cd trading-engine
pytest

# E2E 테스트
cd tests
pytest e2e/
```

## 배포

```bash
# 모든 서비스 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 중지
docker-compose down
```

## 환경 변수

각 서비스의 `.env` 파일 참조:
- `backend/.env` - 백엔드 설정
- `trading-engine/.env` - 엔진 설정
- `frontend/.env` - Frontend 설정

## 라이선스

MIT License

