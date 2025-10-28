# 신규 기능 통합 가이드

작성일: 2025-10-27

이 문서는 Phase 1-2에서 개발된 신규 기능들을 기존 시스템에 통합하는 방법을 설명합니다.

---

## 📋 통합 대상 기능

1. ✅ 수수료 계산 (이미 통합 완료)
2. ✅ 주문 제한 관리 (이미 통합 완료)
3. ⏸️ 뉴스 분석 (통합 필요)
4. ⏸️ 알림 시스템 (통합 필요)

---

## 🔧 1. 뉴스 분석 통합

### 1.1 trading_engine.py에 초기화 추가

```python
# 파일 상단 import 추가
from news_crawler import NewsCrawler
from sentiment_analyzer import SentimentAnalyzer
from news_strategy import NewsBasedStrategy, NewsEnhancedMultiStrategy
from notification import Notifier

class TradingEngine:
    def __init__(self, kiwoom: KiwoomAPI):
        # ... 기존 코드 ...
        
        # 뉴스 크롤러 초기화 (옵션)
        self.news_enabled = False  # Config에 추가 권장
        try:
            if Config.ENABLE_NEWS_ANALYSIS:  # 새로운 설정
                self.news_crawler = NewsCrawler()
                self.sentiment_analyzer = SentimentAnalyzer()
                self.news_strategy = NewsBasedStrategy(
                    self.news_crawler,
                    self.sentiment_analyzer
                )
                self.news_enabled = True
                log.info("뉴스 분석 기능 활성화")
        except Exception as e:
            log.warning(f"뉴스 분석 초기화 실패: {e}")
            self.news_enabled = False
        
        # 알림 시스템 초기화
        try:
            self.notifier = Notifier()
            log.info("알림 시스템 활성화")
        except Exception as e:
            log.warning(f"알림 시스템 초기화 실패: {e}")
            self.notifier = None
```

### 1.2 뉴스 자동 갱신 시작

```python
def start_trading(self):
    """자동매매 시작"""
    # ... 기존 코드 ...
    
    # 뉴스 자동 갱신 시작
    if self.news_enabled:
        self.news_crawler.start_auto_update(interval=300)  # 5분
        log.info("뉴스 자동 갱신 시작")
    
    # 시작 알림
    if self.notifier:
        self.notifier.notify_system_start()
```

### 1.3 뉴스 신호 통합

```python
def process_signal(self, stock_code: str, prices: List[float]):
    """매매 신호 처리"""
    try:
        # 기존 기술적 분석
        signal_result = self.strategy.generate_signal(prices)
        
        # 뉴스 분석 추가 (옵션)
        if self.news_enabled:
            is_holding = stock_code in self.risk_manager.positions
            news_result = self.news_strategy.generate_signal_for_stock(
                stock_code,
                is_holding
            )
            
            # 뉴스 점수가 강하면 반영
            if abs(news_result['news_score']) >= 50:
                log.info(
                    f"📰 뉴스 점수: {news_result['news_score']:+d}/100 "
                    f"- {news_result['reason']}"
                )
                
                # 신호 강도 조정
                if news_result['signal'] == signal_result['signal']:
                    # 같은 방향: 강화
                    signal_result['strength'] += news_result['strength'] * 0.5
                elif news_result['signal'] != SignalType.HOLD:
                    # 반대 방향: 약화
                    signal_result['strength'] *= 0.7
        
        # 매수/매도 실행
        if signal_result['signal'] == SignalType.BUY:
            self.execute_buy(stock_code, prices[-1], signal_result)
        elif signal_result['signal'] == SignalType.SELL:
            self.execute_sell(stock_code, prices[-1], signal_result)
    
    except Exception as e:
        log.error(f"신호 처리 중 오류: {e}")
```

---

## 🔔 2. 알림 시스템 통합

### 2.1 매수 체결 시 알림

```python
def execute_buy(self, stock_code, current_price, signal_result):
    # ... 기존 코드 ...
    
    if order_result:
        # ... 포지션 추가 ...
        
        # 알림 전송
        if self.notifier:
            stock_name = position.stock_name
            self.notifier.notify_trade(
                "매수",
                stock_name,
                quantity,
                current_price
            )
```

### 2.2 매도 체결 시 알림

```python
def execute_sell(self, stock_code, current_price, signal_result):
    # ... 기존 코드 ...
    
    if order_result:
        profit_loss = self.risk_manager.remove_position(...)
        
        # 알림 전송
        if self.notifier and profit_loss is not None:
            stock_name = position.stock_name
            self.notifier.notify_trade(
                "매도",
                stock_name,
                position.quantity,
                current_price,
                profit_loss
            )
```

### 2.3 급등주 감지 시 알림

```python
def on_surge_detected(self, stock_code, candidate):
    # ... 기존 코드 ...
    
    # 알림 전송
    if self.notifier:
        self.notifier.notify_surge(
            candidate.name,
            stock_code,
            candidate.current_change_rate,
            candidate.get_volume_ratio()
        )
```

### 2.4 손절매/익절매 알림

```python
def execute_exit(self, stock_code, sell_price, reason):
    # ... 기존 코드 ...
    
    if order_result:
        profit_loss = self.risk_manager.remove_position(...)
        
        # 알림 전송
        if self.notifier and profit_loss is not None:
            stock_name = position.stock_name
            
            if reason == "손절매":
                self.notifier.notify_stop_loss(
                    stock_name,
                    position.quantity,
                    position.buy_price,
                    sell_price,
                    abs(profit_loss)
                )
            elif reason == "익절매":
                self.notifier.notify_take_profit(
                    stock_name,
                    position.quantity,
                    position.buy_price,
                    sell_price,
                    profit_loss
                )
```

