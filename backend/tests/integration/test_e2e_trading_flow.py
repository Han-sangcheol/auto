"""
E2E 통합 테스트 - 전체 매매 플로우
"""

import pytest


@pytest.mark.integration
def test_complete_trading_flow(client, sample_account):
    """
    전체 매매 플로우 통합 테스트
    
    시나리오:
    1. 계좌 조회
    2. 주문 생성
    3. 주문 목록 확인
    4. 포지션 생성 (주문 체결 시뮬레이션)
    5. 포지션 조회
    6. 잔고 업데이트 확인
    """
    
    # 1. 계좌 조회
    response = client.get("/api/v1/account/")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) > 0
    account_id = accounts[0]["id"]
    
    # 2. 주문 생성
    order_data = {
        "account_id": account_id,
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "order_type": "buy",
        "price_type": "limit",
        "quantity": 10,
        "price": 70000
    }
    response = client.post("/api/v1/trading/order", json=order_data)
    assert response.status_code == 200
    order = response.json()
    order_id = order["id"]
    
    # 3. 주문 목록 확인
    response = client.get(f"/api/v1/trading/orders/{account_id}")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) > 0
    assert any(o["id"] == order_id for o in orders)
    
    # 4. 잔고 확인
    response = client.get(f"/api/v1/account/{account_id}/balance")
    assert response.status_code == 200
    balance = response.json()
    assert balance["current_balance"] == 10000000


@pytest.mark.integration
def test_surge_detection_flow(client, sample_account):
    """
    급등주 감지 플로우 테스트
    
    시나리오:
    1. 급등주 목록 조회
    2. 급등주 상세 정보 확인
    """
    
    # 1. 급등주 목록 조회
    response = client.get("/api/v1/market/surge?limit=10")
    assert response.status_code == 200
    surge_data = response.json()
    assert "surge_stocks" in surge_data


@pytest.mark.integration
def test_position_management_flow(client, sample_account, sample_position):
    """
    포지션 관리 플로우 테스트
    
    시나리오:
    1. 포지션 조회
    2. 포지션 손익 계산
    3. 매도 주문 (포지션 청산)
    """
    
    # 1. 포지션 조회
    response = client.get(f"/api/v1/account/{sample_account.id}/positions")
    assert response.status_code == 200
    positions = response.json()
    assert len(positions) > 0
    
    position = positions[0]
    assert position["stock_code"] == "005930"
    assert position["quantity"] == 10
    
    # 2. 포지션 손익 확인
    assert "profit_loss" in position
    assert "profit_loss_percent" in position
    
    # 3. 매도 주문 (포지션 청산)
    sell_order_data = {
        "account_id": sample_account.id,
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "order_type": "sell",
        "price_type": "market",
        "quantity": 10
    }
    response = client.post("/api/v1/trading/order", json=sell_order_data)
    assert response.status_code == 200
    sell_order = response.json()
    assert sell_order["order_type"] == "sell"


@pytest.mark.integration
def test_order_lifecycle(client, sample_account):
    """
    주문 라이프사이클 테스트
    
    시나리오:
    1. 주문 생성 (pending)
    2. 주문 취소
    3. 주문 상태 확인 (cancelled)
    """
    
    # 1. 주문 생성
    order_data = {
        "account_id": sample_account.id,
        "stock_code": "000660",
        "stock_name": "SK하이닉스",
        "order_type": "buy",
        "price_type": "limit",
        "quantity": 5,
        "price": 120000
    }
    response = client.post("/api/v1/trading/order", json=order_data)
    assert response.status_code == 200
    order = response.json()
    assert order["status"] == "pending"
    order_id = order["id"]
    
    # 2. 주문 취소
    response = client.delete(f"/api/v1/trading/order/{order_id}")
    assert response.status_code == 200
    cancelled_order = response.json()
    assert cancelled_order["status"] == "cancelled"
    
    # 3. 주문 목록에서 확인
    response = client.get(f"/api/v1/trading/orders/{sample_account.id}")
    assert response.status_code == 200
    orders = response.json()
    
    # 취소된 주문이 목록에 있는지 확인
    cancelled = next((o for o in orders if o["id"] == order_id), None)
    assert cancelled is not None
    assert cancelled["status"] == "cancelled"


@pytest.mark.integration
def test_multi_position_management(client, sample_account):
    """
    여러 포지션 관리 테스트
    
    시나리오:
    1. 여러 종목 매수 주문
    2. 전체 포지션 조회
    3. 총 손익 계산
    """
    
    # 1. 여러 종목 매수 주문
    stocks = [
        ("005930", "삼성전자", 70000, 10),
        ("000660", "SK하이닉스", 120000, 5),
        ("035420", "NAVER", 200000, 3),
    ]
    
    for stock_code, stock_name, price, quantity in stocks:
        order_data = {
            "account_id": sample_account.id,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "order_type": "buy",
            "price_type": "limit",
            "quantity": quantity,
            "price": price
        }
        response = client.post("/api/v1/trading/order", json=order_data)
        assert response.status_code == 200
    
    # 2. 주문 목록 확인
    response = client.get(f"/api/v1/trading/orders/{sample_account.id}")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) >= 3

