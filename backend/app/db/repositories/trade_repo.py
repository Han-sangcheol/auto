"""
거래 내역 Repository

거래 내역 관련 데이터 접근 로직을 처리합니다.
"""

from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from ..models import Trade
from .base_repo import BaseRepository


class TradeRepository(BaseRepository[Trade]):
    """거래 내역 Repository"""
    
    def __init__(self):
        super().__init__(Trade)
    
    def get_by_account(
        self, 
        db: Session, 
        account_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Trade]:
        """계좌의 거래 내역 (최신순)"""
        return db.query(Trade).filter(
            Trade.account_id == account_id
        ).order_by(desc(Trade.executed_at)).offset(skip).limit(limit).all()
    
    def get_by_date_range(
        self, 
        db: Session, 
        account_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Trade]:
        """기간별 거래 내역"""
        return db.query(Trade).filter(
            Trade.account_id == account_id,
            Trade.executed_at >= start_date,
            Trade.executed_at <= end_date
        ).order_by(desc(Trade.executed_at)).all()
    
    def get_recent_trades(
        self, 
        db: Session, 
        account_id: int, 
        days: int = 7
    ) -> List[Trade]:
        """최근 N일 거래 내역"""
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(Trade).filter(
            Trade.account_id == account_id,
            Trade.executed_at >= since
        ).order_by(desc(Trade.executed_at)).all()
    
    def get_trade_summary(self, db: Session, account_id: int) -> dict:
        """거래 요약 통계"""
        trades = db.query(Trade).filter(
            Trade.account_id == account_id
        ).all()
        
        if not trades:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_profit_loss': 0,
                'win_rate': 0,
                'average_profit': 0,
                'average_loss': 0,
            }
        
        buy_trades = [t for t in trades if t.trade_type == 'buy']
        sell_trades = [t for t in trades if t.trade_type == 'sell']
        
        # 손익이 있는 거래만
        pl_trades = [t for t in sell_trades if t.profit_loss is not None]
        winning_trades = [t for t in pl_trades if t.profit_loss > 0]
        losing_trades = [t for t in pl_trades if t.profit_loss < 0]
        
        total_pl = sum(t.profit_loss for t in pl_trades)
        win_rate = (len(winning_trades) / len(pl_trades) * 100) if pl_trades else 0
        avg_profit = (sum(t.profit_loss for t in winning_trades) / len(winning_trades)) if winning_trades else 0
        avg_loss = (sum(t.profit_loss for t in losing_trades) / len(losing_trades)) if losing_trades else 0
        
        return {
            'total_trades': len(trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_profit_loss': total_pl,
            'win_rate': win_rate,
            'average_profit': avg_profit,
            'average_loss': avg_loss,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
        }


# 싱글톤 인스턴스
trade_repo = TradeRepository()

