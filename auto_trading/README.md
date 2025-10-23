# CleonAI 자동매매 프로그램

키움증권 Open API를 활용한 PC 기반 Python 자동매매 시스템

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
- **자동 리스크 관리**: 손절매(-5%), 익절매(+10%), 포지션 사이징 자동화
- **실시간 모니터링**: 실시간 시세 데이터 기반 즉각 반응
- **모의투자 지원**: 안전한 테스트 환경에서 충분한 검증 가능
- **상세한 로깅**: 모든 거래 내역과 의사결정 과정 자동 기록

## 시스템 요구사항

- **운영체제**: Windows 10/11 (64비트)
- **Python**: 3.11 이상 **⚠️ 32비트 버전 필수** (키움 API 요구사항)
- **메모리**: 4GB RAM 이상
- **키움증권**: 계좌 + Open API+ 설치 + 공동인증서

> **중요**: 키움 Open API는 32비트 Python만 지원합니다.  
> 이미 64비트 Python을 사용 중이라면, 별도로 32비트를 설치하여 독립적으로 사용할 수 있습니다.  
> 자세한 내용: [SETUP_ISOLATED_PYTHON.md](SETUP_ISOLATED_PYTHON.md)

## 문서 가이드

### 처음 사용하는 경우

1. **[GETTING_STARTED.md](GETTING_STARTED.md)** ⭐ **추천**
   - 처음부터 끝까지 완전한 설치 가이드
   - 환경 설정부터 첫 실행까지 모든 단계 포함
   - 30-40분 소요 예상

### 이미 설정을 완료한 경우

2. **[QUICKSTART.md](QUICKSTART.md)**
   - 빠른 시작 가이드 (5분)
   - 기본 설정이 완료된 사용자용

### 추가 문서

3. **[KIWOOM_API_SETUP.md](KIWOOM_API_SETUP.md)**
   - 키움증권 Open API+ 신청 및 설치 상세 가이드
   - 모의투자 계좌 신청 방법
   - 공동인증서 준비

4. **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)**
   - 매매 전략 상세 설명
   - 전략 파라미터 조정 방법
   - 성과 평가 지표

5. **[FAQ.md](FAQ.md)**
   - 자주 묻는 질문과 답변
   - 일반적인 문제 해결 방법

6. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
   - 문제 해결 가이드
   - 에러 메시지별 대응 방법

## 빠른 시작 (요약)

### 🚀 원클릭 자동 설치 (권장)

PowerShell 관리자 권한으로:
```powershell
.\auto_setup_complete.ps1
```
→ Python 32비트 다운로드 + 설치 + 환경 구성 모두 자동!

자세한 내용: **[QUICK_INSTALL.md](QUICK_INSTALL.md)**

### 📝 단계별 설치

```bash
# 0. Python 32비트 설치 (처음 1회만) ⚠️ 필수
.\install_python32.ps1           # 자동 다운로드 + 설치
# 또는
.\setup_python32.ps1             # 이미 설치된 경우
# 또는
SETUP_ISOLATED_PYTHON.md 참고   # 수동 설치 가이드

# 1. 설치 스크립트 실행 (처음 1회만)
.\setup.ps1     # PowerShell (권장)
setup.bat       # CMD

# 2. .env 파일 설정
# 계좌번호, 비밀번호, 관심 종목 입력

# 3. 프로그램 실행
.\start.ps1     # PowerShell (권장)
start.bat       # CMD
```

## 프로젝트 구조

```
auto_trading/
├── README.md                    # 이 문서
├── QUICK_INSTALL.md             # 빠른 설치 가이드 ⭐ NEW
├── GETTING_STARTED.md           # 완전 설치 가이드
├── QUICKSTART.md                # 빠른 시작
├── KIWOOM_API_SETUP.md          # 키움 API 가이드
├── SETUP_ISOLATED_PYTHON.md     # Python 32비트 독립 설치 가이드 ⭐ NEW
├── STRATEGY_GUIDE.md            # 전략 설명
├── FAQ.md                       # 자주 묻는 질문
├── TROUBLESHOOTING.md           # 문제 해결
├── .env.example                 # 설정 템플릿
├── auto_setup_complete.ps1      # 완전 자동 설치 스크립트 ⭐ NEW
├── install_python32.ps1         # Python 32비트 자동 설치 ⭐ NEW
├── setup_python32.ps1           # Python 32비트 환경 구성 ⭐ NEW
├── setup.ps1                    # 설치 스크립트 (PowerShell)
├── setup.bat                    # 설치 스크립트 (CMD)
├── start.ps1                    # 실행 스크립트 (PowerShell)
├── start.bat                    # 실행 스크립트 (CMD)
├── requirements.txt             # 패키지 목록
├── main.py                      # 프로그램 진입점
├── config.py                    # 설정 관리
├── kiwoom_api.py                # 키움 API 래퍼
├── surge_detector.py            # 급등주 감지 ⭐ NEW
├── indicators.py                # 기술적 지표
├── strategies.py                # 매매 전략
├── risk_manager.py              # 리스크 관리
├── trading_engine.py            # 자동매매 엔진
├── logger.py                    # 로깅 시스템
└── logs/                        # 로그 파일
```

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

1. [FAQ.md](FAQ.md) 확인
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 확인
3. 로그 파일 확인 (`logs/trading.log`, `logs/error.log`)

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
