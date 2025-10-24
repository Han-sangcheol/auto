"""
Trading Engine 핵심 클래스

자동매매 로직을 총괄합니다.

[파일 역할]
- 브로커 어댑터 통합
- 전략 실행 및 관리
- 리스크 관리 통합
- 이벤트 발행
- 실시간 데이터 처리
"""

from typing import Dict, List, Optional
from loguru import logger
from .risk_manager import RiskManager
from .config import Config
from ..strategies import MultiStrategy, MACrossoverStrategy, RSIStrategy, MACDStrategy
from ..strategies.surge_strategy import SurgeStrategy
from ..events.event_bus import EventBus, EventType
from ..events.redis_publisher import RedisEventPublisher


class TradingEngine:
    """자동매매 엔진"""
    
    def __init__(self, broker, config: Config = None):
        """
        Args:
            broker: 브로커 어댑터 (KiwoomBroker 등)
            config: 설정 객체 (선택)
        """
        self.broker = broker
        self.config = config or Config
        self.is_running = False
        
        # 관심 종목
        self.watch_list: List[str] = []
        
        # 리스크 관리자
        self.risk_manager = RiskManager(
            max_stocks=self.config.MAX_STOCKS,
            position_size_percent=self.config.POSITION_SIZE_PERCENT,
            stop_loss_percent=self.config.STOP_LOSS_PERCENT,
            take_profit_percent=self.config.TAKE_PROFIT_PERCENT,
            daily_loss_limit_percent=self.config.DAILY_LOSS_LIMIT_PERCENT
        )
        
        # 전략
        self.strategies = self._create_strategies()
        self.multi_strategy = MultiStrategy(
            self.strategies,
            min_signal_strength=self.config.MIN_SIGNAL_STRENGTH
        )
        
        # 급등주 전략 (옵션)
        self.surge_strategy: Optional[SurgeStrategy] = None
        if self.config.ENABLE_SURGE_DETECTION:
            self.surge_strategy = SurgeStrategy(
                broker=self.broker,
                surge_callback=self.on_surge_detected,
                candidate_count=self.config.SURGE_CANDIDATE_COUNT,
                min_change_rate=self.config.SURGE_MIN_CHANGE_RATE,
                min_volume_ratio=self.config.SURGE_MIN_VOLUME_RATIO,
                cooldown_minutes=self.config.SURGE_COOLDOWN_MINUTES
            )
        
        # 이벤트 버스
        self.event_bus = EventBus(use_redis=self.config.USE_REDIS_EVENTS)
        if self.config.USE_REDIS_EVENTS:
            self.event_bus.connect_redis(self.config.REDIS_URL)
        
        # 가격 데이터 저장 (전략 실행용)
        self.price_history: Dict[str, List[float]] = {}
        self.max_history_length = 100
        
        logger.info("TradingEngine 초기화 완료")
    
    def _create_strategies(self) -> List:
        """전략 생성"""
        return [
            MACrossoverStrategy(
                self.config.MA_SHORT_PERIOD,
                self.config.MA_LONG_PERIOD
            ),
            RSIStrategy(
                self.config.RSI_PERIOD,
                self.config.RSI_OVERSOLD,
                self.config.RSI_OVERBOUGHT
            ),
            MACDStrategy(
                self.config.MACD_FAST,
                self.config.MACD_SLOW,
                self.config.MACD_SIGNAL
            )
        ]
    
    def initialize(self) -> bool:
        """엔진 초기화"""
        try:
            logger.info("Trading Engine 초기화 중...")
            
            # 계좌 정보 조회
            account_info = self.broker.get_account_info()
            logger.info(f"계좌 정보: {account_info}")
            
            # 잔고 설정
            balance = self.broker.get_balance()
            self.risk_manager.set_initial_balance(balance)
            
            # 보유 포지션 조회 및 동기화
            positions = self.broker.get_positions()
            logger.info(f"보유 포지션: {len(positions)}개")
            
            for pos in positions:
                self.risk_manager.add_position(
                    stock_code=pos['code'],
                    stock_name=pos['name'],
                    quantity=pos['quantity'],
                    entry_price=pos['buy_price']
                )
            
            # 급등주 전략 초기화
            if self.surge_strategy:
                if not self.surge_strategy.initialize():
                    logger.warning("급등주 전략 초기화 실패 - 기능 비활성화")
                    self.surge_strategy = None
            
            # 실시간 데이터 콜백 설정
            self.broker.set_real_data_callback(self.on_price_update)
            
            # 이벤트 발행
            self.event_bus.publish(EventType.ENGINE_STARTED, {
                'balance': balance,
                'positions': len(positions)
            })
            
            logger.success("Trading Engine 초기화 완료")
            return True
        
        except Exception as e:
            logger.error(f"엔진 초기화 실패: {e}")
            self.event_bus.publish(EventType.ERROR_OCCURRED, {'error': str(e)})
            return False
    
    def start(self):
        """자동매매 시작"""
        if self.is_running:
            logger.warning("이미 실행 중입니다.")
            return
        
        self.is_running = True
        logger.success("🚀 자동매매 시작")
        
        # 관심 종목 실시간 등록
        if self.watch_list:
            self.broker.register_realtime(self.watch_list)
        
        # 급등주 모니터링 시작
        if self.surge_strategy:
            self.surge_strategy.start_monitoring()
        
        self.event_bus.publish(EventType.ENGINE_STARTED, {})
    
    def stop(self):
        """자동매매 중지"""
        if not self.is_running:
            logger.warning("실행 중이 아닙니다.")
            return
        
        self.is_running = False
        
        # 급등주 모니터링 중지
        if self.surge_strategy:
            self.surge_strategy.stop_monitoring()
        
        logger.info("⏸️  자동매매 중지")
        self.event_bus.publish(EventType.ENGINE_STOPPED, {})
    
    def add_to_watchlist(self, stock_code: str):
        """관심 종목 추가"""
        if stock_code not in self.watch_list:
            self.watch_list.append(stock_code)
            logger.info(f"관심 종목 추가: {stock_code}")
            
            if self.is_running:
                self.broker.register_realtime([stock_code])
    
    def remove_from_watchlist(self, stock_code: str):
        """관심 종목 제거"""
        if stock_code in self.watch_list:
            self.watch_list.remove(stock_code)
            logger.info(f"관심 종목 제거: {stock_code}")
    
    def execute_buy(self, stock_code: str, stock_name: str, quantity: int, price: Optional[int] = None):
        """매수 주문"""
        try:
            # 주문 실행
            order_result = self.broker.buy(stock_code, quantity, price)
            
            if order_result['status'] != 'failed':
                # 포지션 추가
                entry_price = price or 0  # TODO: 체결가 사용
                self.risk_manager.add_position(stock_code, stock_name, quantity, entry_price)
                
                # 이벤트 발행
                self.event_bus.publish(EventType.ORDER_PLACED, {
                    'stock_code': stock_code,
                    'order_type': 'buy',
                    'quantity': quantity,
                    'price': price
                })
                
                logger.success(f"매수 주문 완료: {stock_code} {quantity}주")
            
            return order_result
        
        except Exception as e:
            logger.error(f"매수 주문 실패: {e}")
            self.event_bus.publish(EventType.ORDER_FAILED, {'error': str(e)})
            return None
    
    def execute_sell(self, stock_code: str, quantity: int, price: Optional[int] = None, reason: str = ""):
        """매도 주문"""
        try:
            # 주문 실행
            order_result = self.broker.sell(stock_code, quantity, price)
            
            if order_result['status'] != 'failed':
                # 포지션 제거
                sell_price = price or 0  # TODO: 체결가 사용
                self.risk_manager.remove_position(stock_code, sell_price, reason)
                
                # 이벤트 발행
                self.event_bus.publish(EventType.ORDER_PLACED, {
                    'stock_code': stock_code,
                    'order_type': 'sell',
                    'quantity': quantity,
                    'price': price,
                    'reason': reason
                })
                
                logger.success(f"매도 주문 완료: {stock_code} {quantity}주")
            
            return order_result
        
        except Exception as e:
            logger.error(f"매도 주문 실패: {e}")
            self.event_bus.publish(EventType.ORDER_FAILED, {'error': str(e)})
            return None
    
    def on_price_update(self, stock_code: str, price_data: dict):
        """실시간 가격 업데이트 콜백"""
        try:
            current_price = price_data['current_price']
            
            # 가격 히스토리 업데이트
            if stock_code not in self.price_history:
                self.price_history[stock_code] = []
            
            self.price_history[stock_code].append(current_price)
            if len(self.price_history[stock_code]) > self.max_history_length:
                self.price_history[stock_code] = self.price_history[stock_code][-self.max_history_length:]
            
            # 리스크 관리자에 가격 업데이트
            self.risk_manager.update_position_price(stock_code, current_price)
            
            # 급등주 전략에 전달
            if self.surge_strategy and self.surge_strategy.is_monitoring:
                self.surge_strategy.on_price_update(stock_code, price_data)
            
            # 보유 포지션에 대해 손절/익절 확인
            self._check_risk_management(stock_code)
            
            # 관심 종목에 대해 전략 시그널 확인
            if stock_code in self.watch_list:
                self._check_strategy_signals(stock_code)
            
            # 이벤트 발행
            self.event_bus.publish(EventType.PRICE_UPDATE, price_data)
            
        except Exception as e:
            logger.error(f"가격 업데이트 처리 중 오류: {e}")
    
    def _check_risk_management(self, stock_code: str):
        """리스크 관리 확인 (손절/익절)"""
        position = self.risk_manager.positions.get(stock_code)
        if not position:
            return
        
        # 손절매 확인
        if self.risk_manager.check_stop_loss(position):
            self.execute_sell(stock_code, position.quantity, reason="손절매")
            self.event_bus.publish(EventType.STOP_LOSS_TRIGGERED, {
                'stock_code': stock_code,
                'position': position
            })
        
        # 익절매 확인
        elif self.risk_manager.check_take_profit(position):
            self.execute_sell(stock_code, position.quantity, reason="익절매")
            self.event_bus.publish(EventType.TAKE_PROFIT_TRIGGERED, {
                'stock_code': stock_code,
                'position': position
            })
    
    def _check_strategy_signals(self, stock_code: str):
        """전략 시그널 확인"""
        prices = self.price_history.get(stock_code, [])
        if len(prices) < 30:
            return
        
        # 통합 전략 실행
        result = self.multi_strategy.generate_signal(prices)
        signal = result['signal']
        
        from ..strategies.base import SignalType
        
        # 매수 신호
        if signal == SignalType.BUY:
            # 리스크 검증
            is_valid, reason = self.risk_manager.validate_new_position(stock_code)
            if is_valid:
                # 포지션 크기 계산
                stock_info = self.broker.get_stock_info(stock_code)
                price = stock_info.get('price', 0)
                quantity = self.risk_manager.calculate_position_size(price)
                
                if quantity > 0:
                    self.execute_buy(stock_code, stock_info.get('name', ''), quantity)
            
            self.event_bus.publish(EventType.SIGNAL_GENERATED, {
                'stock_code': stock_code,
                'signal': 'BUY',
                'result': result
            })
        
        # 매도 신호
        elif signal == SignalType.SELL:
            position = self.risk_manager.positions.get(stock_code)
            if position:
                self.execute_sell(stock_code, position.quantity, reason="전략 신호")
            
            self.event_bus.publish(EventType.SIGNAL_GENERATED, {
                'stock_code': stock_code,
                'signal': 'SELL',
                'result': result
            })
    
    def on_surge_detected(self, stock_code: str, candidate):
        """급등주 감지 콜백"""
        logger.warning(f"🚀 급등주 감지: {candidate}")
        
        # 이벤트 발행
        self.event_bus.publish(EventType.SURGE_DETECTED, {
            'stock_code': stock_code,
            'candidate': {
                'name': candidate.name,
                'price': candidate.current_price,
                'change_rate': candidate.current_change_rate,
                'volume_ratio': candidate.get_volume_ratio()
            }
        })
        
        # 자동 승인 모드
        if self.config.SURGE_AUTO_APPROVE:
            # 관심 종목에 추가
            self.add_to_watchlist(stock_code)
            logger.info(f"급등주 자동 추가: {stock_code}")
    
    def get_status(self) -> dict:
        """엔진 상태 조회"""
        stats = self.risk_manager.get_statistics()
        
        return {
            'is_running': self.is_running,
            'watch_list': self.watch_list,
            'risk_manager': stats,
            'event_bus': self.event_bus.get_statistics()
        }

