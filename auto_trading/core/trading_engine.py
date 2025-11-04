"""
자동매매 엔진 모듈

[파일 역할]
전체 매매 프로세스를 자동화하는 핵심 엔진입니다.
모든 구성 요소를 통합하여 자동매매를 실행합니다.

[주요 기능]
1. 초기화
   - 계좌 정보 조회
   - 보유 종목 확인
   - 관심 종목 등록
   - 실시간 시세 구독

2. 실시간 모니터링
   - 실시간 가격 데이터 수신
   - 가격 히스토리 누적
   - 매매 신호 분석

3. 자동 매매 실행
   - 매수/매도 신호 감지
   - 리스크 관리 검증
   - 주문 전송
   - 체결 확인

4. 리스크 관리
   - 손절매/익절매 모니터링
   - 일일 손실 한도 확인
   - 포지션 관리

[흐름]
초기화 → 실시간 데이터 수신 → 신호 생성 → 리스크 검증 → 주문 실행 → 반복

[사용 방법]
engine = TradingEngine(kiwoom_api)
engine.initialize()
engine.start_trading()

[수정 내역 - 2025-10-26]
- GUI 응답없음 문제 해결을 위해 QTimer 기반으로 변경
- 블로킹 while 루프 제거
- PyQt 이벤트 루프와 통합하여 논블로킹 방식으로 동작
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, time as dt_time
import time
from collections import defaultdict
import threading
import traceback
import json
import os

from PyQt5.QtCore import QTimer

from core.kiwoom_api import KiwoomAPI
from core.strategies import MultiStrategy, SignalType, create_default_strategies
from core.risk_manager import RiskManager
from core.indicators import calculate_all_indicators
from features.surge_detector import SurgeDetector
from features.market_scheduler import MarketScheduler, MarketState
from utils.logger import log
from config import Config

# 뉴스 분석 및 알림 시스템 (선택적 로드)
try:
    from features.news_crawler import NewsCrawler
    from features.sentiment_analyzer import SentimentAnalyzer
    from features.news_strategy import NewsBasedStrategy
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    log.warning("뉴스 분석 모듈을 로드할 수 없습니다. (패키지 미설치)")

try:
    from utils.notification import Notifier
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    log.warning("알림 시스템을 로드할 수 없습니다. (win10toast 미설치)")

try:
    from features.health_monitor import HealthMonitor
    HEALTH_MONITOR_AVAILABLE = True
except ImportError:
    HEALTH_MONITOR_AVAILABLE = False
    log.warning("헬스 모니터를 로드할 수 없습니다. (psutil 미설치)")

try:
    from features.scheduler import TradingScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    log.warning("스케줄러를 로드할 수 없습니다.")


class TradingEngine:
    """자동매매 엔진 클래스"""
    
    def __init__(self, kiwoom: KiwoomAPI):
        self.kiwoom = kiwoom
        self.risk_manager = RiskManager()
        
        # 전략 초기화
        base_strategies = create_default_strategies(Config)
        self.strategy = MultiStrategy(
            base_strategies,
            Config.MIN_SIGNAL_STRENGTH
        )
        
        # 가격 데이터 저장 (종목별)
        self.price_history: Dict[str, List[float]] = defaultdict(list)
        
        # 🔄 데이터베이스 저장 기능 제거 - 외부 데이터 소스(yfinance) 사용
        # 차트는 advanced_chart_widget.py에서 yfinance로 조회하여 표시
        
        # 📦 거래 이력 블랙박스 데이터베이스
        from database.trading_history_db import TradingHistoryDB
        self.history_db = TradingHistoryDB(
            db_path=os.path.join(Config.LOG_DIR, "trading_history.db")
        )
        
        # 실행 상태
        self.is_running = False
        self.watch_list = Config.WATCH_LIST.copy()  # 복사본 사용 (동적 추가 가능)
        
        # 통계
        self.last_check_time = {}
        self.signal_count = 0
        
        # 급등주 감지기
        self.surge_detector: Optional[SurgeDetector] = None
        self.surge_approval_callback: Optional[Callable] = None
        self.surge_detected_stocks = set()  # 이미 추가된 급등주 추적
        self.surge_add_lock = threading.Lock()  # 급등주 추가 시 동기화
        self.surge_processing = False  # 급등주 처리 중 플래그
        
        # 뉴스 분석 (선택적)
        self.news_enabled = False
        self.news_crawler = None
        self.sentiment_analyzer = None
        self.news_strategy = None
        
        # 알림 시스템 (선택적)
        self.notifier = None
        
        # 헬스 모니터 (선택적)
        self.health_monitor = None
        
        # 스케줄러 (선택적)
        self.scheduler = None
        
        # 시장 스케줄러 (필수)
        self.market_scheduler = MarketScheduler()
        
        # GUI 모니터 창 (선택적)
        self.monitor_window = None
        
        # QTimer 설정 (GUI 응답없음 문제 해결)
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._periodic_check)
        self.check_timer.setInterval(5000)  # 5초마다 체크
        
        # 에러 복구 카운트
        self.error_count = 0
        self.max_errors = 5
        self.last_error_time = None
        
        log.info("자동매매 엔진 초기화 완료")
    
    def set_monitor_window(self, window):
        """모니터 창 설정"""
        self.monitor_window = window
    
    def _add_gui_log(self, message: str, color: str = "black"):
        """GUI 로그 추가 (모니터 창이 있을 때만)"""
        if self.monitor_window:
            try:
                self.monitor_window.add_log(message, color)
            except:
                pass  # GUI 로그 실패해도 무시
    
    def _add_chart_marker(self, stock_code: str, trade_type: str, price: float):
        """차트에 매매 마커 추가 (모니터 창 차트가 있을 때만)"""
        if self.monitor_window and hasattr(self.monitor_window, 'chart_widget'):
            try:
                if self.monitor_window.chart_widget:
                    # 🆕 매수 시 차트에 종목 자동 추가
                    if trade_type.lower() == 'buy':
                        position = self.risk_manager.positions.get(stock_code)
                        if position:
                            self.monitor_window.chart_widget.add_stock(
                                stock_code,
                                position.stock_name
                            )
                    
                    # 매매 마커 추가
                    self.monitor_window.chart_widget.add_trade_marker(
                        stock_code, trade_type, price
                    )
            except:
                pass  # 차트 마커 실패해도 무시
    
    def initialize(self) -> bool:
        """
        엔진 초기화
        
        Returns:
            초기화 성공 여부
        """
        try:
            log.info("자동매매 엔진 초기화 중...")
            
            # 로그인 후 대기 (API 안정화)
            import time
            log.info("⏳ API 안정화 대기 (3초)...")
            time.sleep(3)
            
            # 1. 계좌 정보 조회
            log.info("1️⃣ 계좌 정보 조회 중...")
            balance_info = self.kiwoom.get_balance()
            if not balance_info:
                log.warning("잔고 조회 실패 - 기본값 사용 (모의투자 초기 자금)")
                # 모의투자 기본 초기 자금: 10,000,000원
                cash = 10000000
            else:
                cash = balance_info.get('cash', 10000000)
            
            self.risk_manager.set_initial_balance(cash)
            log.info(f"계좌 잔고: {cash:,}원")
            
            # API 호출 간격 확보
            time.sleep(2)
            
            # 2. 보유 종목 조회
            log.info("2️⃣ 보유 종목 조회 중...")
            holdings = self.kiwoom.get_holdings()
            if holdings:
                log.info(f"보유 종목: {len(holdings)}개")
            else:
                log.info("보유 종목: 0개 (초기 상태)")
            
            for holding in holdings:
                self.risk_manager.add_position(
                    holding['code'],
                    holding['name'],
                    holding['quantity'],
                    holding['buy_price']
                )
            
            # 🆕 데이터베이스에서 매도 금지 상태 복원
            try:
                open_positions = self.history_db.get_open_positions()
                for db_pos in open_positions:
                    stock_code = db_pos['stock_code']
                    if stock_code in self.risk_manager.positions:
                        position = self.risk_manager.positions[stock_code]
                        position.sell_blocked = bool(db_pos.get('sell_blocked', 0))
                        position.db_position_id = db_pos['position_id']
                        if position.sell_blocked:
                            log.info(f"   📌 매도 금지 복원: {position.stock_name}({stock_code})")
            except Exception as restore_error:
                log.warning(f"⚠️  매도 금지 상태 복원 실패: {restore_error}")
            
            # API 호출 간격 확보
            time.sleep(1)
            
            # 3. 실시간 시세 등록 (관심 종목 + 보유 종목)
            log.info("3️⃣ 실시간 시세 등록 중...")
            self.kiwoom.set_real_data_callback(self.on_price_update)
            # 🆕 호가 데이터 콜백 설정 (선제적 매수 판단)
            self.kiwoom.callbacks['order_book_data'] = self.on_order_book_update
            log.info("✅ 호가 데이터 콜백 설정 완료")
            
            # 🆕 관심 종목 + 보유 종목을 모두 실시간 등록
            all_stocks = list(set(self.watch_list + [p.stock_code for p in self.risk_manager.positions.values()]))
            if all_stocks:
                log.info(f"   등록 종목: {len(all_stocks)}개 (관심: {len(self.watch_list)}개, 보유: {len(self.risk_manager.positions)}개)")
                self.kiwoom.register_real_data(all_stocks)
            else:
                log.warning("   등록할 종목이 없습니다.")
            
            # API 안정화를 위한 추가 대기
            time.sleep(2)
            
            # 4. 급등주 감지기 초기화 (옵션) - 재시도 로직 포함
            if Config.ENABLE_SURGE_DETECTION:
                log.info("4️⃣ 급등주 감지 기능 활성화 중...")
                self.surge_detector = SurgeDetector(
                    self.kiwoom,
                    self.on_surge_detected
                )
                
                # 재시도 로직 (최대 3회)
                max_retries = 3
                for attempt in range(max_retries):
                    if attempt > 0:
                        wait_time = 5 * attempt  # 5초, 10초
                        log.info(f"   ⏳ 재시도 대기 ({wait_time}초)...")
                        time.sleep(wait_time)
                        log.info(f"   🔄 급등주 감지기 초기화 재시도 ({attempt + 1}/{max_retries})")
                    
                    if self.surge_detector.initialize():
                        log.success("✅ 급등주 감지 기능 활성화 완료")
                        
                        # 🆕 저장된 관심주 복원
                        try:
                            log.info("   📂 저장된 관심주 로드 중...")
                            watchlist = self.surge_detector.load_watchlist()
                            
                            if watchlist:
                                log.info(f"   관심주 {len(watchlist)}개 복원 시작...")
                                for item in watchlist:
                                    stock_code = item['code']
                                    stock_name = item['name']
                                    
                                    # 현재가 조회
                                    stock_info = self.kiwoom.get_stock_info(stock_code)
                                    if stock_info:
                                        success = self.surge_detector.add_watchlist_candidate(
                                            stock_code=stock_code,
                                            stock_name=stock_name,
                                            current_price=stock_info['current_price'],
                                            change_rate=stock_info['change_rate']
                                        )
                                        if success:
                                            log.info(f"   ⭐ 관심주 복원: {stock_name}({stock_code})")
                                        time.sleep(0.5)  # API 호출 간격
                                    else:
                                        log.warning(f"   ⚠️  종목 정보 조회 실패: {stock_name}({stock_code})")
                                
                                log.success(f"✅ 관심주 {len(watchlist)}개 복원 완료")
                            else:
                                log.info("   저장된 관심주 없음")
                                
                        except Exception as watchlist_error:
                            log.warning(f"⚠️  관심주 복원 실패: {watchlist_error}")
                        
                        break
                    else:
                        if attempt < max_retries - 1:
                            log.warning(f"   ⚠️  급등주 감지 기능 초기화 실패 - 재시도 예정")
                        else:
                            log.warning("⚠️  급등주 감지 기능 초기화 최종 실패 - 기능 비활성화")
                            self.surge_detector = None
            
            # 5. 일일 주문 카운트 리셋
            self.kiwoom.reset_daily_order_count()
            
            # 6. 뉴스 분석 초기화 (선택적)
            if NEWS_AVAILABLE and hasattr(Config, 'ENABLE_NEWS_ANALYSIS'):
                try:
                    if Config.ENABLE_NEWS_ANALYSIS:
                        log.info("뉴스 분석 기능 초기화 중...")
                        self.news_crawler = NewsCrawler()
                        self.sentiment_analyzer = SentimentAnalyzer()
                        self.news_strategy = NewsBasedStrategy(
                            self.news_crawler,
                            self.sentiment_analyzer
                        )
                        self.news_enabled = True
                        log.success("뉴스 분석 기능 활성화 완료")
                except Exception as e:
                    log.warning(f"뉴스 분석 초기화 실패: {e}")
                    self.news_enabled = False
            
            # 7. 알림 시스템 초기화 (선택적)
            if NOTIFICATION_AVAILABLE:
                try:
                    self.notifier = Notifier(
                        enable_sound=getattr(Config, 'ENABLE_SOUND_ALERTS', True)
                    )
                    log.success("알림 시스템 활성화 완료")
                except Exception as e:
                    log.warning(f"알림 시스템 초기화 실패: {e}")
                    self.notifier = None
            
            # 8. 헬스 모니터 초기화 (선택적)
            if HEALTH_MONITOR_AVAILABLE:
                try:
                    check_interval = getattr(Config, 'HEALTH_CHECK_INTERVAL', 60)
                    enable_auto_recovery = getattr(Config, 'ENABLE_AUTO_RECOVERY', True)
                    
                    self.health_monitor = HealthMonitor(
                        trading_engine=self,
                        kiwoom_api=self.kiwoom,
                        check_interval=check_interval,
                        enable_auto_recovery=enable_auto_recovery
                    )
                    log.success(f"헬스 모니터 활성화 완료 (체크 간격: {check_interval}초)")
                except Exception as e:
                    log.warning(f"헬스 모니터 초기화 실패: {e}")
                    self.health_monitor = None
            
            # 9. 스케줄러 초기화 (선택적)
            if SCHEDULER_AVAILABLE and getattr(Config, 'ENABLE_AUTO_SHUTDOWN', False):
                try:
                    self.scheduler = TradingScheduler(
                        enable_auto_shutdown=True,
                        shutdown_callback=self._safe_shutdown
                    )
                    log.success(f"자동 종료 스케줄러 활성화 (종료 시간: {TradingScheduler.AUTO_STOP_TIME})")
                except Exception as e:
                    log.warning(f"스케줄러 초기화 실패: {e}")
                    self.scheduler = None
            
            # 🆕 뉴스 크롤링 패턴 사전 로드
            if self.surge_detector and hasattr(self.surge_detector, 'news_crawler'):
                news_crawler = self.surge_detector.news_crawler
                if news_crawler and hasattr(news_crawler, 'pattern_learner'):
                    try:
                        log.info("뉴스 크롤링 패턴 로드 중...")
                        news_crawler.pattern_learner.load_patterns()
                        log.success("✅ 저장된 크롤링 패턴 로드 완료")
                    except Exception as e:
                        log.warning(f"⚠️  크롤링 패턴 로드 실패 (신규 패턴 시작): {e}")
            
            # 🆕 설정 재로드 콜백 등록
            log.info("설정 재로드 시스템 등록 중...")
            Config.register_reload_callback(self._on_config_reloaded)
            log.success("✅ 설정 재로드 시스템 활성화")
            
            log.success("자동매매 엔진 초기화 완료")
            return True
            
        except Exception as e:
            log.error(f"엔진 초기화 중 오류: {e}")
            return False
    
    def _on_config_reloaded(self):
        """
        🆕 설정 재로드 콜백 (Config 변경 시 자동 호출)
        """
        try:
            log.info("=" * 70)
            log.info("⚙️  설정 변경 감지 - 자동매매 엔진 업데이트 중...")
            log.info("=" * 70)
            
            # 1. RiskManager 업데이트
            if self.risk_manager:
                self.risk_manager.reload_settings()
            
            # 2. SurgeDetector 업데이트
            if self.surge_detector:
                self.surge_detector.reload_settings()
            
            # 3. MarketScheduler 업데이트 (필요시)
            # 시장 시간 설정이 변경될 수 있음
            
            log.info("=" * 70)
            log.success("✅ 자동매매 엔진 설정 업데이트 완료!")
            log.success("   모든 변경사항이 즉시 적용되었습니다.")
            log.info("=" * 70)
            
        except Exception as e:
            log.error(f"설정 재로드 중 오류: {e}")
            import traceback
            log.error(traceback.format_exc())
    
    def set_surge_approval_callback(self, callback: Callable):
        """
        급등주 승인 콜백 설정
        
        Args:
            callback: 승인 요청 콜백 함수 (stock_code, stock_name, surge_info) -> bool
        """
        self.surge_approval_callback = callback
        log.info("급등주 승인 콜백 설정 완료")
    
    def start_trading(self):
        """자동매매 시작 (논블로킹 방식)"""
        if self.is_running:
            log.warning("이미 실행 중입니다.")
            return
        
        # 시장 상태 확인
        market_state = self.market_scheduler.get_current_market_state()
        
        # 장외 시간이면 자동 시작 예약 또는 경고
        if market_state in [MarketState.WEEKEND, MarketState.HOLIDAY, MarketState.CLOSED]:
            minutes_until_open = self.market_scheduler.get_time_until_market_open()
            hours = minutes_until_open // 60
            mins = minutes_until_open % 60
            
            log.warning("=" * 70)
            log.warning(f"⚠️  현재 장외 시간입니다 ({market_state.value})")
            log.warning(f"장 시작까지: {hours}시간 {mins}분")
            log.warning("=" * 70)
            
            if Config.AUTO_START_ENABLED:
                log.info("자동 시작이 활성화되어 있습니다. 장 시작 시 자동으로 시작합니다.")
                self.market_scheduler.schedule_auto_start(self._auto_start_callback)
                
                # GUI 로그 추가
                self._add_gui_log(
                    f"⏰ 자동 시작 예약: 장 시작 시 ({hours}시간 {mins}분 후)",
                    "orange"
                )
                return
            else:
                log.info("장 시작 후 다시 시도해주세요.")
                
                # GUI 로그 추가
                self._add_gui_log(
                    f"⚠️ 장외 시간 - 장 시작 후 다시 시도하세요 ({hours}시간 {mins}분 후)",
                    "red"
                )
                return
        
        # 장 시작 전이면 경고만
        if market_state == MarketState.PRE_OPEN:
            minutes_until_open = self.market_scheduler.get_time_until_market_open()
            log.info(f"⏰ 장 시작 전입니다. {minutes_until_open}분 후 개장")
            log.info("실시간 데이터 수신은 시작하지만, 매매는 개장 후 실행됩니다.")
        
        self.is_running = True
        log.success("🚀 자동매매 시작!")
        log.success(f"📊 시장 상태: {market_state.value}")
        log.info(f"관심 종목: {', '.join(self.watch_list)}")
        
        # 급등주 모니터링 시작
        if self.surge_detector:
            self.surge_detector.start_monitoring()
        
        # 뉴스 자동 갱신 시작
        if self.news_enabled and self.news_crawler:
            interval = getattr(Config, 'NEWS_UPDATE_INTERVAL', 300)
            self.news_crawler.start_auto_update(interval=interval)
            log.info(f"뉴스 자동 갱신 시작 ({interval}초 간격)")
        
        # 시작 알림
        if self.notifier:
            self.notifier.notify_system_start()
        
        # 헬스 모니터링 시작
        if self.health_monitor:
            self.health_monitor.start()
        
        # 스케줄러 시작
        if self.scheduler:
            self.scheduler.start()
        
        # 현재 상태 출력
        self.risk_manager.print_status()
        
        # 자동 종료 스케줄 설정
        self.market_scheduler.schedule_auto_stop(self._auto_stop_callback)
        
        # QTimer 시작 (논블로킹)
        self.check_timer.start()
        log.info("✅ QTimer 기반 모니터링 시작 (5초 간격)")
    
    def _periodic_check(self):
        """
        주기적 체크 (QTimer 콜백)
        GUI 응답없음 문제 해결을 위해 논블로킹 방식으로 구현
        """
        try:
            if not self.is_running:
                return
            
            # 🆕 개발 모드: 시장 상태 체크 건너뛰기
            if not Config.DEVELOPMENT_MODE:
                # 시장 상태 확인
                market_state = self.market_scheduler.get_current_market_state()
                
                # 시장 상태별 동작
                if market_state == MarketState.PRE_OPEN:
                    # 장 시작 전: 준비 상태 로그 (1분마다)
                    current_time = datetime.now()
                    if not hasattr(self, '_last_preopen_log_time'):
                        self._last_preopen_log_time = current_time
                    
                    if (current_time - self._last_preopen_log_time).seconds >= 60:
                        minutes_until_open = self.market_scheduler.get_time_until_market_open()
                        log.info(f"⏰ 장 시작 전 대기 중... {minutes_until_open}분 후 개장")
                        self._last_preopen_log_time = current_time
                    return
                
                elif market_state in [MarketState.CLOSED, MarketState.WEEKEND, MarketState.HOLIDAY]:
                    # 장외 시간: 자동 종료
                    if market_state == MarketState.CLOSED and datetime.now().time() >= dt_time(15, 30):
                        log.info(f"장 마감 ({market_state.value}). 자동매매를 종료합니다.")
                        self.stop_trading()
                        return
                    # 대기 상태 로그 (5분마다)
                    current_time = datetime.now()
                    if not hasattr(self, '_last_closed_log_time'):
                        self._last_closed_log_time = current_time
                    
                    if (current_time - self._last_closed_log_time).seconds >= 300:  # 5분
                        minutes_until_open = self.market_scheduler.get_time_until_market_open()
                        hours = minutes_until_open // 60
                        mins = minutes_until_open % 60
                        log.info(f"⏸️  장외 시간 ({market_state.value}). 장 시작까지: {hours}시간 {mins}분")
                        self._last_closed_log_time = current_time
                    return
                
                elif market_state == MarketState.AFTER_HOURS:
                    # 시간외 매매
                    if not Config.ENABLE_AFTER_HOURS_TRADING:
                        log.info("시간외 매매 시간입니다. 자동매매를 종료합니다.")
                        self.stop_trading()
                        return
                    # 제한적 매매 (급등주 감지 비활성화 등)
                    log.info("⚡ 시간외 매매 중...")
                
                # 장 운영 시간 확인 (정규장 또는 시간외)
                if not self.is_market_open():
                    return
            
            # 하트비트 (1분마다) - 프로그램 정상 실행 확인
            current_time = datetime.now()
            if not hasattr(self, '_last_heartbeat_time'):
                self._last_heartbeat_time = current_time
            
            if (current_time - self._last_heartbeat_time).seconds >= 60:  # 1분
                log.info(f"💓 하트비트 - {current_time.strftime('%H:%M:%S')} | 정상 실행 중")
                self._last_heartbeat_time = current_time
            
            # 상태 요약 출력 (5분마다)
            if not hasattr(self, '_last_status_time'):
                self._last_status_time = current_time
            
            if (current_time - self._last_status_time).seconds >= 300:  # 5분
                self._print_status_summary()
                self._last_status_time = current_time
            
            # 🆕 보유 종목 현재가 업데이트 (실시간 데이터 수신 안될 경우 대비)
            self._update_all_positions_price()
            
            # 손절매/익절매 확인 (최우선)
            self.check_exit_conditions()
            
            # 일일 손실 한도 확인
            if self.risk_manager.check_daily_loss_limit():
                log.critical("⛔ 일일 손실 한도 초과로 자동매매를 중지합니다.")
                self.stop_trading()
                return
                
        except Exception as e:
            log.error(f"주기적 체크 중 오류 발생: {e}")
            # 오류가 발생해도 타이머는 계속 실행
    
    def _update_all_positions_price(self):
        """
        🆕 모든 보유 종목의 현재가 업데이트
        
        실시간 데이터 수신이 제대로 안될 경우를 대비하여
        주기적으로 모든 보유 종목의 현재가를 API로 직접 조회합니다.
        """
        try:
            positions = self.risk_manager.positions
            if not positions:
                return
            
            # 마지막 업데이트 시간 체크 (1분에 한 번만)
            current_time = time.time()
            if not hasattr(self, '_last_price_update_time'):
                self._last_price_update_time = 0
            
            if current_time - self._last_price_update_time < 60:  # 1분
                return
            
            self._last_price_update_time = current_time
            
            log.info(f"🔄 보유 종목 현재가 일괄 업데이트 중... ({len(positions)}개 종목)")
            
            for stock_code, position in positions.items():
                try:
                    # 현재가 조회
                    current_price = self.kiwoom.get_current_price(stock_code)
                    
                    if current_price:
                        # 기존 가격과 다르면 업데이트
                        if current_price != position.current_price:
                            old_price = position.current_price
                            position.update_price(current_price)
                            
                            profit_rate = ((current_price - position.avg_price) / position.avg_price) * 100
                            log.info(
                                f"   📊 {stock_code} {position.stock_name}: "
                                f"{old_price:,}원 → {current_price:,}원 "
                                f"(수익률: {profit_rate:+.2f}%)"
                            )
                        else:
                            log.debug(f"   ✓ {stock_code}: 가격 변동 없음 ({current_price:,}원)")
                    else:
                        log.warning(f"   ⚠️  {stock_code}: 현재가 조회 실패")
                    
                    # API 호출 간격 (0.5초)
                    time.sleep(0.5)
                    
                except Exception as e:
                    log.error(f"   ❌ {stock_code} 현재가 조회 중 오류: {e}")
            
            log.success(f"✅ 보유 종목 현재가 업데이트 완료 ({len(positions)}개)")
            
        except Exception as e:
            log.error(f"보유 종목 현재가 업데이트 중 오류: {e}")
    
    def _print_status_summary(self):
        """상태 요약 출력"""
        try:
            log.info("=" * 70)
            log.info("📊 자동매매 상태 요약")
            log.info("=" * 70)
            
            # 관심 종목 현황
            log.info(f"👀 관심 종목: {len(self.watch_list)}개 - {', '.join(self.watch_list[:5])}")
            if len(self.watch_list) > 5:
                log.info(f"   ... 외 {len(self.watch_list) - 5}개")
            
            # 가격 데이터 수신 현황
            data_counts = {code: len(hist) for code, hist in self.price_history.items()}
            if data_counts:
                log.info(f"📡 가격 데이터: {sum(data_counts.values())}개 수신")
                for code, count in list(data_counts.items())[:3]:
                    log.info(f"   {code}: {count}개")
            else:
                log.warning("⚠️  가격 데이터 수신 없음 - 실시간 등록 확인 필요")
            
            # 포지션 현황
            positions = self.risk_manager.positions
            if positions:
                log.info(f"📈 보유 포지션: {len(positions)}개")
                for code, pos in positions.items():
                    pl_pct = ((pos.current_price - pos.entry_price) / pos.entry_price) * 100
                    log.info(
                        f"   {code}: {pos.quantity}주 @ {pos.entry_price:,}원 "
                        f"→ {pos.current_price:,}원 ({pl_pct:+.2f}%)"
                    )
            else:
                log.info("📭 보유 포지션 없음")
            
            # 급등주 모니터링 상태
            if self.surge_detector and self.surge_detector.is_monitoring:
                surge_stats = self.surge_detector.get_statistics()
                log.info(f"🚀 급등주 모니터링: 활성 ✅")
                log.info(f"   후보군: {surge_stats.get('candidate_count', 0)}개")
                log.info(f"   감지됨: {surge_stats.get('detected_count', 0)}개")
                log.info(f"   추가됨: {len(self.surge_detected_stocks)}개")
            else:
                log.warning("⚠️  급등주 모니터링: 비활성")
            
            # 매매 신호
            log.info(f"📊 매매 신호 생성: {self.signal_count}회")
            
            log.info("=" * 70)
            
        except Exception as e:
            log.error(f"상태 요약 출력 중 오류: {e}")
    
    def stop_trading(self):
        """자동매매 중지"""
        self.is_running = False
        
        # QTimer 중지
        if self.check_timer.isActive():
            self.check_timer.stop()
            log.info("⏹️  QTimer 모니터링 중지")
        
        # 자동 시작/종료 스케줄 취소
        self.market_scheduler.cancel_scheduled_tasks()
        
        # 급등주 모니터링 중지
        if self.surge_detector:
            self.surge_detector.stop_monitoring()
        
        # 뉴스 자동 갱신 중지
        if self.news_enabled and self.news_crawler:
            self.news_crawler.stop_auto_update()
            log.info("뉴스 자동 갱신 중지")
        
        # 헬스 모니터링 중지
        if self.health_monitor:
            self.health_monitor.stop()
            # 최종 헬스 요약 출력
            self.health_monitor.print_health_summary()
        
        # 1분봉 집계기 중지 및 데이터 저장
        # 🔄 데이터베이스 저장 기능 제거됨
        
        # 스케줄러 중지
        if self.scheduler:
            self.scheduler.stop()
        
        # 종료 알림
        if self.notifier:
            self.notifier.notify_system_stop()
        
        log.info("🛑 자동매매 중지")
        
        # 최종 통계 출력
        self.risk_manager.print_status()
        
        # 급등주 통계 출력
        if self.surge_detector:
            self.surge_detector.print_status()
    
    def is_market_open(self) -> bool:
        """
        장 운영 시간 확인 (MarketScheduler 기반)
        
        Returns:
            장 운영 중 여부
        """
        market_state = self.market_scheduler.get_current_market_state()
        
        # 정규장은 항상 허용
        if market_state == MarketState.OPEN:
            return True
        
        # 시간외 매매 설정 시
        if Config.ENABLE_AFTER_HOURS_TRADING and market_state == MarketState.AFTER_HOURS:
            return True
        
        return False
    
    def on_price_update(self, stock_code: str, price_data: Dict):
        """
        실시간 시세 업데이트 처리
        
        Args:
            stock_code: 종목 코드
            price_data: 가격 데이터
        """
        if not self.is_running:
            return
        
        try:
            current_price = price_data['current_price']
            change_rate = price_data.get('change_rate', 0)
            
            # 🔍 실시간 데이터 수신 확인 로그 (처음 5번만 표시)
            if not hasattr(self, '_price_update_count'):
                self._price_update_count = {}
            if stock_code not in self._price_update_count:
                self._price_update_count[stock_code] = 0
            self._price_update_count[stock_code] += 1
            
            if self._price_update_count[stock_code] <= 5:
                log.info(
                    f"🔍 실시간 데이터 수신: {stock_code} {current_price:,}원 "
                    f"({change_rate:+.2f}%) [수신 #{self._price_update_count[stock_code]}]"
                )
            
            # 급등주 감지기에 데이터 전달
            if self.surge_detector and self.surge_detector.is_monitoring:
                self.surge_detector.on_price_update(stock_code, price_data)
            
            # 관심 종목이 아니면 매매 신호 생성 안 함
            if stock_code not in self.watch_list:
                return
            
            # 가격 히스토리 업데이트
            self.price_history[stock_code].append(current_price)
            
            # 최근 100개만 유지
            if len(self.price_history[stock_code]) > 100:
                self.price_history[stock_code] = self.price_history[stock_code][-100:]
            
            # 🆕 관심 종목의 실시간 가격 표시 (30번째 업데이트마다, 과도한 로그 방지)
            data_count = len(self.price_history[stock_code])
            if data_count <= 100 and data_count % 30 == 0:
                log.info(
                    f"📊 관심종목 실시간: {stock_code} {current_price:,}원 "
                    f"({change_rate:+.2f}%) | 데이터: {data_count}개"
                )
            
            # 보유 중인 종목의 현재가 업데이트
            self.risk_manager.update_position_price(stock_code, current_price)
            
            # 최소 30개 이상 데이터가 있어야 신호 생성
            if len(self.price_history[stock_code]) < 30:
                return
            
            # 보유 종목은 더 빠르게 체크 (5초), 일반 종목은 10초
            is_holding = stock_code in self.risk_manager.positions
            check_interval = 5 if is_holding else 10
            
            now = time.time()
            last_check = self.last_check_time.get(stock_code, 0)
            if now - last_check < check_interval:
                return
            
            self.last_check_time[stock_code] = now
            
            # 보유 종목은 더 자주 체크한다는 로그
            if is_holding and len(self.price_history[stock_code]) % 10 == 0:
                log.info(f"💼 보유 종목 체크: {stock_code} (5초 간격)")
            
            # 매매 신호 생성
            self.process_signal(stock_code, self.price_history[stock_code])
            
        except Exception as e:
            log.error(f"시세 업데이트 처리 중 오류: {e}")
    
    def process_signal(self, stock_code: str, prices: List[float]):
        """
        매매 신호 처리
        
        Args:
            stock_code: 종목 코드
            prices: 가격 리스트
        """
        try:
            # 신호 생성
            signal_result = self.strategy.generate_signal(prices)
            signal = signal_result['signal']
            
            if signal == SignalType.HOLD:
                # 디버깅: 왜 HOLD인지 주기적으로 로그 출력 (30개마다)
                if len(prices) % 30 == 0:
                    log.debug(f"[{stock_code}] HOLD 신호 - 강도: {signal_result['strength']:.2f}, 이유: {signal_result.get('reason', 'N/A')}")
                return
            
            self.signal_count += 1
            current_price = prices[-1]
            
            # 매수 신호
            if signal == SignalType.BUY:
                log.warning("=" * 70)
                log.warning(f"🔔 매수 신호 발생! {stock_code}")
                log.warning(f"   현재가: {current_price:,}원")
                log.warning(f"   신호 강도: {signal_result['strength']:.2f}")
                log.warning(f"   사유: {signal_result['reason']}")
                log.warning("=" * 70)
                self.execute_buy(stock_code, current_price, signal_result)
            
            # 매도 신호
            elif signal == SignalType.SELL:
                # 🆕 매도 금지 확인 (일반 매도 신호만 차단, 손절/익절 제외)
                if stock_code in self.risk_manager.positions:
                    position = self.risk_manager.positions[stock_code]
                    if position.sell_blocked:
                        log.info(f"🚫 매도 금지 설정: {stock_code} - 자동 매도 차단 (사용자 설정)")
                        return
                
                log.warning("=" * 70)
                log.warning(f"🔔 매도 신호 발생! {stock_code}")
                log.warning(f"   현재가: {current_price:,}원")
                log.warning(f"   신호 강도: {signal_result['strength']:.2f}")
                log.warning(f"   사유: {signal_result['reason']}")
                log.warning("=" * 70)
                self.execute_sell(stock_code, current_price, signal_result)
                
        except Exception as e:
            log.error(f"신호 처리 중 오류: {e}")
    
    def on_order_book_update(self, stock_code: str, order_book_data: Dict):
        """
        🆕 실시간 호가 데이터 처리 (선제적 매수 판단)
        
        Args:
            stock_code: 종목 코드
            order_book_data: 호가 데이터 {
                'bid_volume': 매수 총잔량,
                'ask_volume': 매도 총잔량,
                'execution_strength': 체결강도
            }
        """
        if not self.is_running:
            return
        
        try:
            # 급등주 감지기로 호가 데이터 전달
            if self.surge_detector and self.surge_detector.is_monitoring:
                self.surge_detector.on_order_book_update(stock_code, order_book_data)
            
        except Exception as e:
            log.error(f"호가 데이터 처리 중 오류 ({stock_code}): {e}")
    
    def execute_buy(
        self,
        stock_code: str,
        current_price: int,
        signal_result: Dict
    ):
        """
        매수 실행
        
        Args:
            stock_code: 종목 코드
            current_price: 현재가
            signal_result: 신호 정보
        """
        try:
            log.info(f"🔍 [execute_buy] 시작: {stock_code}, 가격: {current_price:,}원")
            
            # 🆕 물타기 여부 확인
            is_average_down = stock_code in self.risk_manager.positions
            
            # 리스크 검증 (물타기 허용)
            log.info(f"🔍 [execute_buy] 리스크 검증 중... (물타기: {'예' if is_average_down else '아니오'})")
            is_valid, reason = self.risk_manager.validate_new_position(stock_code, allow_average_down=True)
            if not is_valid:
                log.warning(f"❌ 매수 불가: {stock_code}")
                log.warning(f"   사유: {reason}")
                log.warning(f"   현재 보유: {len(self.risk_manager.positions)}/{Config.MAX_STOCKS}")
                log.warning(f"   현재 잔고: {self.risk_manager.current_balance:,}원")
                return
            log.info(f"✅ [execute_buy] 리스크 검증 통과 - {reason}")
            
            # 🆕 매수 수량 계산 (물타기인 경우 수량 비율 적용)
            log.info(f"🔍 [execute_buy] 매수 수량 계산 중...")
            if is_average_down:
                # 물타기: 기존 수량 * 비율
                existing_position = self.risk_manager.positions[stock_code]
                base_quantity = existing_position.quantity
                quantity = int(base_quantity * Config.AVERAGE_DOWN_SIZE_RATIO)
                log.info(f"   물타기 수량: {base_quantity}주 × {Config.AVERAGE_DOWN_SIZE_RATIO} = {quantity}주")
            else:
                # 신규 매수: 일반 계산
                quantity = self.risk_manager.calculate_position_size(current_price)
            
            if quantity < 1:
                log.warning(f"매수 불가: {stock_code} - 수량 부족")
                return
            log.info(f"✅ [execute_buy] 수량 계산 완료: {quantity}주")
            
            # 주문 전송
            order_type = "🔻 물타기" if is_average_down else "📈 매수"
            log.warning("=" * 70)
            log.warning(
                f"{order_type} 시도: {stock_code} {quantity}주 @ {current_price:,}원 | "
                f"신호 강도: {signal_result['strength']:.2f}"
            )
            if is_average_down:
                existing_position = self.risk_manager.positions[stock_code]
                log.warning(f"   현재 평균가: {existing_position.avg_price:,}원 | 수량: {existing_position.quantity}주")
                log.warning(f"   물타기 {existing_position.average_down_count + 1}/{Config.MAX_AVERAGE_DOWN_COUNT}회차")
            log.warning("=" * 70)
            
            log.info(f"🔍 [execute_buy] 키움 API buy_order 호출 중...")
            order_result = self.kiwoom.buy_order(
                stock_code,
                quantity,
                0  # 시장가 주문
            )
            log.info(f"✅ [execute_buy] buy_order 호출 완료, 결과: {order_result}")
            
            if order_result:
                stock_name = self.kiwoom.get_stock_name(stock_code)  # 종목명 조회
                
                # 🆕 물타기 처리
                if is_average_down:
                    existing_position = self.risk_manager.positions[stock_code]
                    old_avg_price = existing_position.avg_price
                    old_quantity = existing_position.quantity
                    
                    # 포지션에 추가 매수 반영
                    existing_position.add_position(quantity, current_price)
                    
                    position = existing_position
                    
                    log.success("=" * 70)
                    log.success(f"✅ 물타기 체결 완료!")
                    log.success(f"   종목: {stock_name} ({stock_code})")
                    log.success(f"   수량: {old_quantity}주 → {position.quantity}주 (+{quantity}주)")
                    log.success(f"   평균가: {old_avg_price:,}원 → {position.avg_price:,}원")
                    log.success(f"   총 투자: {position.total_invested:,}원")
                    log.success(f"   물타기: {position.average_down_count}/{Config.MAX_AVERAGE_DOWN_COUNT}회")
                    log.success("=" * 70)
                else:
                    # 신규 포지션 추가
                    position = self.risk_manager.add_position(
                        stock_code,
                        stock_name,
                        quantity,
                        current_price
                    )
                
                # 🆕 뉴스 점수 설정 (급등주 매수의 경우)
                if position and 'news_score' in signal_result:
                    position.news_score = signal_result['news_score']
                    if position.news_score != 0:
                        adjusted_stop_loss = position.get_adjusted_stop_loss_percent()
                        log.info(
                            f"   📰 뉴스 점수: {position.news_score:+d}/100 "
                            f"→ 손절 기준: {Config.STOP_LOSS_PERCENT}% → {adjusted_stop_loss:.1f}%"
                        )
                
                if position:
                    total_cost = current_price * quantity
                    
                    # 📦 블랙박스: 거래 기록
                    try:
                        trade_reason = signal_result.get('reason', '매수 신호')
                        if is_average_down:
                            trade_reason = f"물타기 {position.average_down_count}회차 - {trade_reason}"
                        
                        trade_id = self.history_db.record_trade({
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'trade_type': 'BUY',
                            'quantity': quantity,
                            'price': current_price,
                            'total_amount': total_cost,
                            'timestamp': datetime.now().isoformat(),
                            'order_id': str(order_result),
                            'reason': trade_reason,
                            'signal_strength': signal_result.get('strength', 0)
                        })
                        
                        if is_average_down:
                            # 📦 블랙박스: 포지션 업데이트 (물타기)
                            if position.db_position_id:
                                self.history_db.update_position(position.db_position_id, {
                                    'quantity': position.quantity,
                                    'entry_price': position.avg_price,  # 평균가로 업데이트
                                    'total_invested': position.total_invested,
                                    'average_down_count': position.average_down_count
                                })
                                log.debug(f"📦 블랙박스 포지션 업데이트: Position ID={position.db_position_id} (물타기)")
                        else:
                            # 📦 블랙박스: 포지션 시작 (신규 매수)
                            position_id = self.history_db.start_position({
                                'stock_code': stock_code,
                                'stock_name': stock_name,
                                'entry_time': position.entry_time.isoformat(),
                                'entry_price': current_price,
                                'quantity': quantity,
                                'total_invested': total_cost,
                                'entry_config': json.dumps(self._get_current_config()),
                                'sell_blocked': 1 if position.sell_blocked else 0
                            })
                            
                            # Position 객체에 DB ID 저장
                            position.db_position_id = position_id
                            log.debug(f"📦 블랙박스 포지션 시작: Position ID={position_id}")
                        
                        # 📦 블랙박스: 시장 스냅샷 기록
                        self.history_db.record_market_snapshot({
                            'timestamp': datetime.now().isoformat(),
                            'position_id': position.db_position_id,
                            'market_state': self.market_scheduler.get_current_state().value,
                            'total_balance': self.risk_manager.current_balance,
                            'total_asset': self.risk_manager.current_balance + sum(
                                p.current_price * p.quantity for p in self.risk_manager.positions.values()
                            ),
                            'available_cash': self.risk_manager.current_balance,
                            'stock_code': stock_code,
                            'current_price': current_price
                        })
                        
                        log.debug(f"📦 블랙박스 기록 완료: Trade ID={trade_id}")
                    except Exception as e:
                        log.error(f"❌ 블랙박스 기록 실패: {e}")
                    
                    if not is_average_down:
                        log.success("=" * 70)
                        log.success(f"✅ 매수 체결 완료!")
                        log.success(f"   종목: {stock_code}")
                    log.success(f"   수량: {quantity}주")
                    log.success(f"   체결가: {current_price:,}원")
                    log.success(f"   총 금액: {total_cost:,}원")
                    log.success(f"   사유: {signal_result['reason']}")
                    log.success(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
                    log.success("=" * 70)
                    
                    # GUI 로그 추가
                    self._add_gui_log(
                        f"✅ 매수: {stock_code} {quantity}주 @ {current_price:,}원",
                        "green"
                    )
                    
                    # 차트 마커 추가
                    self._add_chart_marker(stock_code, "buy", current_price)
                    
                    # 알림 전송
                    if self.notifier:
                        self.notifier.notify_trade(
                            "매수",
                            stock_name,
                            quantity,
                            current_price
                        )
                    
                    # 🆕 실시간 시세 등록 (새로 매수한 종목)
                    try:
                        log.info(f"📡 실시간 시세 등록: {stock_code}")
                        self.kiwoom.register_real_data([stock_code])
                    except Exception as e:
                        log.warning(f"실시간 시세 등록 실패 ({stock_code}): {e}")
            else:
                log.error("=" * 70)
                log.error(f"❌ 매수 주문 실패: {stock_code}")
                log.error("=" * 70)
                
                # GUI 로그 추가
                self._add_gui_log(f"❌ 매수 실패: {stock_code}", "red")
                
        except Exception as e:
            log.error("=" * 70)
            log.error(f"❌ 매수 실행 중 치명적 오류!")
            log.error(f"   종목: {stock_code}")
            log.error(f"   에러 타입: {type(e).__name__}")
            log.error(f"   에러 메시지: {str(e)}")
            log.error(f"   상세 스택:")
            log.error(f"{traceback.format_exc()}")
            log.error("=" * 70)
    
    def execute_sell(
        self,
        stock_code: str,
        current_price: int,
        signal_result: Dict
    ):
        """
        매도 실행
        
        Args:
            stock_code: 종목 코드
            current_price: 현재가
            signal_result: 신호 정보
        """
        try:
            # 보유 종목 확인
            if stock_code not in self.risk_manager.positions:
                log.debug(f"매도 불가: {stock_code} - 보유하지 않음")
                return
            
            position = self.risk_manager.positions[stock_code]
            
            # 🆕 매도 금지 확인 (일반 매도만 차단)
            if position.sell_blocked:
                log.info(f"🚫 매도 금지: {stock_code} - 사용자 설정으로 매도 차단")
                return
            
            # 주문 전송
            log.info(
                f"📉 매도 시도: {stock_code} {position.quantity}주 @ {current_price:,}원 | "
                f"신호 강도: {signal_result['strength']:.2f}"
            )
            
            order_result = self.kiwoom.sell_order(
                stock_code,
                position.quantity,
                0  # 시장가 주문
            )
            
            if order_result:
                # 포지션 제거
                profit_loss = self.risk_manager.remove_position(
                    stock_code,
                    current_price,
                    signal_result['reason']
                )
                
                if profit_loss is not None:
                    total_amount = current_price * position.quantity
                    profit_rate = (profit_loss / (position.entry_price * position.quantity)) * 100
                    log.success("=" * 70)
                    log.success(f"✅ 매도 체결 완료!")
                    log.success(f"   종목: {stock_code}")
                    log.success(f"   수량: {position.quantity}주")
                    log.success(f"   매수가: {position.entry_price:,}원")
                    log.success(f"   매도가: {current_price:,}원")
                    log.success(f"   총 금액: {total_amount:,}원")
                    log.success(f"   손익: {profit_loss:+,}원 ({profit_rate:+.2f}%)")
                    log.success(f"   사유: {signal_result['reason']}")
                    log.success(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
                    log.success("=" * 70)
                    
                    # 차트 마커 추가
                    self._add_chart_marker(stock_code, "sell", current_price)
                    
                    # 알림 전송
                    if self.notifier:
                        self.notifier.notify_trade(
                            "매도",
                            position.stock_name,
                            position.quantity,
                            current_price,
                            profit_loss
                        )
            else:
                log.error("=" * 70)
                log.error(f"❌ 매도 주문 실패: {stock_code}")
                log.error("=" * 70)
                
        except Exception as e:
            log.error(f"매도 실행 중 오류: {e}")
    
    def check_exit_conditions(self):
        """
        손절매/익절매 조건 확인 (+ 추가 매수 체크)
        """
        try:
            for stock_code, position in list(self.risk_manager.positions.items()):
                # 추가 매수 확인 (손절매보다 먼저 체크)
                if self.risk_manager.check_average_down(position):
                    log.warning(f"🔄 추가 매수 시도: {stock_code}")
                    
                    # 추가 매수 수량 계산
                    initial_quantity = int(position.total_invested / position.entry_price)
                    add_quantity = int(initial_quantity * Config.AVERAGE_DOWN_SIZE_RATIO)
                    if add_quantity < 1:
                        add_quantity = 1
                    
                    # 내부 처리 (잔고 차감, 평균가 계산)
                    success = self.risk_manager.execute_average_down(stock_code, position.current_price)
                    
                    if success:
                        # 키움 API로 실제 주문 (추가 매수는 우선순위 보통)
                        result = self.kiwoom.buy_order(
                            stock_code, 
                            add_quantity, 
                            0,  # 시장가
                            priority="익절"  # 추가 매수도 중요 주문으로 처리
                        )
                        
                        if result:
                            log.success("=" * 70)
                            log.success(f"✅ 추가 매수 주문 성공!")
                            log.success(f"   종목: {stock_code}")
                            log.success(f"   수량: {add_quantity}주")
                            log.success(f"   가격: 시장가")
                            log.success(f"   신규 평균가: {position.avg_price:,}원")
                            log.success(f"   신규 총 수량: {position.quantity}주")
                            log.success(f"   추가 매수 횟수: {position.average_down_count}/{Config.MAX_AVERAGE_DOWN_COUNT}")
                            log.success("=" * 70)
                            
                            # GUI 로그 추가
                            self._add_gui_log(
                                f"🔄 추가매수: {stock_code} {add_quantity}주 (평균가: {position.avg_price:,}원)",
                                "orange"
                            )
                        else:
                            log.error(f"❌ 추가 매수 주문 실패: {stock_code}")
                            # 실패 시 내부 처리 롤백
                            position.average_down_count -= 1
                            if position.average_down_prices:
                                position.average_down_prices.pop()
                            # 원래 상태로 복구 (간단히 재계산)
                            position.total_invested = position.entry_price * (position.quantity - add_quantity)
                            position.quantity -= add_quantity
                            if position.quantity > 0:
                                position.avg_price = int(position.total_invested / position.quantity)
                            position.update_stop_profit_prices()
                            self.risk_manager.current_balance += position.current_price * add_quantity
                    else:
                        log.warning(f"⚠️  추가 매수 조건 미충족: {stock_code}")
                    
                    continue  # 추가 매수 후 손절 체크는 건너뜀 (이번 루프에서)
                
                # 🆕 매도 금지 확인 (손절/익절 포함)
                if position.sell_blocked:
                    log.debug(f"🚫 매도 금지 설정: {stock_code} - 손절/익절 실행 안함")
                    continue
                
                # 손절매 확인
                if self.risk_manager.check_stop_loss(position):
                    loss_rate = ((position.current_price - position.entry_price) / position.entry_price) * 100
                    log.warning("=" * 70)
                    log.warning(f"🚨 손절매 조건 감지!")
                    log.warning(f"   종목: {stock_code}")
                    log.warning(f"   매수가: {position.entry_price:,}원")
                    log.warning(f"   현재가: {position.current_price:,}원")
                    log.warning(f"   손실률: {loss_rate:.2f}%")
                    log.warning(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
                    log.warning("=" * 70)
                    self.execute_exit(
                        stock_code,
                        position.current_price,
                        "손절매"
                    )
                
                # 익절매 확인
                elif self.risk_manager.check_take_profit(position):
                    profit_rate = ((position.current_price - position.entry_price) / position.entry_price) * 100
                    log.warning("=" * 70)
                    log.warning(f"🎯 익절매 조건 감지!")
                    log.warning(f"   종목: {stock_code}")
                    log.warning(f"   매수가: {position.entry_price:,}원")
                    log.warning(f"   현재가: {position.current_price:,}원")
                    log.warning(f"   수익률: {profit_rate:.2f}%")
                    log.warning(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
                    log.warning("=" * 70)
                    self.execute_exit(
                        stock_code,
                        position.current_price,
                        "익절매"
                    )
                    
        except Exception as e:
            log.error(f"청산 조건 확인 중 오류: {e}")
    
    def execute_exit(self, stock_code: str, sell_price: int, reason: str):
        """
        강제 청산 실행 (손절매/익절매)
        
        Args:
            stock_code: 종목 코드
            sell_price: 매도가
            reason: 청산 사유
        """
        try:
            if stock_code not in self.risk_manager.positions:
                return
            
            position = self.risk_manager.positions[stock_code]
            
            # 주문 우선순위 설정 (손절/익절은 우선순위 높음)
            priority = "손절" if reason == "손절매" else "익절" if reason == "익절매" else "일반"
            
            # 주문 전송
            order_result = self.kiwoom.sell_order(
                stock_code,
                position.quantity,
                0,  # 시장가 주문
                priority=priority  # 우선순위 전달
            )
            
            if order_result:
                # 포지션 정보 저장 (제거 전)
                position_data = {
                    'stock_name': position.stock_name,
                    'quantity': position.quantity,
                    'avg_price': position.avg_price,
                    'entry_time': position.entry_time,
                    'db_position_id': position.db_position_id
                }
                
                # 포지션 제거
                profit_loss = self.risk_manager.remove_position(
                    stock_code,
                    sell_price,
                    reason
                )
                
                if profit_loss is not None:
                    total_amount = sell_price * position_data['quantity']
                    profit_rate = (profit_loss / (position_data['avg_price'] * position_data['quantity'])) * 100
                    holding_duration = (datetime.now() - position_data['entry_time']).total_seconds()
                    
                    # 📦 블랙박스: 거래 기록
                    try:
                        trade_id = self.history_db.record_trade({
                            'stock_code': stock_code,
                            'stock_name': position_data['stock_name'],
                            'trade_type': 'SELL',
                            'quantity': position_data['quantity'],
                            'price': sell_price,
                            'total_amount': total_amount,
                            'timestamp': datetime.now().isoformat(),
                            'order_id': str(order_result),
                            'reason': reason,
                            'position_id': position_data['db_position_id']
                        })
                        
                        # 📦 블랙박스: 포지션 종료
                        if position_data['db_position_id']:
                            self.history_db.close_position(position_data['db_position_id'], {
                                'exit_time': datetime.now().isoformat(),
                                'exit_price': sell_price,
                                'exit_reason': reason,
                                'profit_loss': int(profit_loss),
                                'profit_loss_percent': profit_rate,
                                'holding_duration_seconds': int(holding_duration),
                                'exit_config': json.dumps(self._get_current_config())
                            })
                            
                            # 일일 요약 업데이트
                            self.history_db.update_daily_summary()
                            
                            log.debug(f"📦 블랙박스 기록 완료: Trade ID={trade_id}, Position 종료")
                    except Exception as e:
                        log.error(f"❌ 블랙박스 기록 실패: {e}")
                    
                    emoji = "✅" if profit_loss >= 0 else "❌"
                    log.success("=" * 70)
                    log.success(f"{emoji} 청산 체결 완료! ({reason})")
                    log.success(f"   종목: {stock_code}")
                    log.success(f"   수량: {position_data['quantity']}주")
                    log.success(f"   매수가: {position_data['avg_price']:,}원")
                    log.success(f"   매도가: {sell_price:,}원")
                    log.success(f"   총 금액: {total_amount:,}원")
                    log.success(f"   손익: {profit_loss:+,}원 ({profit_rate:+.2f}%)")
                    log.success(f"   사유: {reason}")
                    log.success(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
                    log.success("=" * 70)
                    
                    # 차트 마커 추가
                    self._add_chart_marker(stock_code, "sell", sell_price)
                    
                    # 알림 전송
                    if self.notifier:
                        if reason == "손절매":
                            self.notifier.notify_stop_loss(
                                position.stock_name,
                                position.quantity,
                                position.entry_price,
                                sell_price,
                                abs(profit_loss)
                            )
                        elif reason == "익절매":
                            self.notifier.notify_take_profit(
                                position.stock_name,
                                position.quantity,
                                position.entry_price,
                                sell_price,
                                profit_loss
                            )
            else:
                log.error("=" * 70)
                log.error(f"❌ 청산 주문 실패: {stock_code} ({reason})")
                log.error("=" * 70)
                
        except Exception as e:
            log.error(f"청산 실행 중 오류: {e}")
    
    def on_surge_detected(self, stock_code: str, candidate):
        """
        급등주 감지 콜백
        
        Args:
            stock_code: 종목 코드
            candidate: SurgeCandidate 객체
        """
        try:
            # 이미 추가된 종목은 무시
            if stock_code in self.surge_detected_stocks:
                log.debug(f"이미 추가된 급등주: {candidate.name} ({stock_code})")
                return
            
            # 이미 관심 종목에 있으면 무시
            if stock_code in self.watch_list:
                log.debug(f"이미 관심 종목: {candidate.name} ({stock_code})")
                return
            
            # 승인 콜백이 설정되지 않았으면 자동 추가
            if not self.surge_approval_callback:
                log.warning("급등주 승인 콜백이 설정되지 않았습니다. 자동으로 추가합니다.")
                self.add_surge_stock(stock_code, candidate)
                return
            
            # 알림 전송
            if self.notifier:
                self.notifier.notify_surge(
                    candidate.name,
                    stock_code,
                    candidate.current_change_rate,
                    candidate.get_volume_ratio()
                )
            
            # 승인 요청 (🔥 수정: candidate 객체를 직접 전달)
            def request_approval():
                try:
                    # 콜백 함수에 stock_code와 candidate 전달
                    approved = self.surge_approval_callback(stock_code, candidate)
                    # 콜백에서 이미 add_surge_stock 호출하므로 여기서는 호출 안 함
                    if not approved:
                        log.info(f"급등주 매수 거부: {candidate.name} ({stock_code})")
                except Exception as e:
                    log.error(f"급등주 승인 처리 중 오류: {e}")
            
            # 별도 스레드에서 승인 요청 (메인 루프 블로킹 방지)
            approval_thread = threading.Thread(target=request_approval, daemon=True)
            approval_thread.start()
            
        except Exception as e:
            log.error(f"급등주 감지 콜백 처리 중 오류: {e}")
    
    def add_surge_stock(self, stock_code: str, candidate):
        """
        급등주를 관심 종목에 추가하고 즉시 매수
        
        Args:
            stock_code: 종목 코드
            candidate: SurgeCandidate 객체
        """
        # 다른 급등주 처리 중이면 대기
        if self.surge_processing:
            log.warning(f"⏳ 다른 급등주 처리 중 - 대기: {candidate.name} ({stock_code})")
            return
        
        # 동시 추가 방지 (스레드 안전성)
        with self.surge_add_lock:
            try:
                # 처리 중 플래그 설정
                self.surge_processing = True
                
                # 이미 추가되었는지 다시 확인 (lock 내부에서)
                if stock_code in self.surge_detected_stocks:
                    log.debug(f"이미 처리 중인 급등주: {candidate.name} ({stock_code})")
                    self.surge_processing = False
                    return
                
                # 최대 종목 수 체크
                current_positions = len(self.risk_manager.positions)
                if current_positions >= Config.MAX_STOCKS:
                    log.warning(
                        f"⚠️  최대 보유 종목 수 도달 ({current_positions}/{Config.MAX_STOCKS}) - "
                        f"급등주 추가 불가: {candidate.name}"
                    )
                    self.surge_processing = False
                    return
                
                # 관심 종목에 추가
                if stock_code not in self.watch_list:
                    self.watch_list.append(stock_code)
                    log.success(
                        f"✅ 급등주 추가: {candidate.name} ({stock_code}) | "
                        f"상승률: {candidate.current_change_rate:+.2f}% | "
                        f"거래량: {candidate.get_volume_ratio():.2f}배"
                    )
                
                # GUI 로그 추가 (실패해도 계속 진행)
                try:
                    self._add_gui_log(
                        f"🚀 급등주: {candidate.name} ({stock_code}) "
                        f"{candidate.current_change_rate:+.2f}% ↑",
                        "orange"
                    )
                except Exception as gui_error:
                    log.debug(f"GUI 로그 추가 실패 (무시): {gui_error}")
                
                # 실시간 시세 등록 건너뛰기
                # → 급등주는 이미 surge_detector 후보군에 등록되어 실시간 데이터 수신 중
                # → 추가 등록 시 블로킹 발생 위험 (PyQt COM 호출 문제)
                log.info(f"✅ 실시간 시세: {stock_code} (surge_detector에서 이미 수신 중)")
                
                # 추가 완료 기록
                self.surge_detected_stocks.add(stock_code)
                
                log.info(f"현재 관심 종목 수: {len(self.watch_list)}개")
                
                # 🔥 단타 매매: 급등주 즉시 매수 (데이터 누적 대기 없이)
                try:
                    log.warning("=" * 70)
                    log.warning(f"🚀 급등주 즉시 매수 시도!")
                    log.warning(f"   종목: {candidate.name} ({stock_code})")
                    log.warning(f"   현재가: {candidate.current_price:,}원")
                    log.warning(f"   상승률: {candidate.current_change_rate:+.2f}%")
                    log.warning(f"   거래량 비율: {candidate.get_volume_ratio():.2f}배")
                    log.warning("=" * 70)
                    
                    # 즉시 매수 실행 (신호 생성 우회)
                    # 🆕 관심주 보너스 점수
                    base_strength = 3.0
                    if hasattr(candidate, 'candidate_type') and candidate.candidate_type == "watchlist":
                        base_strength = 4.0  # 관심주는 더 강한 신호 (보너스)
                        log.info("   ⭐ 관심주 보너스 점수 적용: 3.0 → 4.0")
                    
                    signal_result = {
                        'signal': 'BUY',
                        'strength': base_strength,
                        'reason': f"{'⭐관심주' if candidate.candidate_type == 'watchlist' else '급등주'} 감지 (상승률 {candidate.current_change_rate:+.2f}%, 거래량 {candidate.get_volume_ratio():.2f}배)",
                        'news_score': candidate.news_score  # 🆕 뉴스 점수 전달
                    }
                    
                    log.info(f"🔄 execute_buy 함수 호출 준비 완료")
                    self.execute_buy(stock_code, candidate.current_price, signal_result)
                    log.info(f"✅ execute_buy 함수 호출 완료")
                    
                except Exception as buy_error:
                    log.error("=" * 70)
                    log.error(f"❌ 급등주 즉시 매수 실패!")
                    log.error(f"   종목: {candidate.name} ({stock_code})")
                    log.error(f"   에러: {type(buy_error).__name__}: {str(buy_error)}")
                    log.error(f"   상세: {traceback.format_exc()}")
                    log.error("=" * 70)
                
            except Exception as e:
                log.error("=" * 70)
                log.error(f"❌ 급등주 추가 및 매수 중 오류!")
                log.error(f"   에러 타입: {type(e).__name__}")
                log.error(f"   에러 메시지: {str(e)}")
                log.error(f"   상세: {traceback.format_exc()}")
                log.error("=" * 70)
            finally:
                # 처리 완료 - 플래그 해제
                self.surge_processing = False
                log.info(f"✅ 급등주 처리 완료: {candidate.name} ({stock_code})")
    
    def get_status(self) -> Dict:
        """
        현재 상태 반환
        
        Returns:
            상태 정보 딕셔너리
        """
        stats = self.risk_manager.get_statistics()
        
        status = {
            'is_running': self.is_running,
            'watch_list': self.watch_list,
            'signal_count': self.signal_count,
            'positions': len(self.risk_manager.positions),
            'statistics': stats
        }
        
        # 급등주 감지 통계 추가
        if self.surge_detector:
            status['surge_detection'] = self.surge_detector.get_statistics()
            status['surge_detected_stocks'] = list(self.surge_detected_stocks)
        
        return status
    
    def _auto_start_callback(self):
        """
        자동 시작 콜백 (MarketScheduler에서 호출)
        """
        log.success("=" * 70)
        log.success("⏰ 자동 시작 시간 도래!")
        log.success("=" * 70)
        
        # GUI 로그 추가
        self._add_gui_log("⏰ 자동 시작 - 장 시작 시간입니다!", "green")
        
        # 실제 자동매매 시작 (재귀 방지)
        if not self.is_running:
            # start_trading() 대신 직접 시작 (시장 상태 체크 우회)
            self.is_running = True
            log.success("🚀 자동매매 시작!")
            
            # 급등주 모니터링 시작
            if self.surge_detector:
                self.surge_detector.start_monitoring()
            
            # 뉴스 자동 갱신 시작
            if self.news_enabled and self.news_crawler:
                interval = getattr(Config, 'NEWS_UPDATE_INTERVAL', 300)
                self.news_crawler.start_auto_update(interval=interval)
            
            # 시작 알림
            if self.notifier:
                self.notifier.notify_system_start()
            
            # 헬스 모니터링 시작
            if self.health_monitor:
                self.health_monitor.start()
            
            # 스케줄러 시작
            if self.scheduler:
                self.scheduler.start()
            
            # 현재 상태 출력
            self.risk_manager.print_status()
            
            # 자동 종료 스케줄 설정
            self.market_scheduler.schedule_auto_stop(self._auto_stop_callback)
            
            # QTimer 시작
            self.check_timer.start()
            log.info("✅ QTimer 기반 모니터링 시작 (5초 간격)")
    
    def _auto_stop_callback(self):
        """
        자동 종료 콜백 (MarketScheduler에서 호출)
        """
        log.warning("=" * 70)
        log.warning("⏰ 자동 종료 시간 도래 (장 마감)")
        log.warning("=" * 70)
        
        # GUI 로그 추가
        self._add_gui_log("⏰ 자동 종료 - 장 마감 시간입니다!", "orange")
        
        # 자동매매 중지
        if self.is_running:
            self.stop_trading()
    
    def _get_current_config(self) -> dict:
        """
        현재 설정값 수집 (블랙박스 기록용)
        
        매수/매도 시점의 모든 설정값을 수집하여
        나중에 성과 분석 시 활용할 수 있도록 합니다.
        
        Returns:
            설정값 딕셔너리
        """
        return {
            # 포지션 관리
            'POSITION_SIZE_PERCENT': Config.POSITION_SIZE_PERCENT,
            'MAX_STOCKS': Config.MAX_STOCKS,
            'AUTO_TRADING_RATIO': Config.AUTO_TRADING_RATIO,
            
            # 리스크 관리
            'STOP_LOSS_PERCENT': Config.STOP_LOSS_PERCENT,
            'TAKE_PROFIT_PERCENT': Config.TAKE_PROFIT_PERCENT,
            'DAILY_LOSS_LIMIT_PERCENT': Config.DAILY_LOSS_LIMIT_PERCENT,
            
            # 급등주 감지
            'SURGE_THRESHOLD': Config.SURGE_THRESHOLD,
            'SURGE_VOLUME_RATIO': Config.SURGE_VOLUME_RATIO,
            'SURGE_MONITORING_CHANGE_RATE': Config.SURGE_MONITORING_CHANGE_RATE,
            
            # 추가 매수 (물타기)
            'ENABLE_AVERAGE_DOWN': Config.ENABLE_AVERAGE_DOWN,
            'AVERAGE_DOWN_TRIGGER_PERCENT': Config.AVERAGE_DOWN_TRIGGER_PERCENT,
            'MAX_AVERAGE_DOWN_COUNT': Config.MAX_AVERAGE_DOWN_COUNT,
            'AVERAGE_DOWN_SIZE_RATIO': Config.AVERAGE_DOWN_SIZE_RATIO,
            
            # 뉴스 분석
            'ENABLE_NEWS_ANALYSIS': Config.ENABLE_NEWS_ANALYSIS,
            'NEWS_POSITIVE_SURGE_ADJUST': Config.NEWS_POSITIVE_SURGE_ADJUST,
            'NEWS_NEGATIVE_STOPLOSS_ADJUST': Config.NEWS_NEGATIVE_STOPLOSS_ADJUST,
            'NEWS_BUY_THRESHOLD': Config.NEWS_BUY_THRESHOLD,
            'NEWS_SELL_THRESHOLD': Config.NEWS_SELL_THRESHOLD,
            
            # 전략
            'MIN_SIGNAL_STRENGTH': Config.MIN_SIGNAL_STRENGTH,
            
            # 타임스탬프
            'recorded_at': datetime.now().isoformat()
        }
    
    def _safe_shutdown(self):
        """
        안전한 종료 (스케줄러 콜백용)
        
        모든 자동매매 작업을 정리하고 프로그램을 종료합니다.
        """
        log.warning("=" * 70)
        log.warning("🛑 자동 종료 시작 (스케줄러)")
        log.warning("=" * 70)
        
        try:
            # 매매 중지
            if self.is_running:
                self.stop_trading()
            
            log.success("안전한 종료 완료")
            
        except Exception as e:
            log.error(f"안전한 종료 중 오류: {e}")


# 테스트 코드
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    print("자동매매 엔진 테스트")
    print("=" * 60)
    
    # PyQt 애플리케이션 생성 (키움 API 필요)
    app = QApplication(sys.argv)
    
    # 키움 API 초기화
    kiwoom = KiwoomAPI()
    
    if not kiwoom.login():
        print("❌ 로그인 실패")
        sys.exit(1)
    
    # 자동매매 엔진 생성
    engine = TradingEngine(kiwoom)
    
    if not engine.initialize():
        print("❌ 엔진 초기화 실패")
        sys.exit(1)
    
    # 상태 출력
    status = engine.get_status()
    print(f"\n엔진 상태:")
    print(f"  실행 중: {status['is_running']}")
    print(f"  관심 종목: {', '.join(status['watch_list'])}")
    print(f"  보유 종목: {status['positions']}개")
    
    print("\n✅ 테스트 완료")
    sys.exit(0)

