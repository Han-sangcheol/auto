"""
계좌 Repository

계좌 관련 데이터 접근 로직을 처리합니다.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import Account, Position
from .base_repo import BaseRepository


class AccountRepository(BaseRepository[Account]):
    """계좌 Repository"""
    
    def __init__(self):
        super().__init__(Account)
    
    def get_by_user(self, db: Session, user_id: int) -> List[Account]:
        """사용자의 계좌 목록 조회"""
        return db.query(Account).filter(Account.user_id == user_id).all()
    
    def get_by_account_no(
        self, 
        db: Session, 
        broker: str, 
        account_no: str
    ) -> Optional[Account]:
        """계좌번호로 조회"""
        return db.query(Account).filter(
            Account.broker == broker,
            Account.account_no == account_no
        ).first()
    
    def get_active_accounts(self, db: Session, user_id: int) -> List[Account]:
        """활성화된 계좌 목록"""
        return db.query(Account).filter(
            Account.user_id == user_id,
            Account.is_active == True
        ).all()
    
    def update_balance(
        self, 
        db: Session, 
        account_id: int, 
        new_balance: int
    ) -> Optional[Account]:
        """잔고 업데이트"""
        account = self.get(db, account_id)
        if account:
            account.current_balance = new_balance
            db.commit()
            db.refresh(account)
        return account
    
    def get_account_summary(self, db: Session, account_id: int) -> dict:
        """계좌 요약 정보"""
        account = self.get(db, account_id)
        if not account:
            return {}
        
        # 포지션 정보
        positions = db.query(Position).filter(
            Position.account_id == account_id
        ).all()
        
        stock_value = sum(
            pos.current_price * pos.quantity for pos in positions
        )
        
        total_value = account.current_balance + stock_value
        total_pl = total_value - account.initial_balance
        total_pl_pct = (total_pl / account.initial_balance * 100) if account.initial_balance > 0 else 0
        
        return {
            'account_id': account.id,
            'current_balance': account.current_balance,
            'initial_balance': account.initial_balance,
            'stock_value': stock_value,
            'total_value': total_value,
            'total_profit_loss': total_pl,
            'total_profit_loss_percent': total_pl_pct,
            'cash_available': account.current_balance,
            'positions_count': len(positions),
        }


# 싱글톤 인스턴스
account_repo = AccountRepository()

