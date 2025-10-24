"""
거래 내역 관련 Pydantic 스키마
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TradeBase(BaseModel):
    """거래 기본 스키마"""
    stock_code: str
    stock_name: str
    trade_type: str  # 'buy', 'sell'
    quantity: int
    price: int
    total_amount: int
    fee: int = 0
    tax: int = 0
    profit_loss: Optional[int] = None


class TradeCreate(TradeBase):
    """거래 생성 스키마"""
    order_id: Optional[int] = None
    account_id: int


class TradeResponse(TradeBase):
    """거래 응답 스키마"""
    id: int
    order_id: Optional[int] = None
    account_id: int
    executed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TradeSummary(BaseModel):
    """거래 요약 스키마"""
    total_trades: int
    buy_trades: int
    sell_trades: int
    total_profit_loss: int
    win_rate: float
    average_profit: float
    average_loss: float

