# CleonAI 자동매매 프로그램

키움증권 Open API를 활용한 PC 기반 Python 자동매매 시스템

---

## ⚠️ 🔴 절대 변경 금지 - 하이브리드 아키텍처 🔴 ⚠️

> **경고**: 이 섹션은 프로젝트의 핵심 아키텍처입니다. 절대로 수정하지 마십시오!

### 🏗️ 32bit/64bit 하이브리드 구조 (2025-11-05 확정)

**이 프로젝트는 32bit와 64bit Python을 동시에 사용합니다.**

```
D:\cleonAI\
├── .venv32\              # 32bit Python (키움 API 전용)
│   └── auto_trading 실행
│
├── .venv\                # 64bit Python (데이터 분석)
│   └── analysis 실행
│
├── auto_trading\         # 🔴 32bit 전용 모듈
│   ├── requirements_32bit.txt  ← 이것만 사용!
│   ├── main.py
│   └── data/stocks.db (SQLite 공유)
│
└── analysis\             # ✅ 64bit 전용 모듈
    ├── requirements_64bit.txt  ← 고급 분석용
    └── 시각화/백테스팅
```

### 📋 핵심 원칙 (절대 변경 금지)

1. **auto_trading은 항상 32bit Python으로만 실행**
   - 키움 API는 32bit만 지원
   - `.venv32` 가상환경 사용
   - `requirements_32bit.txt` 패키지만 설치

2. **빌드가 필요한 패키지는 64bit 모듈로 분리**
   - psutil, yfinance, pandas-ta 등
   - Visual C++ 빌드 도구 필요 패키지
   - 32bit에서 빌드 실패하는 모든 패키지

3. **데이터 공유는 SQLite를 통해서만**
   - `auto_trading/data/stocks.db`
   - 32bit → 쓰기, 64bit → 읽기

4. **절대로 requirements.txt를 통합하지 말것**
   - `requirements_32bit.txt` (자동매매)
   - `requirements_64bit.txt` (분석)
   - 분리 유지 필수!

### 🚫 하지 말아야 할 것

- ❌ requirements.txt에 psutil, yfinance 추가
- ❌ 64bit Python으로 auto_trading 실행
- ❌ 32bit에서 고급 분석 패키지 설치 시도
- ❌ 두 requirements 파일 통합

### ✅ 올바른 실행 방법

**자동매매 (32bit)**:
```powershell
cd D:\cleonAI\auto_trading
..\.venv32\Scripts\Activate.ps1
pip install -r requirements_32bit.txt
python main.py
```

**데이터 분석 (64bit)**:
```powershell
cd D:\cleonAI\analysis
..\.venv\Scripts\Activate.ps1
pip install -r requirements_64bit.txt
jupyter notebook
```

### 📚 상세 문서

- **아키텍처**: [HYBRID_ARCHITECTURE.md](HYBRID_ARCHITECTURE.md) ⭐ 필독
- **32bit 설정**: [docs/installation/PYTHON_32BIT_SETUP.md](docs/installation/PYTHON_32BIT_SETUP.md)
- **64bit 분석**: [../analysis/README.md](../analysis/README.md)

---

## 개요

이 프로그램은 키움증권 Open API+를 사용하여 주식을 자동으로 매매하는 시스템입니다. 
검증된 기술적 분석 전략(이동평균, RSI, MACD)을 조합하여 매매 신호를 생성하고, 
엄격한 리스크 관리를 통해 안전한 거래를 수행합니다.

## 주요 기능

- **다중 전략 조합**: 3개 전략의 합의 알고리즘으로 신뢰도 높은 신호 생성
- **급등주 자동 감지**: 거래대금 상위 종목 중 급등하는 종목을 실시간 감지 및 자동 매매
  - 거래대금 상위 100개 종목 실시간 모니터링
  - 상승률 + 거래량 급증 조건으로 급등주 감지
  - 수동 승인(안전) 또는 자동 승인(공격적) 선택 가능
- **시계열 데이터베이스**: 🆕 **SQLite** 기반 데이터 저장 (32/64비트 모두 지원)
  - 실시간 1분봉 OHLCV 데이터 자동 저장
  - Python 기본 포함 (추가 설치 불필요)
  - Excel, CSV 내보내기 지원
  - 과거 데이터 기반 백테스팅 및 분석 지원
- **자동 리스크 관리**: 손절매(-5%), 익절매(+10%), 포지션 사이징 자동화
- **실시간 모니터링**: 실시간 시세 데이터 기반 즉각 반응
- **모의투자 지원**: 안전한 테스트 환경에서 충분한 검증 가능
- **상세한 로깅**: 모든 거래 내역과 의사결정 과정 자동 기록

## 시스템 요구사항

