"""
주문 Repository

주문 관련 데이터 접근 로직을 처리합니다.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models import Order
from .base_repo import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """주문 Repository"""
    
    def __init__(self):
        super().__init__(Order)
    
    def get_by_account(
        self, 
        db: Session, 
        account_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """계좌의 주문 목록 (최신순)"""
        return db.query(Order).filter(
            Order.account_id == account_id
        ).order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    
    def get_by_status(
        self, 
        db: Session, 
        account_id: int, 
        status: str
    ) -> List[Order]:
        """상태별 주문 조회"""
        return db.query(Order).filter(
            Order.account_id == account_id,
            Order.status == status
        ).all()
    
    def get_pending_orders(self, db: Session, account_id: int) -> List[Order]:
        """대기 중인 주문 목록"""
        return self.get_by_status(db, account_id, 'pending')
    
    def get_recent_orders(
        self, 
        db: Session, 
        account_id: int, 
        hours: int = 24
    ) -> List[Order]:
        """최근 N시간 이내 주문"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return db.query(Order).filter(
            Order.account_id == account_id,
            Order.created_at >= since
        ).order_by(desc(Order.created_at)).all()
    
    def update_status(
        self, 
        db: Session, 
        order_id: int, 
        status: str,
        filled_quantity: Optional[int] = None,
        filled_price: Optional[int] = None
    ) -> Optional[Order]:
        """주문 상태 업데이트"""
        order = self.get(db, order_id)
        if order:
            order.status = status
            if filled_quantity is not None:
                order.filled_quantity = filled_quantity
            if filled_price is not None:
                order.filled_price = filled_price
            db.commit()
            db.refresh(order)
        return order
    
    def cancel_order(self, db: Session, order_id: int) -> Optional[Order]:
        """주문 취소"""
        return self.update_status(db, order_id, 'cancelled')


# 싱글톤 인스턴스
order_repo = OrderRepository()

