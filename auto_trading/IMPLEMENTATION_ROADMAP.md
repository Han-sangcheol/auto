# 자동매매 프로그램 구현 로드맵

작성일: 2025-10-27
최종 업데이트: 2025-10-27

## 📊 전체 진행 상황

```
Phase 1: 키움 API 규칙 적용          [████████████] 100% ✅
Phase 2: 감성 분석 모듈              [████████████] 100% ✅
Phase 3: 완전 자동화 & 알림 통합     [████████████] 100% ✅
Phase 4: GUI 개선 & AI 통합          [░░░░░░░░░░░░]   0% ⏳
────────────────────────────────────────────────────────
전체 진행률:                         [█████████░░░]  75%
```

---

## Phase 1: 키움 API 규칙 적용 ✅

**목표**: 정확한 수수료 계산 및 API 제한 준수

### 완료 항목

#### 1.1 수수료 계산 모듈
- ✅ `fee_calculator.py` 생성
  - 매수 수수료: 0.015%
  - 매도 수수료: 0.015%
  - 매도세: 0.23%
  - 유관기관 수수료: 0.0036396%
  - 모의투자 시 수수료 0원 처리
- ✅ `risk_manager.py` 통합
  - `add_position()`: 매수 수수료 차감
  - `remove_position()`: 매도 수수료 및 세금 차감
  - 순수익률 정확 계산
- ✅ `monitor_gui.py` 표시
  - 총 수수료 현황 표시

#### 1.2 주문 제한 관리
- ✅ `kiwoom_api.py` 개선
  - 일일 주문 한도: 100건
  - 초당 주문 한도: 3건
  - `_wait_for_order()` 메서드 구현
  - 주문 실패 시 재시도 로직 (최대 3회)
  - 주문 통계 추적 (`get_order_statistics()`)
  - 일일 카운트 리셋 기능 (`reset_daily_order_count()`)
- ✅ `trading_engine.py` 초기화
  - 시작 시 일일 카운트 자동 리셋

### 성과
- 💰 **실제 수익률 정확도**: 수수료 반영으로 현실적인 성과 예측 가능
- 🛡️ **API 안정성**: 과부하 방지로 계좌 정지 위험 제거
- 📊 **투명성**: 모든 비용 항목 상세 로깅

### 관련 문서
- `auto_trading/fee_calculator.py`
- `auto_trading/PHASE1_COMPLETE.md`

---

## Phase 2: 감성 분석 모듈 ✅

**목표**: 뉴스 기반 매매 신호 생성

### 완료 항목

#### 2.1 뉴스 크롤링
- ✅ `news_crawler.py` 생성
  - 네이버 금융 뉴스 수집
  - BeautifulSoup4 사용
  - 제목, 본문, 링크, 출처 수집
  - 5분 간격 자동 갱신 (설정 가능)
  - 에러 처리 강화

#### 2.2 감성 분석
- ✅ `sentiment_analyzer.py` 생성
  - 키워드 기반 긍정/부정 분석
  - 긍정 키워드: "상승", "호재", "증가", "강세" 등
  - 부정 키워드: "하락", "악재", "감소", "약세" 등
  - 감성 점수 계산 (-100 ~ +100)
  - AI 모델 통합 준비 (인터페이스 정의)

#### 2.3 뉴스 기반 전략
- ✅ `news_strategy.py` 생성
  - `NewsBasedStrategy` 클래스
  - 긍정 뉴스 ≥ 30점: 매수 신호
  - 부정 뉴스 ≤ -30점: 매도 신호
  - 기존 기술적 전략과 결합 가능

#### 2.4 설정 통합
- ✅ `config.py`에 뉴스 설정 추가
  - `ENABLE_NEWS_ANALYSIS`
  - `NEWS_UPDATE_INTERVAL`
  - `NEWS_BUY_THRESHOLD`
  - `NEWS_SELL_THRESHOLD`

### 성과
- 📰 **시장 반응 포착**: 실시간 뉴스로 빠른 대응
- 🧠 **지능형 매매**: 기술적 분석 + 뉴스 분석 결합
- 🔧 **확장 가능**: AI 모델 통합 준비 완료

### 제한사항
- ⏳ 현재는 키워드 기반 분석만 지원
- ⏳ AI 모델(KoBERT 등)은 Phase 4에서 통합 예정
- ⏳ 네이버 금융만 지원 (향후 다음, 한경 추가 예정)

### 관련 문서
- `auto_trading/news_crawler.py`
- `auto_trading/sentiment_analyzer.py`
- `auto_trading/news_strategy.py`
- `auto_trading/PHASE2_COMPLETE.md`

---

## Phase 3: 완전 자동화 & 알림 통합 ✅

**목표**: 24시간 무인 운영 및 실시간 알림

