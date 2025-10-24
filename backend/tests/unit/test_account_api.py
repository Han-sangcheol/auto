"""
계좌 API 테스트
"""

import pytest


@pytest.mark.unit
def test_get_accounts(client, sample_account):
    """계좌 목록 조회 테스트"""
    response = client.get("/api/v1/account/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["account_number"] == "8888888888"


@pytest.mark.unit
def test_get_account_balance(client, sample_account):
    """계좌 잔고 조회 테스트"""
    response = client.get(f"/api/v1/account/{sample_account.id}/balance")
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_balance"] == 10000000
    assert data["initial_balance"] == 10000000


@pytest.mark.unit
def test_get_positions(client, sample_account, sample_position):
    """포지션 목록 조회 테스트"""
    response = client.get(f"/api/v1/account/{sample_account.id}/positions")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["stock_code"] == "005930"
    assert data[0]["quantity"] == 10


@pytest.mark.unit
def test_get_account_not_found(client):
    """존재하지 않는 계좌 조회 테스트"""
    response = client.get("/api/v1/account/9999/balance")
    
    assert response.status_code == 404