- **운영체제**: Windows 10/11 (64비트)
- **Python**: 3.11 이상 **⚠️ 32비트 버전 필수** (키움 API 요구사항)
- **메모리**: 4GB RAM 이상
- **키움증권**: 계좌 + Open API+ 설치 + 공동인증서

> ### ⚠️ 중요: Python 32bit 필수!
> 
> **키움 Open API는 32bit Python만 지원합니다.**
> 
> - 현재 64bit Python 사용 중이라면 추가로 32bit 설치 필요
> - 두 버전은 독립적으로 사용 가능 (충돌 없음)
> - 자동 설치 스크립트 제공 (관리자 권한 필요)
> 
> **빠른 설치:**
> ```powershell
> cd auto_trading\scripts
> .\install_python32.ps1  # 관리자 권한 PowerShell
> ```
> 
> 📖 **자세한 가이드**: [Python 32bit 설치](docs/installation/PYTHON_32BIT_SETUP.md)

## 📚 문서 가이드

**모든 문서는 [docs/](docs/) 폴더에 체계적으로 정리되어 있습니다.**

### 빠른 링크

| 카테고리 | 문서 |
|---------|------|
| 🚀 **설치** | [빠른 설치](docs/installation/QUICK_INSTALL.md) ⭐ 추천 |
| 📖 **사용법** | [빠른 시작](docs/guides/QUICKSTART.md) |
| 🔧 **문제 해결** | [FAQ](docs/troubleshooting/FAQ.md) / [트러블슈팅](docs/troubleshooting/TROUBLESHOOTING.md) |
| 📊 **데이터 분석** | [데이터 시각화 가이드](docs/guides/VISUALIZATION_GUIDE.md) |
| 📚 **전체 문서** | [docs/README.md](docs/README.md) |

### 처음 사용하는 경우

1. [빠른 설치](docs/installation/QUICK_INSTALL.md) ⭐ **가장 쉬움** (5분)
2. 또는 [완전 설치 가이드](docs/installation/GETTING_STARTED.md) (30-40분)
3. [빠른 시작](docs/guides/QUICKSTART.md) (5분)
4. [매매 전략](docs/guides/STRATEGY_GUIDE.md)

### 문제가 발생한 경우

1. [FAQ](docs/troubleshooting/FAQ.md)
2. [트러블슈팅](docs/troubleshooting/TROUBLESHOOTING.md)
3. [실행 문제 해결](docs/troubleshooting/START_TROUBLESHOOTING.md)

## 데이터베이스 및 분석

### 🆕 시계열 데이터베이스 (2025-10-28)

프로그램은 실시간으로 수신한 가격 데이터를 자동으로 데이터베이스에 저장합니다.

**기술 스택:**
- **SQLite**: Python 기본 포함 데이터베이스 (32/64비트 모두 지원)
- **CSV**: 범용 파일 포맷 (Excel, Power BI 등 모든 도구 호환)
- **1분봉 OHLCV**: 시가, 고가, 저가, 종가, 거래량

**자동 저장:**
```python
# 데이터는 자동으로 저장됩니다 (설정 변경 불필요)
# 저장 위치: data/stocks.db (SQLite 데이터베이스)
# CSV: data/csv/YYYY-MM/종목코드_YYYY-MM-DD.csv
```

**데이터 활용:**

1. **Excel/CSV 내보내기**
```python
from data_analyzer import DataAnalyzer
from database import StockDatabase
from datetime import datetime, timedelta

db = StockDatabase()
analyzer = DataAnalyzer(db)

# 최근 7일 데이터를 Excel로
start_date = datetime.now() - timedelta(days=7)
analyzer.export_to_excel('005930', start_date, datetime.now(), 'samsung.xlsx')
```

2. **통계 분석**
```python
# 통계 출력
analyzer.print_statistics('005930', start_date, datetime.now())
```

3. **자동 리포트**
```python
# HTML 리포트 생성
analyzer.generate_report('005930', start_date, datetime.now(), 'report.html')
```

**상세 가이드**: [데이터 시각화 가이드](docs/guides/VISUALIZATION_GUIDE.md)

## 빠른 시작 (요약)

### ✅ 실행 전 체크리스트

1. **Python 32bit 설치 확인** ⚠️ 필수!
   ```powershell
   python -c "import sys; print('32bit' if sys.maxsize <= 2**32 else '64bit')"
   ```
   - 결과가 `32bit`이면 OK
   - `64bit`이면 [Python 32bit 설치](docs/installation/PYTHON_32BIT_SETUP.md) 필요

2. **키움 Open API+ 설치**
   - [설치 가이드](docs/installation/KIWOOM_API_SETUP.md) 참고

