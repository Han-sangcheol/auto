# CleonAI 프로젝트 현황

**최종 업데이트**: 2025년 10월 28일

---

## 📊 프로젝트 개요

CleonAI는 두 가지 주요 프로젝트로 구성됩니다:

### 1. 엔터프라이즈 자동매매 플랫폼 ⭐

**상태**: ✅ **완료** (Phase 6/6 완료)

현대적인 마이크로서비스 아키텍처 기반 자동매매 플랫폼

- **Frontend**: PySide6 GUI
- **Backend**: FastAPI REST API
- **Trading Engine**: 키움 API 32-bit
- **Database**: PostgreSQL, Redis
- **문서**: [docs/](docs/)

### 2. auto_trading (독립 프로젝트)

**상태**: ✅ **완료** (Phase 4/4 완료)

키움 API 기반 독립 실행형 자동매매 프로그램

- **구조**: 단일 실행 파일
- **특징**: 빠른 설치, 독립 실행
- **문서**: [auto_trading/docs/](auto_trading/docs/)

---

## 🎯 완료된 기능

### 엔터프라이즈 플랫폼

#### ✅ Phase 1: 프로젝트 초기 설정
- 프로젝트 구조 설계
- 기술 스택 선정
- 개발 환경 구성

#### ✅ Phase 2: Backend API 개발
- FastAPI 서버 구축
- PostgreSQL 데이터베이스 설계
- REST API 17개 엔드포인트 구현
- WebSocket 실시간 통신

#### ✅ Phase 3: Trading Engine 리팩토링
- 키움 API 래퍼 구현
- 5가지 매매 전략 (MA, RSI, MACD, Multi, Surge)
- 리스크 관리 시스템
- Redis 이벤트 버스

#### ✅ Phase 4: GUI 개발
- 6개 화면 구현
  - 대시보드 (계좌 요약, 손익)
  - 매매 화면 (주문 실행)
  - 차트 (실시간 캔들스틱)
  - 급등주 모니터
  - 설정 화면
  - 로그 뷰어
- 실시간 WebSocket 연동

#### ✅ Phase 5: 통합 및 테스트
- Frontend-Backend-Engine 통합
- Redis 메시지 브로커
- 단위 테스트 및 통합 테스트

#### ✅ Phase 6: 배포 및 문서화
- Docker 컨테이너화
- 배포 가이드 작성
- 완전한 문서화

### auto_trading

#### ✅ Phase 1-3: 기본 기능
- 키움 API 연동
- 3가지 매매 전략
- 리스크 관리
- 로깅 시스템

#### ✅ Phase 4: 급등주 감지
- 실시간 급등주 모니터링
- 자동/수동 승인 옵션
- GUI 모니터 창
- 데이터베이스 저장

---

## 📈 기술 스택

### 엔터프라이즈 플랫폼

| 계층 | 기술 |
|------|------|
| Frontend | PySide6, pyqtgraph |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL, Redis |
| Trading | PyQt5 (32-bit), Kiwoom API |
| 배포 | Docker, Docker Compose |

### auto_trading

| 항목 | 기술 |
|------|------|
| 언어 | Python 3.11+ (32-bit) |
| API | 키움 Open API+ |
| GUI | PyQt5 |
| Database | SQLite |
| 로깅 | Loguru |

---

## 📁 프로젝트 구조

```
cleonAI/                              # 루트
├── README.md                         # 엔터프라이즈 플랫폼 README
├── PROJECT_STATUS.md                 # 이 문서
├── START.bat / START.ps1             # 통합 런처
├── launcher.py                       # Python 런처
├── docs/                             # 📚 엔터프라이즈 문서
│   ├── architecture/                 # 아키텍처
│   ├── user/                         # 사용자 가이드
│   ├── developer/                    # 개발자 가이드
│   ├── implementation/               # 구현 상태
│   └── archive/                      # 완료 기록
├── backend/                          # FastAPI 서버
├── frontend/                         # PySide6 GUI
├── trading-engine/                   # 키움 API 엔진 (32-bit)
├── database/                         # DB 스크립트
├── docker/                           # Docker 파일
├── scripts/                          # 유틸리티 스크립트
├── shared/                           # 공통 모듈
└── auto_trading/                     # 🔗 독립 프로젝트
    ├── README.md                     # auto_trading README
    ├── docs/                         # 📚 auto_trading 문서
    ├── main.py                       # 실행 파일
    └── (기타 소스 코드)
```

---

## 🚀 빠른 시작

### 엔터프라이즈 플랫폼

```bash
# 통합 런처 (가장 쉬움)
START.bat

# 또는
python launcher.py
```

→ Backend, Frontend, Trading Engine 모두 자동 실행

**문서**: [docs/user/QUICKSTART_SIMPLE.md](docs/user/QUICKSTART_SIMPLE.md)

### auto_trading (독립 프로젝트)

```bash
cd auto_trading
start.bat

# 또는 원클릭 설치
.\auto_setup_complete.ps1
```

**문서**: [auto_trading/docs/installation/QUICK_INSTALL.md](auto_trading/docs/installation/QUICK_INSTALL.md)

---

## 📊 통계

### 엔터프라이즈 플랫폼

- **코드**: 5,000+ 줄
- **API 엔드포인트**: 17개
- **화면**: 6개
- **전략**: 5개
- **문서**: 2,000+ 줄

### auto_trading

- **코드**: 3,000+ 줄
- **전략**: 3개 (+ 급등주)
- **문서**: 35개 (체계적 정리)

---

## 📚 문서

### 엔터프라이즈 플랫폼

- [전체 문서](docs/README.md)
- [빠른 시작](docs/user/QUICKSTART_SIMPLE.md)
- [API 문서](docs/developer/API.md)
- [아키텍처](docs/architecture/ARCHITECTURE.md)

### auto_trading

- [전체 문서](auto_trading/docs/README.md)
- [빠른 설치](auto_trading/docs/installation/QUICK_INSTALL.md)
- [사용 가이드](auto_trading/docs/guides/QUICKSTART.md)
- [FAQ](auto_trading/docs/troubleshooting/FAQ.md)

---

## 🔄 향후 계획

### 단기 (1-3개월)

- [ ] 모바일 앱 (선택 사항)
- [ ] 백테스팅 시스템 강화
- [ ] 추가 매매 전략

### 장기 (6개월+)

- [ ] 다중 브로커 지원
- [ ] AI/ML 전략
- [ ] 클라우드 배포

---

## ⚠️ 주의사항

1. **실계좌 사용 전 충분한 테스트**
   - 모의투자로 최소 1개월 이상 검증
   - 소액부터 시작

2. **리스크 관리 필수**
   - 손절매/익절매 설정
   - 포지션 크기 제한
   - 일일 손실 한도

3. **법적 준수**
   - 프로그램매매 신고 의무 확인
   - 관련 법규 준수

---

## 📞 지원

- **문서**: [docs/](docs/) / [auto_trading/docs/](auto_trading/docs/)
- **이슈**: GitHub Issues
- **이메일**: support@cleonai.com

---

**Made with ❤️ by CleonAI Development Team**

