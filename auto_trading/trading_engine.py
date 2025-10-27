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

from PyQt5.QtCore import QTimer

from kiwoom_api import KiwoomAPI
from strategies import MultiStrategy, SignalType, create_default_strategies
from risk_manager import RiskManager
from indicators import calculate_all_indicators
from surge_detector import SurgeDetector
from logger import log
from config import Config

# 뉴스 분석 및 알림 시스템 (선택적 로드)
try:
    from news_crawler import NewsCrawler
    from sentiment_analyzer import SentimentAnalyzer
    from news_strategy import NewsBasedStrategy
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    log.warning("뉴스 분석 모듈을 로드할 수 없습니다. (패키지 미설치)")

try:
    from notification import Notifier
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    log.warning("알림 시스템을 로드할 수 없습니다. (win10toast 미설치)")

try:
    from health_monitor import HealthMonitor
    HEALTH_MONITOR_AVAILABLE = True
except ImportError:
    HEALTH_MONITOR_AVAILABLE = False
    log.warning("헬스 모니터를 로드할 수 없습니다. (psutil 미설치)")


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
            time.sleep(2)
            
            # 1. 계좌 정보 조회
            balance_info = self.kiwoom.get_balance()
            if not balance_info:
                log.warning("잔고 조회 실패 - 기본값 사용 (모의투자 초기 자금)")
                # 모의투자 기본 초기 자금: 10,000,000원
                cash = 10000000
            else:
                cash = balance_info.get('cash', 10000000)
            
            self.risk_manager.set_initial_balance(cash)
            log.info(f"계좌 잔고: {cash:,}원")
            
            # 2. 보유 종목 조회
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
            
            # 3. 실시간 시세 등록 (관심 종목)
            self.kiwoom.set_real_data_callback(self.on_price_update)
            self.kiwoom.register_real_data(self.watch_list)
            
            # 4. 급등주 감지기 초기화 (옵션)
            if Config.ENABLE_SURGE_DETECTION:
                log.info("급등주 감지 기능 활성화 중...")
                self.surge_detector = SurgeDetector(
                    self.kiwoom,
                    self.on_surge_detected
                )
                if self.surge_detector.initialize():
                    log.success("급등주 감지 기능 활성화 완료")
                else:
                    log.warning("급등주 감지 기능 초기화 실패 - 기능 비활성화")
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
            
            log.success("자동매매 엔진 초기화 완료")
            return True
            
        except Exception as e:
            log.error(f"엔진 초기화 중 오류: {e}")
            return False
    
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
        
        self.is_running = True
        log.success("🚀 자동매매 시작!")
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
        
        # 현재 상태 출력
        self.risk_manager.print_status()
        
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
            
            # 장 운영 시간 확인
            if not self.is_market_open():
                if datetime.now().time() >= dt_time(15, 30):  # 3시 30분 이후
                    log.info("장 마감. 자동매매를 종료합니다.")
                    self.stop_trading()
                    return
                # 장 시간 외에는 체크만 하고 리턴
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
        장 운영 시간 확인
        
        Returns:
            장 운영 중 여부
        """
        now = datetime.now()
        
        # 주말 체크
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 장 시간 체크 (9:00 ~ 15:30)
        current_time = now.time()
        market_open = dt_time(9, 0)
        market_close = dt_time(15, 30)
        
        return market_open <= current_time <= market_close
    
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
            
            # 관심 종목의 실시간 가격 표시 (5번째 업데이트마다) - 단타에 적합
            if len(self.price_history[stock_code]) % 5 == 0:
                log.info(
                    f"📊 실시간: {stock_code} {current_price:,}원 "
                    f"({change_rate:+.2f}%) | 데이터: {len(self.price_history[stock_code])}개"
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
                log.warning("=" * 70)
                log.warning(f"🔔 매도 신호 발생! {stock_code}")
                log.warning(f"   현재가: {current_price:,}원")
                log.warning(f"   신호 강도: {signal_result['strength']:.2f}")
                log.warning(f"   사유: {signal_result['reason']}")
                log.warning("=" * 70)
                self.execute_sell(stock_code, current_price, signal_result)
                
        except Exception as e:
            log.error(f"신호 처리 중 오류: {e}")
    
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
            
            # 리스크 검증
            log.info(f"🔍 [execute_buy] 리스크 검증 중...")
            is_valid, reason = self.risk_manager.validate_new_position(stock_code)
            if not is_valid:
                log.warning(f"매수 불가: {stock_code} - {reason}")
                return
            log.info(f"✅ [execute_buy] 리스크 검증 통과")
            
            # 매수 수량 계산
            log.info(f"🔍 [execute_buy] 매수 수량 계산 중...")
            quantity = self.risk_manager.calculate_position_size(current_price)
            if quantity < 1:
                log.warning(f"매수 불가: {stock_code} - 수량 부족")
                return
            log.info(f"✅ [execute_buy] 수량 계산 완료: {quantity}주")
            
            # 주문 전송
            log.info(
                f"📈 매수 시도: {stock_code} {quantity}주 @ {current_price:,}원 | "
                f"신호 강도: {signal_result['strength']:.2f}"
            )
            
            log.info(f"🔍 [execute_buy] 키움 API buy_order 호출 중...")
            order_result = self.kiwoom.buy_order(
                stock_code,
                quantity,
                0  # 시장가 주문
            )
            log.info(f"✅ [execute_buy] buy_order 호출 완료, 결과: {order_result}")
            
            if order_result:
                # 포지션 추가
                stock_name = stock_code  # 실제로는 종목명 조회 필요
                position = self.risk_manager.add_position(
                    stock_code,
                    stock_name,
                    quantity,
                    current_price
                )
                
                if position:
                    total_cost = current_price * quantity
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
                    
                    # 알림 전송
                    if self.notifier:
                        self.notifier.notify_trade(
                            "매수",
                            stock_name,
                            quantity,
                            current_price
                        )
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
                    profit_rate = (profit_loss / (position.buy_price * position.quantity)) * 100
                    log.success("=" * 70)
                    log.success(f"✅ 매도 체결 완료!")
                    log.success(f"   종목: {stock_code}")
                    log.success(f"   수량: {position.quantity}주")
                    log.success(f"   매수가: {position.buy_price:,}원")
                    log.success(f"   매도가: {current_price:,}원")
                    log.success(f"   총 금액: {total_amount:,}원")
                    log.success(f"   손익: {profit_loss:+,}원 ({profit_rate:+.2f}%)")
                    log.success(f"   사유: {signal_result['reason']}")
                    log.success(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
                    log.success("=" * 70)
                    
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
        손절매/익절매 조건 확인 (단타 매매에 중요)
        """
        try:
            for stock_code, position in list(self.risk_manager.positions.items()):
                # 손절매 확인
                if self.risk_manager.check_stop_loss(position):
                    loss_rate = ((position.current_price - position.buy_price) / position.buy_price) * 100
                    log.warning("=" * 70)
                    log.warning(f"🚨 손절매 조건 감지!")
                    log.warning(f"   종목: {stock_code}")
                    log.warning(f"   매수가: {position.buy_price:,}원")
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
                    profit_rate = ((position.current_price - position.buy_price) / position.buy_price) * 100
                    log.warning("=" * 70)
                    log.warning(f"🎯 익절매 조건 감지!")
                    log.warning(f"   종목: {stock_code}")
                    log.warning(f"   매수가: {position.buy_price:,}원")
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
            
            # 주문 전송
            order_result = self.kiwoom.sell_order(
                stock_code,
                position.quantity,
                0  # 시장가 주문
            )
            
            if order_result:
                # 포지션 제거
                profit_loss = self.risk_manager.remove_position(
                    stock_code,
                    sell_price,
                    reason
                )
                
                if profit_loss is not None:
                    total_amount = sell_price * position.quantity
                    profit_rate = (profit_loss / (position.buy_price * position.quantity)) * 100
                    emoji = "✅" if profit_loss >= 0 else "❌"
                    log.success("=" * 70)
                    log.success(f"{emoji} 청산 체결 완료! ({reason})")
                    log.success(f"   종목: {stock_code}")
                    log.success(f"   수량: {position.quantity}주")
                    log.success(f"   매수가: {position.buy_price:,}원")
                    log.success(f"   매도가: {sell_price:,}원")
                    log.success(f"   총 금액: {total_amount:,}원")
                    log.success(f"   손익: {profit_loss:+,}원 ({profit_rate:+.2f}%)")
                    log.success(f"   사유: {reason}")
                    log.success(f"   시각: {datetime.now().strftime('%H:%M:%S')}")
                    log.success("=" * 70)
                    
                    # 알림 전송
                    if self.notifier:
                        if reason == "손절매":
                            self.notifier.notify_stop_loss(
                                position.stock_name,
                                position.quantity,
                                position.buy_price,
                                sell_price,
                                abs(profit_loss)
                            )
                        elif reason == "익절매":
                            self.notifier.notify_take_profit(
                                position.stock_name,
                                position.quantity,
                                position.buy_price,
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
            
            # 승인 요청
            surge_info = {
                'name': candidate.name,
                'price': candidate.current_price,
                'change_rate': candidate.current_change_rate,
                'volume_ratio': candidate.get_volume_ratio()
            }
            
            # 콜백 호출 (별도 스레드에서)
            def request_approval():
                try:
                    approved = self.surge_approval_callback(stock_code, candidate.name, surge_info)
                    if approved:
                        self.add_surge_stock(stock_code, candidate)
                    else:
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
                    
                    # GUI 로그 추가
                    self._add_gui_log(
                        f"🚀 급등주: {candidate.name} ({stock_code}) "
                        f"{candidate.current_change_rate:+.2f}% ↑",
                        "orange"
                    )
                    
                    # 실시간 시세 등록 (안전하게 처리)
                    try:
                        log.info(f"🔍 실시간 시세 등록 시도: {stock_code}")
                        time.sleep(1.0)  # API 호출 제한 방지 (1초 대기로 증가)
                        self.kiwoom.register_real_data([stock_code])
                        log.info(f"✅ 실시간 시세 등록 완료: {stock_code}")
                        time.sleep(0.5)  # 추가 안전 대기
                    except Exception as reg_error:
                        log.error(f"⚠️  실시간 시세 등록 실패: {stock_code} - {reg_error}")
                        log.error(f"   에러 타입: {type(reg_error).__name__}")
                        log.warning("   → 시세 등록은 실패했지만 급등주 추가는 계속 진행")
                    
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
                        signal_result = {
                            'signal': 'BUY',
                            'strength': 3.0,  # 급등주는 강한 신호
                            'reason': f"급등주 감지 (상승률 {candidate.current_change_rate:+.2f}%, 거래량 {candidate.get_volume_ratio():.2f}배)"
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