3. **모의투자 계좌 준비**
   - [키움 홈페이지](https://www.kiwoom.com)에서 신청

### 🚀 원클릭 자동 설치 (권장)

PowerShell 관리자 권한으로:
```powershell
cd auto_trading\scripts
.\install_python32.ps1  # Python 32bit 자동 설치
.\setup.ps1             # 가상환경 생성 및 패키지 설치
```
→ Python 32비트 다운로드 + 설치 + 환경 구성 모두 자동!

자세한 내용: **[빠른 설치 가이드](docs/installation/QUICK_INSTALL.md)**

### 📝 단계별 설치

```powershell
# 0. Python 32비트 설치 (처음 1회만) ⚠️ 필수
cd auto_trading\scripts
.\install_python32.ps1           # 자동 다운로드 + 설치 (관리자 권한)

# 1. 가상환경 생성 및 패키지 설치 (처음 1회만)
cd ..
scripts\setup.bat       # CMD
# 또는
scripts\setup.ps1       # PowerShell (권장)

# 2. .env 파일 설정 (중요!)
# 파일 탐색기에서 .env 파일을 메모장으로 열기
# 필수 항목:
#   KIWOOM_ACCOUNT_NUMBER=계좌번호     # 모의투자는 8로 시작
#   KIWOOM_ACCOUNT_PASSWORD=0000       # HTS에서 설정한 4자리 비밀번호
#   WATCH_LIST=005930,000660,035720    # 관심 종목
#
# 계좌 비밀번호 설정 방법: docs/troubleshooting/PASSWORD_ISSUE.md 참고

# 3. 프로그램 실행 (32bit Python 가상환경 자동 활성화)
scripts\start.bat       # CMD
# 또는
scripts\start.ps1       # PowerShell (권장)
```

### 🔍 문제 해결

**"64-bit Python detected!" 오류가 발생하면:**
1. Python 32bit 설치: `scripts\install_python32.ps1`
2. 가상환경 재생성: `scripts\setup.bat`
3. 실행 스크립트 사용: `scripts\start.bat`

📖 **자세한 가이드**: [Python 32bit 설치](docs/installation/PYTHON_32BIT_SETUP.md)

## 프로젝트 구조

**2025-11-05 업데이트**: Python 32bit/64bit 명확한 구분 추가  
**2025-11-04 구조 개선**: 모듈을 역할별로 분리하여 체계적으로 관리합니다.

### Python 환경 구분

```
D:\cleonAI\
├── .venv32\          # ⚠️ 32bit Python (auto_trading 전용)
├── .venv\            # ✅ 64bit Python (backend, frontend 등)
└── auto_trading\     # 🔴 32bit Python 필수 (키움 API)
```

### 파일 구조

```
auto_trading/
├── README.md                    # 이 문서
├── main.py                      # 프로그램 진입점 (32bit 체크 포함)
├── config.py                    # 설정 관리
│
├── core/                        # 📦 핵심 자동매매 로직
│   ├── trading_engine.py        # 자동매매 엔진
│   ├── strategies.py            # 매매 전략
│   ├── risk_manager.py          # 리스크 관리
│   ├── indicators.py            # 기술적 지표
│   └── kiwoom_api.py            # 키움 API 래퍼
│
├── features/                    # 🚀 고급 기능 (선택적)
│   ├── surge_detector.py        # 급등주 감지
│   ├── news_crawler.py          # 뉴스 크롤링
│   ├── news_strategy.py         # 뉴스 기반 전략
│   ├── sentiment_analyzer.py    # 감성 분석
│   ├── market_scheduler.py      # 시장 스케줄러
│   ├── scheduler.py             # 자동 시작/종료
│   └── health_monitor.py        # 헬스 모니터
│
├── gui/                         # 🖥️ GUI 컴포넌트
│   ├── monitor_gui.py           # 메인 모니터 창
│   ├── chart_widget.py          # 차트 위젯
│   ├── advanced_chart_widget.py # 고급 차트
│   ├── settings_dialog.py       # 설정 다이얼로그
│   └── ...                      # 기타 GUI 위젯
│
├── database/                    # 💾 데이터 저장 및 분석
│   ├── database.py              # SQLite 데이터베이스
│   ├── trading_history_db.py    # 거래 이력 블랙박스
│   ├── data_analyzer.py         # 데이터 분석
│   └── candle_aggregator.py     # 캔들 집계
│
├── utils/                       # 🛠️ 유틸리티
│   ├── logger.py                # 로깅 시스템
│   ├── fee_calculator.py        # 수수료 계산
│   └── notification.py          # 알림 시스템
│
├── scripts/                     # 📜 실행 스크립트 및 설치 도구
│   ├── setup.ps1 / setup.bat    # 설치 스크립트 (.venv32 생성)
│   ├── start.ps1 / start.bat    # 실행 스크립트 (32bit Python 자동)
│   ├── install_python32.ps1     # Python 32비트 자동 설치 ⭐
│   └── ...
│
├── docs/                        # 📚 문서
│   ├── guides/                  # 사용 가이드
│   │   ├── TRADING_LOGIC.md     # ⭐ 매매 원리 문서
│   │   ├── QUICKSTART.md        # 빠른 시작
│   │   └── ...
│   ├── installation/            # 설치 가이드
│   ├── troubleshooting/         # 문제 해결
│   └── implementation/          # 구현 진행
│
├── data/                        # 데이터 저장
│   ├── stocks.db                # SQLite 데이터베이스
│   └── csv/                     # CSV 내보내기
│
├── logs/                        # 로그 파일
│   ├── trading.log              # 거래 로그
│   ├── error.log                # 에러 로그
│   └── trading_history.db       # 거래 이력 블랙박스
│
├── requirements.txt             # 패키지 의존성
└── .env                         # 환경 변수 (Git 제외)
```

### 주요 모듈 설명

| 모듈 | 역할 | 주요 파일 |
|-----|------|----------|
| `core/` | 자동매매 핵심 로직 | trading_engine, strategies, risk_manager |
| `features/` | 선택적 고급 기능 | surge_detector, news_crawler, scheduler |
| `gui/` | PyQt 기반 GUI | monitor_gui, chart_widget, dialogs |
| `database/` | 데이터 저장/분석 | database, trading_history_db, analyzer |
| `utils/` | 공통 유틸리티 | logger, fee_calculator, notification |
| `scripts/` | 실행 스크립트 | setup.ps1, start.bat 등 |

## 주의사항

### 투자 리스크
- 자동매매도 손실 위험이 있습니다
- **반드시 모의투자로 최소 1개월 이상 테스트**하세요
- 실계좌 사용 시 소액부터 시작하세요

### 급등주 자동 승인 사용 시 주의 ⚠️
- **`SURGE_AUTO_APPROVE=True` 설정은 매우 공격적입니다**
- 급등 조건을 만족하는 모든 종목을 자동으로 매수합니다
- 짧은 시간에 여러 종목을 동시에 매수할 수 있습니다
- **실계좌에서는 반드시 `False`(수동 승인)로 시작하세요**
- 충분한 테스트 후에만 자동 승인을 고려하세요

### 법적 준수
- 프로그램매매 신고 의무를 확인하세요
- 관련 법규를 준수하세요
- 불공정거래는 절대 금지됩니다

### 보안
- `.env` 파일을 절대로 공유하지 마세요
- 계좌 정보는 안전하게 보관하세요
- 신뢰할 수 있는 PC에서만 실행하세요

## 지원

문제가 발생하거나 질문이 있으시면:

1. [FAQ](docs/troubleshooting/FAQ.md) 확인
2. [트러블슈팅](docs/troubleshooting/TROUBLESHOOTING.md) 확인
3. [전체 문서](docs/README.md) 확인
4. 로그 파일 확인 (`logs/trading.log`, `logs/error.log`)

## 라이선스

이 프로그램은 교육 및 개인 학습 목적으로 제공됩니다.

**면책 조항**: 
- 이 프로그램 사용으로 인한 모든 투자 손실은 사용자 본인의 책임입니다.
- 개발자는 어떠한 투자 손실에 대해서도 책임지지 않습니다.
- 실제 투자는 신중하게 결정하시기 바랍니다.

---

**버전**: 1.1.0  
**최종 업데이트**: 2025년 10월 23일  
**주요 추가 기능**: 급등주 자동 감지 및 매매


## 실행 방법
# 1. Docker 서비스 시작
docker-compose up -d postgres redis

# 2. Backend 시작
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# 3. Frontend 시작 (새 터미널)
cd frontend
.\.venv\Scripts\Activate.ps1
python main.py

## 완전 실행 (자동매매 포함):
# 터미널 1: Backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# 터미널 2: Frontend
cd frontend
.\.venv\Scripts\Activate.ps1
python main.py

# 터미널 3: Trading Engine
cd trading-engine
.\.venv32\Scripts\Activate.ps1
python engine/main.py






## PowerShell에서 직접 가상환경을 생성:
# 1. 프로젝트 루트로 이동
cd D:\cleonAI

# 2. 32bit Python으로 가상환경 생성
C:\Python32\python.exe -m venv .venv32

# 3. 가상환경 활성화
.\.venv32\Scripts\Activate.ps1

# 4. auto_trading 폴더로 이동
cd auto_trading

# 5. pip 업그레이드
python -m pip install --upgrade pip

# 6. 패키지 설치
pip install -r requirements.txt

# 7. 프로그램 실행
scripts\start.bat

















