# 🏗️ CleonAI 아키텍처 문서

## ⚠️ 절대 변경 금지 - 2025-11-05 확정

이 문서는 프로젝트의 핵심 아키텍처를 정의합니다. **절대로 수정하지 마십시오!**

---

## 🎯 핵심 결정 사항

### 1. 하이브리드 Python 환경 (32bit/64bit)

**결정일**: 2025-11-05  
**이유**: 키움 API 32bit 제약 + 고급 분석 64bit 요구사항

```
D:\cleonAI\
│
├── .venv32\              # Python 3.11.9 (32bit)
│   └── 용도: 키움 API 자동매매만
│
└── .venv\                # Python 3.11+ (64bit)
    └── 용도: 나머지 모든 것
```

### 2. 모듈 분리

| 모듈 | Python 버전 | 용도 | 패키지 |
|------|------------|------|--------|
| **auto_trading** | 32bit | 키움 API 자동매매 | requirements_32bit.txt |
| **backend** | 64bit | FastAPI 서버 | requirements.txt |
| **frontend** | 64bit | PyQt GUI | requirements.txt |
| **analysis** | 64bit | 데이터 분석 | requirements_64bit.txt |
| **trading-engine** | 64bit | 트레이딩 로직 | requirements.txt |

### 3. 데이터 공유 방식

**방법**: SQLite 데이터베이스

```
auto_trading (32bit)
    ↓ 쓰기
SQLite DB (auto_trading/data/stocks.db)
    ↓ 읽기
analysis (64bit)
```

---

## 📦 패키지 관리 정책

### 절대 규칙

1. **requirements 파일 통합 금지**
   - `requirements_32bit.txt` → auto_trading만
   - `requirements_64bit.txt` → analysis만
   - `requirements.txt` → backend, frontend, trading-engine

2. **빌드 필요 패키지는 64bit로**
   - psutil, yfinance, pandas-ta
   - Visual C++ 빌드 필요 패키지
   - 32bit에서 실패하는 모든 패키지

3. **32bit 패키지 최소화**
   - PyQt5 (키움 API)
   - numpy, pandas (기본 버전)
   - dotenv, loguru
   - 빌드 불필요 패키지만

---

## 🔄 실행 흐름

### 자동매매 (32bit)

```powershell
# 1. 가상환경 활성화
cd D:\cleonAI\auto_trading
..\.venv32\Scripts\Activate.ps1

# 2. 패키지 설치 (처음 1회)
pip install -r requirements_32bit.txt

# 3. 실행
python main.py
```

### 데이터 분석 (64bit)

```powershell
# 1. 가상환경 활성화
cd D:\cleonAI\analysis
..\.venv\Scripts\Activate.ps1

# 2. 패키지 설치 (처음 1회)
pip install -r requirements_64bit.txt

# 3. 분석/시각화
jupyter notebook
```

---

## 🚫 금지 사항

### 절대 하지 말 것

1. ❌ **auto_trading을 64bit Python으로 실행**
   - 키움 API 초기화 실패
   - QAxWidget 오류 발생

2. ❌ **requirements_32bit.txt에 빌드 필요 패키지 추가**
   - psutil, yfinance, pandas-ta 등
   - Visual C++ 오류 발생

3. ❌ **두 requirements 파일 통합**
   - 32bit/64bit 패키지 충돌
   - 설치 실패

4. ❌ **SQLite DB 동시 쓰기**
   - 32bit와 64bit가 동시에 쓰기 시도
   - DB 잠금 오류

---

## ✅ 올바른 사용 패턴

### 패턴 1: 실시간 매매 + 모니터링

```powershell
# 터미널 1 (32bit)
cd auto_trading
..\.venv32\Scripts\Activate.ps1
python main.py

# 터미널 2 (64bit)
cd analysis
..\.venv\Scripts\Activate.ps1
jupyter notebook
# → 실시간 대시보드
```

### 패턴 2: 백테스팅

```powershell
# 1. 데이터 수집 (32bit)
cd auto_trading
python main.py  # 자동매매 실행 → DB 저장

# 2. 백테스팅 (64bit)
cd ../analysis
jupyter notebook
# → 수집된 데이터로 전략 테스트
```

### 패턴 3: 전략 최적화

```powershell
# 1. 파라미터 최적화 (64bit)
cd analysis
python optimize_strategy.py

# 2. 실전 적용 (32bit)
cd ../auto_trading
# config.py 수정 (최적화된 파라미터)
python main.py
```

---

## 📚 관련 문서

### 필수 문서

1. **[auto_trading/HYBRID_ARCHITECTURE.md](auto_trading/HYBRID_ARCHITECTURE.md)** ⭐
   - 하이브리드 아키텍처 상세 설명

2. **[auto_trading/README.md](auto_trading/README.md)**
   - 자동매매 사용 가이드

3. **[analysis/README.md](analysis/README.md)**
   - 데이터 분석 가이드

4. **[auto_trading/docs/installation/PYTHON_32BIT_SETUP.md](auto_trading/docs/installation/PYTHON_32BIT_SETUP.md)**
   - 32bit Python 설치 방법

### 참고 문서

- [프로젝트 정상화 완료](auto_trading/NORMALIZATION_COMPLETE.md)
- [Python 32bit 업데이트](auto_trading/PYTHON_32BIT_UPDATE.md)
- [키움 API 설정](auto_trading/docs/installation/KIWOOM_API_SETUP.md)

---

## 🎯 설계 원칙

### 1. 명확한 책임 분리

- **32bit**: 키움 API 자동매매만
- **64bit**: 나머지 모든 것

### 2. 최소 의존성

- 32bit 패키지를 최소화
- 빌드 도구 불필요하게 유지

### 3. 안전한 데이터 공유

- SQLite를 통한 표준 데이터 교환
- 파일 잠금 방지

### 4. 독립적 실행

- 각 모듈이 독립적으로 실행 가능
- 상호 의존성 최소화

---

## 🔍 문제 해결

### Q1: 왜 하이브리드 구조?

**A**: 키움 API 제약(32bit) + 고급 분석 요구(64bit) 때문

### Q2: 모든 것을 32bit로 하면?

**A**: 많은 최신 패키지가 32bit 미지원 (pandas-ta, yfinance 등)

### Q3: 모든 것을 64bit로 하면?

**A**: 키움 API 사용 불가 (QAxWidget 오류)

### Q4: 다른 방법은 없나?

**A**: 현재 하이브리드 구조가 최선의 방법

---

## 📊 변경 이력

| 날짜 | 내용 | 작성자 |
|------|------|--------|
| 2025-11-05 | 하이브리드 아키텍처 확정 | CleonAI Team |
| 2025-11-05 | requirements 분리 | CleonAI Team |
| 2025-11-05 | 문서 작성 | CleonAI Team |

---

**마지막 업데이트**: 2025-11-05  
**버전**: 1.0  
**상태**: 확정 (변경 금지)