### 2.5 일일 손실 한도 알림

```python
def check_daily_loss_limit(self):
    # ... 기존 코드 ...
    
    if self.risk_manager.check_daily_loss_limit():
        # 알림 전송
        if self.notifier:
            stats = self.risk_manager.get_statistics()
            loss = stats['daily_loss']
            loss_rate = stats['daily_loss_rate']
            self.notifier.notify_daily_loss_limit(loss, loss_rate)
        
        # 자동매매 중지
        self.stop_trading()
```

---

## ⚙️ 3. config.py에 설정 추가

```python
# 뉴스 분석 기능
ENABLE_NEWS_ANALYSIS = os.getenv('ENABLE_NEWS_ANALYSIS', 'False').lower() == 'true'
NEWS_UPDATE_INTERVAL = int(os.getenv('NEWS_UPDATE_INTERVAL', '300'))  # 5분

# 알림 설정
ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'True').lower() == 'true'
ENABLE_SOUND_ALERTS = os.getenv('ENABLE_SOUND_ALERTS', 'True').lower() == 'true'
```

`.env` 파일에 추가:
```bash
# 뉴스 분석 (선택적)
ENABLE_NEWS_ANALYSIS=False  # 테스트 후 True로 변경
NEWS_UPDATE_INTERVAL=300

# 알림
ENABLE_NOTIFICATIONS=True
ENABLE_SOUND_ALERTS=True
```

---

## 📝 4. 점진적 통합 순서

### Step 1: 알림 시스템만 먼저 통합
```bash
# plyer 설치
pip install plyer

# .env 설정
ENABLE_NOTIFICATIONS=True

# 테스트 실행
python main.py
```

**확인 사항**:
- 프로그램 시작 시 알림 표시
- 매수/매도 시 알림 표시
- 알림 소리 재생

### Step 2: 뉴스 분석 기능 추가
```bash
# 패키지 설치
pip install requests beautifulsoup4

# .env 설정
ENABLE_NEWS_ANALYSIS=True

# 테스트 실행
python main.py
```

**확인 사항**:
- 뉴스 자동 갱신 로그 표시
- 뉴스 점수가 신호에 반영
- 뉴스 기반 매매 실행

### Step 3: 전체 통합 테스트
```bash
# 모의투자 모드로 하루 동안 실행
python main.py

# 로그 확인
tail -f logs/trading_2025-10-27.log

# 알림 이력 확인 (Python 콘솔)
>>> from notification import Notifier
>>> notifier = Notifier()
>>> notifier.print_history()
```

---

## 🧪 5. 테스트 체크리스트

### 수수료 계산 테스트:
- [ ] 모의투자: 수수료 0원 확인
- [ ] 실계좌 (주의): 수수료 정확히 적용 확인
- [ ] 손익분기점 로그 표시 확인

### 주문 제한 테스트:
- [ ] 초당 3건 초과 시 대기 로그
- [ ] 일일 100건 도달 시 주문 거부
- [ ] 주문 실패 시 재시도 동작

### 뉴스 분석 테스트:
- [ ] 뉴스 자동 갱신 (5분마다)
- [ ] 캐시에서 뉴스 조회
- [ ] 감성 분석 점수 계산
- [ ] 뉴스 신호가 매매에 반영

### 알림 시스템 테스트:
- [ ] Windows 토스트 알림 표시
- [ ] 소리 알림 재생
- [ ] 거래 알림 (매수/매도)
- [ ] 급등주 알림
- [ ] 손절매/익절매 알림
- [ ] 시스템 시작/종료 알림

---

## ⚠️ 주의사항

### 1. 뉴스 분석 사용 시:
- 처음에는 `ENABLE_NEWS_ANALYSIS=False`로 시작
- 며칠간 로그 확인 후 활성화
- 뉴스 점수가 매매에 과도하게 영향을 주지 않도록 주의

### 2. 알림 시스템:
- 과도한 알림은 성가실 수 있음
- 중요한 이벤트만 알림 설정 고려
- 소리 알림은 선택적으로 비활성화 가능

### 3. 성능:
- 뉴스 크롤링은 별도 스레드에서 실행 (블로킹 없음)
- 5분 간격으로 갱신 (과도한 요청 금지)
- 캐시 활용으로 빠른 조회

---

## 🐛 문제 해결

### 뉴스 크롤링 실패:
```python
# 로그 확인
# "뉴스 크롤링 오류" 메시지 확인

# 해결 방법:
1. 인터넷 연결 확인
2. 웹사이트 접근 가능 여부 확인
3. requests, beautifulsoup4 설치 확인
```

### 알림이 표시되지 않음:
```python
# 확인 사항:
1. Windows 인지 확인
2. plyer 설치 확인: pip show plyer
3. Windows 알림 설정 확인
4. ENABLE_NOTIFICATIONS=True 확인
```

### 뉴스 분석이 동작하지 않음:
```python
# 확인 사항:
1. ENABLE_NEWS_ANALYSIS=True 확인
2. 뉴스 갱신 로그 확인
3. 뉴스 크롤링 성공 여부 확인
4. 감성 분석 점수 로그 확인
```

---

## 📚 추가 참고

- `PHASE1_COMPLETE.md`: 수수료 및 주문 제한 상세
- `PHASE2_COMPLETE.md`: 뉴스 분석 및 알림 상세
- `IMPLEMENTATION_PROGRESS.md`: 전체 진행 상황
- 개별 모듈의 `if __name__ == "__main__"` 블록: 단위 테스트 예제

---

## 🚀 다음 단계

통합 완료 후:
1. Phase 3: 완전 자동화
2. Phase 3: GUI 개선
3. Phase 4: 스케줄러 및 헬스 체크

---

마지막 업데이트: 2025-10-27

