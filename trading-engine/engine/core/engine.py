"""
Trading Engine 핵심 클래스

자동매매 로직을 총괄합니다.
"""

from typing import Dict, List, Optional
from loguru import logger


class TradingEngine:
    """자동매매 엔진"""
    
    def __init__(self, broker):
        """
        Args:
            broker: 브로커 어댑터 (KiwoomBroker 등)
        """
        self.broker = broker
        self.is_running = False
        self.watch_list: List[str] = []
        self.positions: Dict[str, dict] = {}
        
        logger.info("TradingEngine 초기화")
    
    def initialize(self) -> bool:
        """
        엔진 초기화
        
        Returns:
            초기화 성공 여부
        """
        try:
            # 계좌 정보 조회
            account_info = self.broker.get_account_info()
            logger.info(f"계좌 정보: {account_info}")
            
            # 보유 포지션 조회
            positions = self.broker.get_positions()
            logger.info(f"보유 포지션: {len(positions)}개")
            
            self.positions = {pos['stock_code']: pos for pos in positions}
            
            return True
        
        except Exception as e:
            logger.error(f"엔진 초기화 실패: {e}")
            return False
    
    def start(self):
        """자동매매 시작"""
        if self.is_running:
            logger.warning("이미 실행 중입니다.")
            return
        
        self.is_running = True
        logger.success("🚀 자동매매 시작")
        
        # TODO: 실시간 데이터 수신 등록
        # TODO: 전략 실행
    
    def stop(self):
        """자동매매 중지"""
        if not self.is_running:
            logger.warning("실행 중이 아닙니다.")
            return
        
        self.is_running = False
        logger.info("⏸️  자동매매 중지")
        
        # TODO: 실시간 데이터 수신 해제
    
    def add_to_watchlist(self, stock_code: str):
        """관심 종목 추가"""
        if stock_code not in self.watch_list:
            self.watch_list.append(stock_code)
            logger.info(f"관심 종목 추가: {stock_code}")
            
            # 실시간 데이터 등록
            # self.broker.register_realtime(stock_code)
    
    def remove_from_watchlist(self, stock_code: str):
        """관심 종목 제거"""
        if stock_code in self.watch_list:
            self.watch_list.remove(stock_code)
            logger.info(f"관심 종목 제거: {stock_code}")
            
            # 실시간 데이터 해제
            # self.broker.unregister_realtime(stock_code)
    
    def execute_buy(self, stock_code: str, quantity: int, price: Optional[int] = None):
        """매수 주문"""
        try:
            order_result = self.broker.buy(stock_code, quantity, price)
            logger.info(f"매수 주문: {stock_code} {quantity}주")
            return order_result
        
        except Exception as e:
            logger.error(f"매수 주문 실패: {e}")
            return None
    
    def execute_sell(self, stock_code: str, quantity: int, price: Optional[int] = None):
        """매도 주문"""
        try:
            order_result = self.broker.sell(stock_code, quantity, price)
            logger.info(f"매도 주문: {stock_code} {quantity}주")
            return order_result
        
        except Exception as e:
            logger.error(f"매도 주문 실패: {e}")
            return None
    
    def on_price_update(self, stock_code: str, price_data: dict):
        """
        실시간 가격 업데이트 콜백
        
        Args:
            stock_code: 종목 코드
            price_data: 가격 정보 dict
        """
        # TODO: 전략 시그널 확인
        # TODO: 리스크 관리
        pass

