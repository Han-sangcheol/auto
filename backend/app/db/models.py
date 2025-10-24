"""
SQLAlchemy 데이터베이스 모델

데이터베이스 테이블을 Python 클래스로 정의합니다.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, BigInteger, 
    DateTime, ForeignKey, Text, DECIMAL, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .session import Base


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    """계좌 모델"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    broker = Column(String(50), nullable=False)
    account_no = Column(String(50), nullable=False)
    account_name = Column(String(100))
    account_type = Column(String(20), nullable=False)  # 'simulation', 'real'
    initial_balance = Column(BigInteger, nullable=False, default=0)
    current_balance = Column(BigInteger, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계
    user = relationship("User", back_populates="accounts")
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="account", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="account", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_account_broker_no', 'broker', 'account_no', unique=True),
    )


class Position(Base):
    """포지션 모델"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Integer, nullable=False)
    current_price = Column(Integer, nullable=False, default=0)
    profit_loss = Column(BigInteger, default=0)
    profit_loss_percent = Column(DECIMAL(10, 2), default=0)
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계
    account = relationship("Account", back_populates="positions")
    
    __table_args__ = (
        Index('ix_position_account_stock', 'account_id', 'stock_code', unique=True),
    )


class Order(Base):
    """주문 모델"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100), nullable=False)
    order_type = Column(String(10), nullable=False)  # 'buy', 'sell'
    price_type = Column(String(20), nullable=False)  # 'market', 'limit'
    quantity = Column(Integer, nullable=False)
    price = Column(Integer)
    status = Column(String(20), nullable=False, default='pending', index=True)
    filled_quantity = Column(Integer, default=0)
    filled_price = Column(Integer)
    strategy_name = Column(String(100))
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계
    account = relationship("Account", back_populates="orders")
    trades = relationship("Trade", back_populates="order")


class Trade(Base):
    """거래 내역 모델"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"))
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100), nullable=False)
    trade_type = Column(String(10), nullable=False)  # 'buy', 'sell'
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    total_amount = Column(BigInteger, nullable=False)
    fee = Column(Integer, default=0)
    tax = Column(Integer, default=0)
    profit_loss = Column(BigInteger)
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 관계
    order = relationship("Order", back_populates="trades")
    account = relationship("Account", back_populates="trades")


class Strategy(Base):
    """전략 설정 모델"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    parameters = Column(JSONB, nullable=False, default={})
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계
    account = relationship("Account", back_populates="strategies")
    
    __table_args__ = (
        Index('ix_strategy_account_name', 'account_id', 'name', unique=True),
    )


class SurgeDetection(Base):
    """급등주 감지 기록 모델"""
    __tablename__ = "surge_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100), nullable=False)
    detection_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    price = Column(Integer, nullable=False)
    change_rate = Column(DECIMAL(10, 2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    volume_ratio = Column(DECIMAL(10, 2), nullable=False)
    trade_value = Column(BigInteger)
    status = Column(String(20), nullable=False, default='detected', index=True)
    approved_at = Column(DateTime(timezone=True))
    executed_at = Column(DateTime(timezone=True))


class MarketData(Base):
    """시세 데이터 모델 (TimescaleDB)"""
    __tablename__ = "market_data"
    
    timestamp = Column(DateTime(timezone=True), primary_key=True)
    stock_code = Column(String(20), primary_key=True, index=True)
    open_price = Column(Integer, nullable=False)
    high_price = Column(Integer, nullable=False)
    low_price = Column(Integer, nullable=False)
    close_price = Column(Integer, nullable=False)
    volume = Column(BigInteger, nullable=False)
    trade_value = Column(BigInteger)
    change_rate = Column(DECIMAL(10, 2))


class SystemLog(Base):
    """시스템 로그 모델"""
    __tablename__ = "system_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

