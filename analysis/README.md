# 📊 CleonAI 데이터 분석 모듈 (64bit)

## 개요

이 모듈은 **64bit Python**에서 실행되며, 자동매매 데이터의 고급 분석, 시각화, 백테스팅을 제공합니다.

## 시스템 요구사항

- **Python**: 3.11 이상 **64bit** (32bit 불가)
- **운영체제**: Windows 10/11
- **메모리**: 8GB RAM 이상 권장
- **Visual Studio Build Tools**: 일부 패키지 빌드에 필요 (선택)

## 설치

### 1. 64bit Python 가상환경 생성

```powershell
cd D:\cleonAI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 패키지 설치

```powershell
cd analysis
pip install -r requirements_64bit.txt
```

## 주요 기능

### 1. 데이터 분석
- 거래 데이터 통계 분석
- 성과 지표 계산
- 리스크 분석

### 2. 시각화
- 고급 차트 (Plotly)
- 성과 대시보드
- 실시간 모니터링

### 3. 백테스팅
- 과거 데이터 기반 전략 테스트
- 최적화 파라미터 탐색
- 시뮬레이션

### 4. 외부 데이터
- Yahoo Finance 데이터 조회
- 벤치마크 비교
- 시장 데이터 분석

## 데이터 연동

자동매매 프로그램(32bit)과 SQLite 데이터베이스를 통해 연동:

```python
# 자동매매 데이터 읽기
from analysis.data_loader import load_trading_data

df = load_trading_data("../auto_trading/data/stocks.db")
```

## 사용 예시

### 성과 분석

```python
from analysis.performance import PerformanceAnalyzer

analyzer = PerformanceAnalyzer("../auto_trading/data/stocks.db")
analyzer.calculate_metrics()
analyzer.plot_equity_curve()
```

### 백테스팅

```python
from analysis.backtesting import BacktestEngine

engine = BacktestEngine()
results = engine.run_backtest(strategy="MA_CROSS", start_date="2024-01-01")
```

## 폴더 구조

```
analysis/
├── README.md                # 이 문서
├── requirements_64bit.txt   # 패키지 의존성
├── data_loader.py           # 데이터 로드
├── performance.py           # 성과 분석
├── visualization.py         # 시각화
├── backtesting.py           # 백테스팅
└── notebooks/               # Jupyter 노트북
```

## 64bit vs 32bit

| 기능 | 32bit (auto_trading) | 64bit (analysis) |
|------|---------------------|------------------|
| 키움 API | ✅ 필수 | ❌ 불가 |
| 자동매매 | ✅ 실행 | ❌ 분석만 |
| 고급 분석 | ❌ 제한적 | ✅ 전체 |
| 대용량 데이터 | ❌ 메모리 제한 | ✅ 무제한 |
| Visual Studio | ❌ 불필요 | ✅ 일부 필요 |

## 주의사항

⚠️ **이 모듈은 자동매매를 직접 실행하지 않습니다.**
- 자동매매는 `auto_trading` 폴더에서 32bit Python으로 실행
- 이 모듈은 분석, 시각화, 백테스팅만 수행

## 문제 해결

### Visual C++ 빌드 오류

일부 패키지(psutil, yfinance 등)는 Visual C++ 빌드 도구가 필요합니다.

**해결 방법:**
1. Microsoft C++ Build Tools 설치: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 또는 prebuilt wheel 사용 (대부분 자동)

### 메모리 부족

대용량 데이터 분석 시 메모리가 부족할 수 있습니다.

**해결 방법:**
- 데이터 기간 제한
- 청크 단위 처리
- 샘플링 사용

## 참고 문서

- [메인 README](../auto_trading/README.md)
- [설치 가이드](../auto_trading/docs/installation/GETTING_STARTED.md)
- [아키텍처 문서](ARCHITECTURE.md)

