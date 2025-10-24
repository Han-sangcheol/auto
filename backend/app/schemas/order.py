"""
주문 관련 Pydantic 스키마
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class OrderBase(BaseModel):
    """주문 기본 스키마"""
    stock_code: str
    stock_name: str
    order_type: str  # 'buy', 'sell'
    price_type: str  # 'market', 'limit'
    quantity: int
    price: Optional[int] = None
    strategy_name: Optional[str] = None
    reason: Optional[str] = None
    
    @field_validator('order_type')
    @classmethod
    def validate_order_type(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError('order_type must be "buy" or "sell"')
        return v
    
    @field_validator('price_type')
    @classmethod
    def validate_price_type(cls, v):
        if v not in ['market', 'limit']:
            raise ValueError('price_type must be "market" or "limit"')
        return v


class OrderCreate(OrderBase):
    """주문 생성 스키마"""
    account_id: int


class OrderUpdate(BaseModel):
    """주문 수정 스키마"""
    status: Optional[str] = None
    filled_quantity: Optional[int] = None
    filled_price: Optional[int] = None


class OrderResponse(OrderBase):
    """주문 응답 스키마"""
    id: int
    account_id: int
    status: str
    filled_quantity: int
    filled_price: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrderCancelRequest(BaseModel):
    """주문 취소 요청 스키마"""
    order_id: int
    reason: Optional[str] = None

