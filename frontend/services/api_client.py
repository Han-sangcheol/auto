"""
Backend API 클라이언트

REST API 호출을 담당합니다.
"""

import requests
from typing import Optional, List, Dict
from datetime import datetime


class APIClient:
    """Backend API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def check_health(self) -> Optional[dict]:
        """Backend 헬스 체크"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=3)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Health check failed: {e}")
            return None
    
    # 계좌 API
    def get_accounts(self, user_id: int = 1) -> List[dict]:
        """계좌 목록 조회"""
        response = self.session.get(f"{self.api_v1}/account/")
        response.raise_for_status()
        return response.json()
    
    def get_account_balance(self, account_id: int) -> dict:
        """계좌 잔고 조회"""
        response = self.session.get(f"{self.api_v1}/account/{account_id}/balance")
        response.raise_for_status()
        return response.json()
    
    def get_positions(self, account_id: int) -> List[dict]:
        """포지션 목록 조회"""
        response = self.session.get(f"{self.api_v1}/account/{account_id}/positions")
        response.raise_for_status()
        return response.json()
    
    # 매매 API
    def create_order(
        self,
        account_id: int,
        stock_code: str,
        stock_name: str,
        order_type: str,
        price_type: str,
        quantity: int,
        price: Optional[int] = None
    ) -> dict:
        """주문 실행"""
        data = {
            "account_id": account_id,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "order_type": order_type,
            "price_type": price_type,
            "quantity": quantity,
            "price": price
        }
        response = self.session.post(f"{self.api_v1}/trading/order", json=data)
        response.raise_for_status()
        return response.json()
    
    def cancel_order(self, order_id: int) -> dict:
        """주문 취소"""
        response = self.session.delete(f"{self.api_v1}/trading/order/{order_id}")
        response.raise_for_status()
        return response.json()
    
    def get_orders(self, account_id: int) -> List[dict]:
        """주문 목록 조회"""
        response = self.session.get(f"{self.api_v1}/trading/orders/{account_id}")
        response.raise_for_status()
        return response.json()
    
    def get_trades(self, account_id: int) -> List[dict]:
        """거래 내역 조회"""
        response = self.session.get(f"{self.api_v1}/trading/trades/{account_id}")
        response.raise_for_status()
        return response.json()
    
    # 시세 API
    def get_stock_info(self, stock_code: str) -> dict:
        """종목 정보 조회"""
        response = self.session.get(f"{self.api_v1}/market/stocks/{stock_code}")
        response.raise_for_status()
        return response.json()
    
    def get_chart_data(self, stock_code: str, days: int = 7) -> dict:
        """차트 데이터 조회"""
        response = self.session.get(
            f"{self.api_v1}/market/stocks/{stock_code}/chart",
            params={"days": days}
        )
        response.raise_for_status()
        return response.json()
    
    def get_surge_stocks(self, limit: int = 20) -> dict:
        """급등주 목록 조회"""
        response = self.session.get(
            f"{self.api_v1}/market/surge",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    # 로그 API
    def get_logs(self, limit: int = 1000, level: Optional[str] = None) -> List[dict]:
        """로그 조회"""
        params = {"limit": limit}
        if level:
            params["level"] = level
        
        response = self.session.get(f"{self.api_v1}/logs", params=params)
        response.raise_for_status()
        return response.json()
    
    # Trading Engine 제어 API
    def get_engine_status(self) -> dict:
        """Engine 상태 조회"""
        response = self.session.get(f"{self.api_v1}/engine/status")
        response.raise_for_status()
        return response.json()
    
    def start_engine(self, config: Optional[dict] = None) -> dict:
        """Engine 시작"""
        response = self.session.post(f"{self.api_v1}/engine/start", json=config or {})
        response.raise_for_status()
        return response.json()
    
    def stop_engine(self) -> dict:
        """Engine 중지"""
        response = self.session.post(f"{self.api_v1}/engine/stop")
        response.raise_for_status()
        return response.json()
    
    def restart_engine(self, config: Optional[dict] = None) -> dict:
        """Engine 재시작"""
        response = self.session.post(f"{self.api_v1}/engine/restart", json=config or {})
        response.raise_for_status()
        return response.json()

