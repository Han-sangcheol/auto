"""
pytest 설정 및 픽스처
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db


# 테스트용 인메모리 데이터베이스
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """테스트용 데이터베이스 세션"""
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 세션 생성
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # 테이블 삭제
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """테스트 클라이언트"""
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_account(db):
    """샘플 계좌"""
    from app.db import models
    
    account = models.Account(
        user_id=1,
        broker="kiwoom",
        account_number="8888888888",
        account_name="모의투자",
        initial_balance=10000000,
        current_balance=10000000
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return account


@pytest.fixture
def sample_position(db, sample_account):
    """샘플 포지션"""
    from app.db import models
    
    position = models.Position(
        account_id=sample_account.id,
        stock_code="005930",
        stock_name="삼성전자",
        quantity=10,
        avg_price=70000,
        current_price=72000
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    
    return position


@pytest.fixture
def sample_order(db, sample_account):
    """샘플 주문"""
    from app.db import models
    from datetime import datetime
    
    order = models.Order(
        account_id=sample_account.id,
        stock_code="005930",
        stock_name="삼성전자",
        order_type="buy",
        price_type="limit",
        quantity=10,
        price=70000,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order