### 완료 항목

#### 3.1 Trading Engine 통합
- ✅ 뉴스 분석 모듈 통합
  - 선택적 로드 (ImportError 처리)
  - `initialize()`에서 초기화
  - 자동 뉴스 갱신 시작/중지
- ✅ 알림 시스템 통합
  - 선택적 로드
  - 모든 주요 이벤트에 알림 추가
  - 에러 발생 시에도 안정적 동작

#### 3.2 알림 시스템
- ✅ `notification.py` 생성
  - **Windows 토스트 알림**: win10toast 사용
  - **소리 알림**: winsound 사용 (기본 내장)
  - **알림 종류**:
    - 매수/매도 체결
    - 급등주 감지
    - 손절매/익절매
    - 일일 손실 한도 도달
    - 시스템 시작/종료
    - 에러 발생
  - **소리 구분**: 이벤트별 다른 주파수/패턴

#### 3.3 설정 시스템
- ✅ `config.py` 확장
  - 뉴스 분석 설정
  - 알림 설정 (`ENABLE_NOTIFICATIONS`, `ENABLE_SOUND_ALERTS`)
- ✅ `env.template` 업데이트
  - 상세 설명 추가
  - 권장값 명시
  - 패키지 요구사항 안내

#### 3.4 완전 자동화
- ✅ 급등주 자동 승인 기본값 (SURGE_AUTO_APPROVE=True)
- ✅ 모든 수동 입력 제거
- ✅ 에러 발생 시 기능만 비활성화 (프로그램 계속 실행)
- ✅ 에러 복구 준비 (`error_count`, `max_errors`)

### 성과
- 🤖 **완전 무인 운영**: 사용자 개입 없이 24시간 자동 실행
- 🔔 **실시간 모니터링**: 중요 이벤트 즉시 알림
- 🛡️ **안정성**: 패키지 미설치/에러 발생 시에도 정상 동작
- 🎨 **사용자 경험**: 소리로 이벤트 종류 구분

### 패키지 요구사항
**필수**:
```
pywin32==306
loguru==0.7.2
python-dotenv==1.0.0
pandas==2.1.3
numpy==1.26.2
PyQt5==5.15.10
```

**선택적**:
```
# 뉴스 분석
beautifulsoup4==4.12.2
requests==2.31.0

# 알림
win10toast==0.9
```

### 관련 문서
- `auto_trading/notification.py`
- `auto_trading/PHASE3_AUTOMATION_COMPLETE.md`

---

## Phase 4: GUI 개선 & AI 통합 ⏳

**목표**: 향상된 시각화 및 AI 기반 분석

### 계획 항목

#### 4.1 에러 자동 복구
- ⏳ API 연결 끊김 자동 재연결
- ⏳ 프로그램 비정상 종료 시 자동 재시작
- ⏳ 헬스 체크 시스템 (`health_monitor.py`)
- ⏳ 리소스 모니터링 (CPU, 메모리)

#### 4.2 GUI 차트 기능
- ⏳ `chart_widget.py` 생성
- ⏳ matplotlib 또는 pyqtgraph 사용
- ⏳ 실시간 가격 차트 (종목별)
- ⏳ 수익률 차트 (시간별)
- ⏳ 거래량 차트

#### 4.3 GUI 상세 통계
- ⏳ `monitor_gui.py` 확장
- ⏳ 일별/주별/월별 수익률
- ⏳ 전략별 성과 분석
- ⏳ 승률, 평균 수익, 최대 손실
- ⏳ 거래 히스토리 테이블

#### 4.4 설정 UI
- ⏳ `settings_dialog.py` 생성
- ⏳ 매매 전략 파라미터 조정
- ⏳ 리스크 관리 설정 변경
- ⏳ 급등주 감지 기준 조정
- ⏳ 실시간 설정 적용

#### 4.5 AI 감성 분석
- ⏳ KoBERT 또는 KoGPT 모델 통합
- ⏳ Hugging Face 모델 로컬 실행
- ⏳ 뉴스 감성 분석 정확도 향상
- ⏳ 실시간 분석 성능 최적화

#### 4.6 스케줄러
- ⏳ `scheduler.py` 생성
- ⏳ Windows 작업 스케줄러 연동
- ⏳ 장 시작 30분 전 자동 실행 (8:30)
- ⏳ 장 마감 후 자동 종료 (16:00)
- ⏳ 공휴일 자동 스킵

### 예상 효과
- 📊 **향상된 시각화**: 실시간 차트로 직관적 모니터링
- ⚙️ **편리한 설정**: GUI에서 모든 파라미터 조정
- 🤖 **AI 분석**: 정확한 뉴스 감성 분석
- 🔄 **자동 관리**: 완전 무인 운영 (시작/종료 자동화)

