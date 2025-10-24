"""
키움 증권 브로커 어댑터

키움 OpenAPI를 BaseBroker 인터페이스로 래핑합니다.
"""

from typing import List, Dict, Optional
from .base import BaseBroker
from loguru import logger


class KiwoomBroker(BaseBroker):
    """키움 증권 브로커 어댑터"""
    
    def __init__(self):
        """초기화"""
        # TODO: 기존 kiwoom_api.py를 여기로 통합
        logger.info("KiwoomBroker 초기화")
        self.ocx = None  # COM 객체
        self.account_number = None
    
    def login(self) -> bool:
        """로그인"""
        # TODO: 기존 kiwoom_api.py의 login 로직 사용
        logger.info("키움 로그인 시도")
        return True  # 임시
    
    def get_account_info(self) -> dict:
        """계좌 정보 조회"""
        # TODO: 기존 로직 사용
        return {
            "account_number": "모의투자",
            "name": "홍길동",
            "balance": 10000000
        }
    
    def get_balance(self) -> int:
        """예수금 조회"""
        # TODO: 기존 로직 사용
        return 10000000
    
    def get_positions(self) -> List[Dict]:
        """보유 포지션 조회"""
        # TODO: 기존 로직 사용
        return []
    
    def buy(self, stock_code: str, quantity: int, price: Optional[int] = None) -> dict:
        """매수 주문"""
        # TODO: 기존 로직 사용
        logger.info(f"매수: {stock_code} {quantity}주")
        return {"order_id": "12345", "status": "pending"}
    
    def sell(self, stock_code: str, quantity: int, price: Optional[int] = None) -> dict:
        """매도 주문"""
        # TODO: 기존 로직 사용
        logger.info(f"매도: {stock_code} {quantity}주")
        return {"order_id": "12346", "status": "pending"}
    
    def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        # TODO: 기존 로직 사용
        logger.info(f"주문 취소: {order_id}")
        return True
    
    def get_stock_info(self, stock_code: str) -> dict:
        """종목 정보 조회"""
        # TODO: 기존 로직 사용
        return {
            "code": stock_code,
            "name": "종목명",
            "price": 50000
        }
    
    def register_realtime(self, stock_codes: List[str]):
        """실시간 데이터 수신 등록"""
        # TODO: 기존 로직 사용
        logger.info(f"실시간 등록: {stock_codes}")
    
    def unregister_realtime(self, stock_codes: List[str]):
        """실시간 데이터 수신 해제"""
        # TODO: 기존 로직 사용
        logger.info(f"실시간 해제: {stock_codes}")

