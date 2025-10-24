"""
포지션 Repository

포지션 관련 데이터 접근 로직을 처리합니다.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import Position
from .base_repo import BaseRepository


class PositionRepository(BaseRepository[Position]):
    """포지션 Repository"""
    
    def __init__(self):
        super().__init__(Position)
    
    def get_by_account(self, db: Session, account_id: int) -> List[Position]:
        """계좌의 포지션 목록"""
        return db.query(Position).filter(
            Position.account_id == account_id
        ).all()
    
    def get_by_stock(
        self, 
        db: Session, 
        account_id: int, 
        stock_code: str
    ) -> Optional[Position]:
        """특정 종목 포지션 조회"""
        return db.query(Position).filter(
            Position.account_id == account_id,
            Position.stock_code == stock_code
        ).first()
    
    def update_price(
        self, 
        db: Session, 
        position_id: int, 
        current_price: int
    ) -> Optional[Position]:
        """현재가 업데이트 및 손익 계산"""
        position = self.get(db, position_id)
        if position:
            position.current_price = current_price
            position.profit_loss = (current_price - position.avg_price) * position.quantity
            position.profit_loss_percent = (
                (current_price - position.avg_price) / position.avg_price * 100
            )
            db.commit()
            db.refresh(position)
        return position
    
    def add_quantity(
        self, 
        db: Session, 
        account_id: int, 
        stock_code: str,
        stock_name: str,
        quantity: int, 
        price: int
    ) -> Position:
        """수량 추가 (평균 단가 재계산)"""
        position = self.get_by_stock(db, account_id, stock_code)
        
        if position:
            # 기존 포지션에 추가
            total_cost = (position.avg_price * position.quantity) + (price * quantity)
            total_quantity = position.quantity + quantity
            position.avg_price = int(total_cost / total_quantity)
            position.quantity = total_quantity
            db.commit()
            db.refresh(position)
        else:
            # 신규 포지션 생성
            position = Position(
                account_id=account_id,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                avg_price=price,
                current_price=price
            )
            db.add(position)
            db.commit()
            db.refresh(position)
        
        return position
    
    def reduce_quantity(
        self, 
        db: Session, 
        account_id: int, 
        stock_code: str, 
        quantity: int
    ) -> Optional[Position]:
        """수량 감소 (매도)"""
        position = self.get_by_stock(db, account_id, stock_code)
        
        if not position:
            return None
        
        if position.quantity <= quantity:
            # 전량 매도 - 포지션 삭제
            db.delete(position)
            db.commit()
            return None
        else:
            # 부분 매도
            position.quantity -= quantity
            db.commit()
            db.refresh(position)
            return position


# 싱글톤 인스턴스
position_repo = PositionRepository()

