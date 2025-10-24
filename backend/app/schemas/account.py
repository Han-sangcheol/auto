"""
계좌 관련 Pydantic 스키마

API 요청/응답 데이터 검증을 위한 스키마입니다.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    """계좌 기본 스키마"""
    broker: str
    account_no: str
    account_name: Optional[str] = None
    account_type: str  # 'simulation', 'real'
    initial_balance: int
    is_active: bool = True


class AccountCreate(AccountBase):
    """계좌 생성 스키마"""
    pass


class AccountUpdate(BaseModel):
    """계좌 수정 스키마"""
    account_name: Optional[str] = None
    is_active: Optional[bool] = None


class AccountResponse(AccountBase):
    """계좌 응답 스키마"""
    id: int
    user_id: int
    current_balance: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AccountBalanceResponse(BaseModel):
    """계좌 잔고 응답 스키마"""
    account_id: int
    current_balance: int
    initial_balance: int
    total_profit_loss: int
    total_profit_loss_percent: float
    cash_available: int
    stock_value: int
    
    model_config = ConfigDict(from_attributes=True)

