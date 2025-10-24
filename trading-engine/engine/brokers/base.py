"""
브로커 어댑터 추상 클래스

다양한 증권사 API를 통일된 인터페이스로 사용하기 위한 추상 클래스입니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseBroker(ABC):
    """브로커 어댑터 추상 클래스"""
    
    @abstractmethod
    def login(self) -> bool:
        """
        로그인
        
        Returns:
            성공 여부
        """
        pass
    
    @abstractmethod
    def get_account_info(self) -> dict:
        """
        계좌 정보 조회
        
        Returns:
            계좌 정보 dict
        """
        pass
    
    @abstractmethod
    def get_balance(self) -> int:
        """
        예수금 조회
        
        Returns:
            예수금 (원)
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """
        보유 포지션 조회
        
        Returns:
            포지션 목록
        """
        pass
    
    @abstractmethod
    def buy(self, stock_code: str, quantity: int, price: Optional[int] = None) -> dict:
        """
        매수 주문
        
        Args:
            stock_code: 종목 코드
            quantity: 수량
            price: 가격 (None이면 시장가)
        
        Returns:
            주문 결과 dict
        """
        pass
    
    @abstractmethod
    def sell(self, stock_code: str, quantity: int, price: Optional[int] = None) -> dict:
        """
        매도 주문
        
        Args:
            stock_code: 종목 코드
            quantity: 수량
            price: 가격 (None이면 시장가)
        
        Returns:
            주문 결과 dict
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        주문 취소
        
        Args:
            order_id: 주문 ID
        
        Returns:
            취소 성공 여부
        """
        pass
    
    @abstractmethod
    def get_stock_info(self, stock_code: str) -> dict:
        """
        종목 정보 조회
        
        Args:
            stock_code: 종목 코드
        
        Returns:
            종목 정보 dict
        """
        pass
    
    @abstractmethod
    def register_realtime(self, stock_codes: List[str]):
        """
        실시간 데이터 수신 등록
        
        Args:
            stock_codes: 종목 코드 리스트
        """
        pass
    
    @abstractmethod
    def unregister_realtime(self, stock_codes: List[str]):
        """
        실시간 데이터 수신 해제
        
        Args:
            stock_codes: 종목 코드 리스트
        """
        pass

