# 🚀 CleonAI Trading Platform

**엔터프라이즈급 자동매매 플랫폼**

[![Status](https://img.shields.io/badge/status-완료-success)](docs/implementation/IMPLEMENTATION_STATUS.md)
[![Phase](https://img.shields.io/badge/phase-완료-blue)](docs/archive/PROJECT_COMPLETE.md)

---

## ⚠️ 🔴 중요: 하이브리드 아키텍처 (절대 변경 금지) 🔴 ⚠️

> **2025-11-05 확정**: 이 프로젝트는 32bit/64bit 하이브리드 구조입니다.

### 핵심 구조

```
D:\cleonAI\
├── .venv32\              # 32bit Python (키움 API)
│   └── auto_trading/     # 자동매매 실행
│
├── .venv\                # 64bit Python (나머지 모든 것)
│   ├── backend/          # FastAPI 서버
│   ├── frontend/         # PyQt GUI
│   ├── analysis/         # 데이터 분석
│   └── trading-engine/   # 트레이딩 엔진
│
├── auto_trading\         # 🔴 32bit 전용
│   └── requirements_32bit.txt
│
└── analysis\             # ✅ 64bit 전용
    └── requirements_64bit.txt
```

### 절대 규칙

1. **auto_trading만 32bit Python 사용** (키움 API 제약)
2. **나머지는 모두 64bit Python 사용**
3. **requirements 파일 절대 통합 금지**

**상세**: [auto_trading/HYBRID_ARCHITECTURE.md](auto_trading/HYBRID_ARCHITECTURE.md) ⭐

---

## ⚡ 빠른 시작 (5초 안에!)

### 1단계: 파일 더블클릭

```
D:\cleonAI\ 폴더에서
START.bat 파일을 더블클릭!
```

### 2단계: 3개 창 확인

- **런처 창** - 모든 서비스 제어
- **Backend 콘솔** - API 서버
- **Frontend GUI** - 본격적인 매매 화면! 🎨

### 3단계: 즐기세요!

- 대시보드에서 포지션 확인
- 매매 화면에서 주문 실행
- 차트에서 기술적 분석
- 급등주 자동 감지

---

## 🎨 화면 구성

### 📊 대시보드
- 계좌 요약 (총 자산, 현금, 주식 평가액)
- 손익 실시간 표시
- 보유 포지션 목록

### 💰 매매 화면
- 주문 실행 (시장가/지정가)
- 주문 내역 조회
- 체결 내역 확인

### 📈 차트
- 실시간 캔들스틱 차트
- 기술적 지표 (MA, 볼린저 밴드)
- 거래량 차트

### 🚀 급등주 모니터
- 실시간 급등주 감지
- 감지 설정 조정
- 자동 매수 설정

### ⚙️ 설정
- 매매 전략 설정 (MA, RSI, MACD)
- 리스크 관리 (손절/익절)
- 시스템 설정

### 📝 로그 뷰어
- 실시간 로그 조회
- 레벨별 필터링
- 로그 내보내기

---

## 🏗️ 아키텍처

```
Frontend (PySide6) ←→ Backend (FastAPI) ←→ Trading Engine (32-bit)
        ↓                      ↓                      ↓
    GUI 화면            REST API              키움 API
```

---

## 🛠️ 기술 스택

- **Frontend**: PySide6, pyqtgraph
- **Backend**: FastAPI, SQLAlchemy
- **Database**: PostgreSQL, Redis
- **Trading**: PyQt5 (32-bit), Kiwoom API

---

## 📚 문서

| 문서 | 설명 |
|------|------|
| [빠른 시작](docs/user/QUICKSTART_SIMPLE.md) | 3단계로 시작하기 |
| [API 문서](docs/developer/API.md) | REST API 참조 |
| [사용자 매뉴얼](docs/user/USER_MANUAL.md) | 화면별 사용법 |
| [개발자 가이드](docs/developer/DEVELOPER_GUIDE.md) | 개발 가이드 |
| [배포 가이드](docs/developer/DEPLOYMENT.md) | 배포 방법 |
| [전체 문서](docs/) | 모든 문서 보기 |

---

## 🔧 문제 해결

### Frontend 창이 안 열리면?

```powershell
pip install PySide6 pyqtgraph requests
```

### Backend가 시작 안 되면?

```powershell
pip install fastapi uvicorn
```

### 포트 충돌?

```powershell
# 8000 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8000

# 프로세스 종료
taskkill /PID <PID> /F
```

---

## 🎯 주요 기능

- ✅ **실시간 자동매매** - 5가지 전략
- ✅ **급등주 자동 감지** - 실시간 모니터링
- ✅ **리스크 관리** - 손절/익절 자동화
- ✅ **실시간 차트** - 기술적 지표
- ✅ **포트폴리오 관리** - 다중 포지션
- ✅ **실시간 알림** - WebSocket

---

## 📊 프로젝트 통계

- **코드**: 5,000+ 줄
- **API**: 17개 엔드포인트
- **화면**: 6개 (대시보드, 매매, 차트, 급등주, 설정, 로그)
- **전략**: 5개 (MA, RSI, MACD, Multi, Surge)
- **문서**: 2,000+ 줄

---

## 🎉 완료된 Phase

- ✅ Phase 1: 프로젝트 초기 설정
- ✅ Phase 2: Backend API 개발
- ✅ Phase 3: Trading Engine 리팩토링
- ✅ Phase 4: GUI 개발 ⭐ **NEW!**
- ✅ Phase 5: 통합 및 테스트
- ✅ Phase 6: 배포 및 문서화

**진행률: 100%** 🎊

---

## 🔗 링크

- 📊 [구현 진행 상황](docs/implementation/IMPLEMENTATION_STATUS.md)
- 🎉 [프로젝트 완료 보고](docs/archive/PROJECT_COMPLETE.md)
- 🏗️ [아키텍처 설계](docs/architecture/ARCHITECTURE.md)
- 📚 [전체 문서](docs/)

---

## ⚠️ 주의사항

- 실계좌 사용 전 모의투자로 충분히 테스트
- 리스크 관리 설정 필수
- 키움 API는 32-bit Python 필요

---

## 📞 지원

- **문서**: [docs/](docs/)
- **이슈**: GitHub Issues
- **이메일**: support@cleonai.com

---

## 🔗 관련 프로젝트

### auto_trading (독립 프로젝트)

키움 API 기반 독립 실행형 자동매매 프로그램입니다.

- **위치**: [auto_trading/](auto_trading/)
- **README**: [auto_trading/README.md](auto_trading/README.md)
- **문서**: [auto_trading/docs/](auto_trading/docs/)

---

## 🌟 시작하기

**지금 바로 시작하세요!**

```powershell
# 방법 1: 배치 파일 (가장 쉬움)
더블클릭: START.bat

# 방법 2: PowerShell
.\START.ps1

# 방법 3: Python
python launcher.py
```

---

<div align="center">

**⭐ 좋은 매매 되세요! ⭐**

Made with ❤️ by CleonAI Development Team

</div>
