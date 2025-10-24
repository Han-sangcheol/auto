"""
매매 API 테스트
"""

import pytest


@pytest.mark.unit
def test_create_order(client, sample_account):
    """주문 생성 테스트"""
    order_data = {
        "account_id": sample_account.id,
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "order_type": "buy",
        "price_type": "limit",
        "quantity": 10,
        "price": 70000
    }
    
    response = client.post("/api/v1/trading/order", json=order_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "005930"
    assert data["quantity"] == 10
    assert data["status"] == "pending"


@pytest.mark.unit
def test_get_orders(client, sample_account, sample_order):
    """주문 목록 조회 테스트"""
    response = client.get(f"/api/v1/trading/orders/{sample_account.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["stock_code"] == "005930"


@pytest.mark.unit
def test_cancel_order(client, sample_order):
    """주문 취소 테스트"""
    response = client.delete(f"/api/v1/trading/order/{sample_order.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.unit
def test_create_order_invalid_data(client, sample_account):
    """잘못된 데이터로 주문 생성 테스트"""
    order_data = {
        "account_id": sample_account.id,
        "stock_code": "005930",
        # stock_name 누락
        "order_type": "buy",
        "quantity": -10,  # 잘못된 수량
    }
    
    response = client.post("/api/v1/trading/order", json=order_data)
    
    # 422: Validation Error
    assert response.status_code == 422

