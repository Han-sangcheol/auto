# CleonAI Trading Platform

**엔터프라이즈급 자동매매 플랫폼**

[![Status](https://img.shields.io/badge/status-완료-success)](IMPLEMENTATION_STATUS.md)
[![Phase](https://img.shields.io/badge/phase-6%2F6-blue)](IMPLEMENTATION_STATUS.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🎉 프로젝트 완료!

CleonAI Trading Platform이 성공적으로 완성되었습니다! (2025-10-24)

콘솔 기반의 자동매매 시스템을 **마이크로서비스 아키텍처**로 완전히 전환하여, PySide6 GUI, FastAPI 백엔드, PostgreSQL/Redis를 갖춘 엔터프라이즈급 플랫폼이 되었습니다.

---

## 📋 목차

- [주요 기능](#주요-기능)
- [아키텍처](#아키텍처)
- [기술 스택](#기술-스택)
- [빠른 시작](#빠른-시작)
- [문서](#문서)
- [프로젝트 구조](#프로젝트-구조)
- [개발 가이드](#개발-가이드)
- [라이선스](#라이선스)

---

## ✨ 주요 기능

### 1. 실시간 자동매매
- ✅ 5가지 매매 전략 (MA, RSI, MACD, Multi, Surge)
- ✅ 리스크 관리 (손절매, 익절매, 포지션 사이징)
- ✅ 급등주 자동 감지 및 매수
- ✅ 실시간 시세 모니터링

### 2. 직관적인 GUI
- ✅ PySide6 기반 크로스플랫폼 인터페이스
- ✅ 6개 화면 (대시보드, 매매, 차트, 급등주, 설정, 로그)
- ✅ 실시간 WebSocket 연동
- ✅ pyqtgraph 실시간 차트

### 3. 강력한 백엔드 API
- ✅ FastAPI 기반 고성능 REST API (17개 엔드포인트)
- ✅ WebSocket 실시간 통신 (4개 채널)
- ✅ PostgreSQL 데이터 영구 저장
- ✅ Redis 실시간 캐싱 및 Pub/Sub

### 4. 확장 가능한 아키텍처
- ✅ 마이크로서비스 설계
- ✅ 브로커 어댑터 패턴 (키움 API)
- ✅ 이벤트 기반 아키텍처
- ✅ Docker 컨테이너화

### 5. 포괄적인 문서화
- ✅ API 문서 (Swagger/ReDoc)
- ✅ 사용자 매뉴얼
- ✅ 개발자 가이드
- ✅ 배포 가이드
- ✅ 아키텍처 문서

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (PySide6)                        │
│  - 대시보드 / 차트 / 설정 / 로그 뷰어                        │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API / WebSocket
┌────────────────────┴────────────────────────────────────────┐
│              Backend API Server (FastAPI)                    │
│  - 매매 엔진 제어 / 실시간 데이터 중계 / 인증               │
└────────┬───────────────────┬──────────────────┬────────────┘
         │                   │                  │
    ┌────▼─────┐      ┌─────▼──────┐    ┌─────▼─────┐
    │ Trading  │      │  Database  │    │  Broker   │
    │  Engine  │◄─────┤ PostgreSQL │    │  Adapter  │
    │ Service  │      │  / Redis   │    │  (키움)   │
    └──────────┘      └────────────┘    └───────────┘
```

**상세**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🛠️ 기술 스택

### Frontend
- **PySide6**: Qt 기반 크로스플랫폼 GUI
- **pyqtgraph**: 실시간 차트
- **asyncio**: 비동기 WebSocket 처리

### Backend
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **SQLAlchemy**: ORM
- **PostgreSQL (TimescaleDB)**: 시계열 데이터
- **Redis**: 캐싱 및 Pub/Sub
- **WebSocket**: 실시간 통신

### Trading Engine
- **PyQt5**: Qt 이벤트 루프 (32-bit)
- **Kiwoom OpenAPI**: 증권 API
- **Redis Pub/Sub**: 이벤트 전파
- **loguru**: 구조화된 로깅

### Infrastructure
- **Docker**: 컨테이너화
- **Docker Compose**: 오케스트레이션
- **Nginx**: 리버스 프록시 (프로덕션)

---

## 🚀 빠른 시작

### 사전 요구사항

- Windows 10/11 (64-bit)
- Python 3.10+ (64-bit)
- Python 3.10 (32-bit for Trading Engine)
- Docker Desktop
- 키움 OpenAPI 설치

### 1. 저장소 클론

```powershell
git clone https://github.com/yourusername/cleonai-trading-platform.git
cd cleonai-trading-platform
```

### 2. 환경 변수 설정

```powershell
# .env 파일 생성 및 편집
cp .env.example .env
notepad .env
```

**필수 환경 변수:**
```env
POSTGRES_PASSWORD=your_password
REDIS_PASSWORD=your_password
SECRET_KEY=your_secret_key
```

### 3. Docker 서비스 시작

```powershell
# PostgreSQL과 Redis 시작
docker-compose up -d postgres redis
```

### 4. Backend 시작

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**확인:** http://localhost:8000/docs

### 5. Frontend 시작

```powershell
cd frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### 6. Trading Engine 시작 (옵션)

```powershell
cd trading-engine
C:\Python310-32\python.exe -m venv .venv32
.\.venv32\Scripts\Activate.ps1
pip install -r requirements.txt
python engine/main.py
```

### 또는 자동화 스크립트 사용

```powershell
# 모든 서비스 시작
.\scripts\start_all.ps1
```

---

## 📚 문서

### 사용자 문서
- 📖 [사용자 매뉴얼](docs/USER_MANUAL.md) - 화면별 사용 가이드, FAQ
- 🚀 [빠른 시작 가이드](QUICKSTART.md) - 5분 안에 시작하기

### 개발자 문서
- 🏗️ [아키텍처](docs/ARCHITECTURE.md) - 시스템 설계 및 구조
- 📡 [API 문서](docs/API.md) - REST API 및 WebSocket
- 💻 [개발자 가이드](docs/DEVELOPER_GUIDE.md) - 코딩 규칙, 모듈 개발
- 🚢 [배포 가이드](docs/DEPLOYMENT.md) - 개발/프로덕션 배포

### 진행 상황
- 📊 [구현 진행 상황](IMPLEMENTATION_STATUS.md) - Phase 1-6 완료 (100%)
- ✅ [Phase 6 완료](PHASE_6_COMPLETE.md) - 배포 및 문서화

---

## 📁 프로젝트 구조

```
cleonai-trading-platform/
├── backend/                      # FastAPI 백엔드
│   ├── app/
│   │   ├── api/                  # REST/WebSocket API
│   │   ├── core/                 # 설정, 보안
│   │   ├── db/                   # 데이터베이스, Repository
│   │   ├── schemas/              # Pydantic 스키마
│   │   └── services/             # 비즈니스 로직
│   └── tests/                    # 백엔드 테스트
│
├── frontend/                     # PySide6 프론트엔드
│   ├── views/                    # 화면 (6개)
│   ├── widgets/                  # 재사용 위젯
│   ├── services/                 # API/WebSocket 클라이언트
│   └── tests/                    # 프론트엔드 테스트
│
├── trading-engine/               # 매매 엔진 (32-bit)
│   ├── engine/
│   │   ├── core/                 # 엔진 핵심
│   │   ├── strategies/           # 전략 (5개)
│   │   ├── indicators/           # 기술 지표
│   │   ├── brokers/              # 브로커 어댑터
│   │   └── events/               # 이벤트 시스템
│   └── tests/                    # 엔진 테스트
│
├── database/                     # 데이터베이스 스키마
│   ├── init.sql                  # 초기화 스크립트
│   └── backups/                  # 백업 디렉토리
│
├── docs/                         # 문서 (5개 주요 문서)
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── USER_MANUAL.md
│   ├── DEVELOPER_GUIDE.md
│   └── DEPLOYMENT.md
│
├── scripts/                      # 유틸리티 스크립트
│   ├── start_all.ps1
│   ├── deploy_production.ps1
│   └── test_integration.ps1
│
├── docker-compose.yml            # 개발 환경
├── docker-compose.prod.yml       # 프로덕션 환경
└── README_ENTERPRISE.md          # 이 파일
```

---

## 💻 개발 가이드

### 새로운 전략 추가

```python
# trading-engine/engine/strategies/my_strategy.py
from .base import BaseStrategy, SignalType

class MyStrategy(BaseStrategy):
    def generate_signal(self, stock_code, prices):
        # 전략 로직 구현
        if condition:
            return SignalType.BUY
        return None
```

**상세**: [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)

### API 엔드포인트 추가

1. 스키마 정의 (`backend/app/schemas/`)
2. 데이터베이스 모델 (`backend/app/db/models.py`)
3. Repository (`backend/app/db/repositories/`)
4. API 엔드포인트 (`backend/app/api/v1/`)
5. 라우터 등록 (`backend/app/main.py`)

**상세**: [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)

### 테스트 실행

```powershell
# Backend 테스트
cd backend
pytest tests/ -v

# Trading Engine 테스트
cd trading-engine
pytest tests/ -v

# Frontend 테스트
cd frontend
pytest tests/ -v
```

---

## 🚢 프로덕션 배포

### 자동화 스크립트

```powershell
# 환경 변수 설정
$env:POSTGRES_PASSWORD="your_password"
$env:REDIS_PASSWORD="your_password"
$env:SECRET_KEY="your_secret_key"

# 배포 실행
.\scripts\deploy_production.ps1
```

**상세**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 📊 프로젝트 통계

### 코드
- **총 파일 수**: 60+
- **총 코드 라인**: 5,000+
- **API 엔드포인트**: 17개
- **WebSocket 채널**: 4개
- **전략 모듈**: 5개
- **화면 컴포넌트**: 6개

### 테스트
- **단위 테스트**: 50+ 케이스
- **통합 테스트**: 5개 시나리오
- **E2E 테스트**: 자동화

### 문서
- **총 문서 라인**: 2,000+
- **주요 문서**: 5개
- **코드 예시**: 30+
- **FAQ**: 7개

---

## 🛡️ 보안

### 주의사항
- ❌ `.env` 파일을 Git에 커밋하지 마세요
- ❌ 계좌번호, 비밀번호를 코드에 하드코딩하지 마세요
- ✅ 모의투자로 충분히 테스트하세요
- ✅ 실계좌 사용 시 리스크 관리 필수

### 환경 변수
모든 민감한 정보는 환경 변수로 관리합니다:
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `SECRET_KEY`
- `KIWOOM_ACCOUNT_NUMBER`

---

## 🤝 기여

기여를 환영합니다! 다음 절차를 따라주세요:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**커밋 메시지 규칙:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `refactor`: 리팩토링
- `test`: 테스트 추가

**상세**: [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)

---

## 📞 지원

### 문서
- 📖 [사용자 매뉴얼](docs/USER_MANUAL.md)
- 💻 [개발자 가이드](docs/DEVELOPER_GUIDE.md)
- 🚀 [배포 가이드](docs/DEPLOYMENT.md)

### 이슈
- GitHub Issues: https://github.com/yourusername/cleonai-trading-platform/issues

### 연락처
- Email: support@cleonai.com

---

## 📜 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 🌟 주요 성과

### 아키텍처 전환
- ❌ **이전**: 단일 파일 콘솔 애플리케이션
- ✅ **현재**: 마이크로서비스 기반 엔터프라이즈급 플랫폼

### 기능 향상
- ✅ GUI 인터페이스 (PySide6)
- ✅ 실시간 WebSocket 통신
- ✅ 데이터 영구 저장 (PostgreSQL)
- ✅ 확장 가능한 전략 시스템
- ✅ 브로커 어댑터 패턴

### 개발 경험
- ✅ 포괄적인 문서화 (2,000+ 줄)
- ✅ 자동화된 테스트
- ✅ 배포 자동화
- ✅ 명확한 코딩 규칙

---

## 🎯 향후 계획

### Phase 7 (선택)
- [ ] CI/CD 파이프라인 (GitHub Actions)
- [ ] 모니터링 시스템 (Prometheus + Grafana)
- [ ] 멀티 브로커 지원 (eBest, NH투자증권)
- [ ] 백테스팅 기능
- [ ] 포트폴리오 분석 도구
- [ ] 모바일 앱 (React Native)

---

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트에 감사를 표합니다:
- [FastAPI](https://fastapi.tiangolo.com/)
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)
- [Docker](https://www.docker.com/)

---

**작성일**: 2025-10-24  
**버전**: 1.0  
**상태**: ✅ 프로젝트 완료 (Phase 1-6)  
**담당자**: CleonAI Development Team

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요! ⭐**

[Documentation](docs/) | [Issues](https://github.com/yourusername/cleonai-trading-platform/issues) | [Discussions](https://github.com/yourusername/cleonai-trading-platform/discussions)

</div>