---

## 🎯 주요 성과

### Phase 1-3 완료로 달성한 목표
1. ✅ **정확한 손익 계산**: 수수료 반영
2. ✅ **API 안정성**: 과부하 방지
3. ✅ **지능형 매매**: 뉴스 분석 기반 신호
4. ✅ **완전 자동화**: 24시간 무인 운영
5. ✅ **실시간 알림**: 중요 이벤트 즉시 통지
6. ✅ **모듈화**: 선택적 기능 활성화
7. ✅ **안정성**: 에러 발생 시에도 동작

### 남은 과제
1. ⏳ GUI 개선 (차트, 통계, 설정)
2. ⏳ AI 모델 통합
3. ⏳ 에러 자동 복구
4. ⏳ 스케줄러 자동화

---

## 📦 프로젝트 구조

```
auto_trading/
├── main.py                    # 메인 실행 파일
├── config.py                  # 설정 관리 ✅ (Phase 3)
├── logger.py                  # 로깅 시스템
├── kiwoom_api.py              # 키움 API 래퍼 ✅ (Phase 1)
├── indicators.py              # 기술적 지표
├── strategies.py              # 매매 전략
├── risk_manager.py            # 리스크 관리 ✅ (Phase 1)
├── fee_calculator.py          # 수수료 계산 ✅ (Phase 1)
├── trading_engine.py          # 자동매매 엔진 ✅ (Phase 3)
├── surge_detector.py          # 급등주 감지
├── monitor_gui.py             # GUI 모니터 ✅ (Phase 1)
│
├── news_crawler.py            # 뉴스 크롤링 ✅ (Phase 2)
├── sentiment_analyzer.py      # 감성 분석 ✅ (Phase 2)
├── news_strategy.py           # 뉴스 전략 ✅ (Phase 2)
├── notification.py            # 알림 시스템 ✅ (Phase 3)
│
├── requirements.txt           # 필수 패키지
├── requirements_extended.txt  # 선택적 패키지 (Phase 2-3)
├── env.template               # 설정 템플릿 ✅ (Phase 3)
│
├── logs/                      # 로그 디렉토리
├── PHASE1_COMPLETE.md         # Phase 1 문서
├── PHASE2_COMPLETE.md         # Phase 2 문서
├── PHASE3_AUTOMATION_COMPLETE.md  # Phase 3 문서
└── IMPLEMENTATION_ROADMAP.md  # 본 파일
```

---

## 🚀 빠른 시작

### 1. 기본 기능만 사용 (알림 없이)
```powershell
# 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 기본 패키지만 설치
pip install -r requirements.txt

# .env 파일 설정
copy env.template .env
# .env 편집하여 계좌 정보 입력

# 프로그램 실행
python main.py
```

### 2. 알림 시스템 사용
```powershell
# win10toast 설치
pip install win10toast

# .env 파일 수정
# ENABLE_NOTIFICATIONS=True

# 프로그램 실행
python main.py
```

### 3. 뉴스 분석 사용
```powershell
# 추가 패키지 설치
pip install beautifulsoup4 requests

# .env 파일 수정
# ENABLE_NEWS_ANALYSIS=True

# 프로그램 실행
python main.py
```

---

## 📞 문제 해결

### 일반적인 문제
1. **import 오류**:
   - 필수 패키지: `pip install -r requirements.txt`
   - 선택적 패키지: `pip install beautifulsoup4 requests win10toast`

2. **알림 안 뜸**:
   - Windows 10 이상 필요
   - `ENABLE_NOTIFICATIONS=True` 확인
   - `pip install win10toast` 실행

3. **뉴스 크롤링 실패**:
   - 인터넷 연결 확인
   - `ENABLE_NEWS_ANALYSIS=False`로 비활성화 가능

4. **키움 API 오류**:
   - 키움 OpenAPI 설치 확인
   - 로그인 확인
   - 계좌번호/비밀번호 확인

### 로그 확인
```powershell
# 실시간 로그 확인
Get-Content logs\trading.log -Wait -Tail 50

# 에러 로그만 확인
Get-Content logs\error.log -Wait -Tail 20
```

---

## 📝 기여 가이드

### 코드 스타일
- PEP 8 준수
- 타입 힌트 사용
- Docstring (Google 스타일)

### 테스트
- 단위 테스트: `pytest`
- 통합 테스트: 모의투자 환경
- 최소 1주일 검증 후 실계좌 사용

### 문서화
- 주요 기능 추가 시 README 업데이트
- Phase 완료 시 별도 문서 작성
- 설정 변경 시 env.template 업데이트

---

**작성자**: CleonAI Auto Trading Team
**최종 업데이트**: 2025-10-27
**다음 Phase**: Phase 4 - GUI 개선 & AI 통합

