"""
포지션 관련 Pydantic 스키마
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class PositionBase(BaseModel):
    """포지션 기본 스키마"""
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: int


class PositionCreate(PositionBase):
    """포지션 생성 스키마"""
    account_id: int


class PositionUpdate(BaseModel):
    """포지션 수정 스키마"""
    quantity: Optional[int] = None
    avg_price: Optional[int] = None
    current_price: Optional[int] = None


class PositionResponse(PositionBase):
    """포지션 응답 스키마"""
    id: int
    account_id: int
    current_price: int
    profit_loss: int
    profit_loss_percent: Decimal
    entry_time: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

