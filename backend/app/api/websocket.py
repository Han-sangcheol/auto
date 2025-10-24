"""
WebSocket 실시간 통신 엔드포인트

실시간 시세, 주문 체결, 포지션 업데이트 등을 WebSocket으로 스트리밍합니다.
"""

from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio

router = APIRouter()


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 채널별 활성 연결 관리
        self.active_connections: Dict[str, Set[WebSocket]] = {
            'market': set(),      # 실시간 시세
            'orders': set(),      # 주문 체결
            'positions': set(),   # 포지션 업데이트
            'surge': set(),       # 급등주 알림
        }
    
    async def connect(self, websocket: WebSocket, channel: str):
        """클라이언트 연결"""
        await websocket.accept()
        if channel in self.active_connections:
            self.active_connections[channel].add(websocket)
            print(f"✅ Client connected to {channel} (Total: {len(self.active_connections[channel])})")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        """클라이언트 연결 해제"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            print(f"❌ Client disconnected from {channel} (Remaining: {len(self.active_connections[channel])})")
    
    async def send_to_channel(self, channel: str, message: dict):
        """특정 채널의 모든 클라이언트에게 메시지 전송"""
        if channel not in self.active_connections:
            return
        
        # 연결이 끊긴 클라이언트 제거용
        dead_connections = set()
        
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                dead_connections.add(connection)
        
        # 끊긴 연결 정리
        for connection in dead_connections:
            self.active_connections[channel].discard(connection)
    
    async def broadcast(self, message: dict):
        """모든 채널에 브로드캐스트"""
        for channel in self.active_connections:
            await self.send_to_channel(channel, message)
    
    def get_stats(self) -> dict:
        """연결 통계"""
        return {
            channel: len(connections)
            for channel, connections in self.active_connections.items()
        }


# 전역 연결 관리자
manager = ConnectionManager()


@router.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    """
    실시간 시세 WebSocket
    
    메시지 형식:
    {
        "type": "price_update",
        "data": {
            "stock_code": "005930",
            "price": 75000,
            "change_rate": 1.5,
            "volume": 1000000,
            "timestamp": "2025-10-24T09:00:00"
        }
    }
    """
    await manager.connect(websocket, 'market')
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (keep-alive용)
            data = await websocket.receive_text()
            
            # ping/pong 처리
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, 'market')


@router.websocket("/ws/orders")
async def websocket_orders(websocket: WebSocket):
    """
    주문 체결 WebSocket
    
    메시지 형식:
    {
        "type": "order_filled",
        "data": {
            "order_id": 123,
            "stock_code": "005930",
            "quantity": 10,
            "price": 75000,
            "timestamp": "2025-10-24T09:00:00"
        }
    }
    """
    await manager.connect(websocket, 'orders')
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, 'orders')


@router.websocket("/ws/positions")
async def websocket_positions(websocket: WebSocket):
    """
    포지션 업데이트 WebSocket
    
    메시지 형식:
    {
        "type": "position_update",
        "data": {
            "stock_code": "005930",
            "quantity": 10,
            "avg_price": 74000,
            "current_price": 75000,
            "profit_loss": 10000,
            "profit_loss_percent": 1.35
        }
    }
    """
    await manager.connect(websocket, 'positions')
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, 'positions')


@router.websocket("/ws/surge")
async def websocket_surge(websocket: WebSocket):
    """
    급등주 알림 WebSocket
    
    메시지 형식:
    {
        "type": "surge_detected",
        "data": {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "price": 75000,
            "change_rate": 6.5,
            "volume_ratio": 3.2,
            "timestamp": "2025-10-24T09:00:00"
        }
    }
    """
    await manager.connect(websocket, 'surge')
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, 'surge')


@router.get("/ws/stats")
async def websocket_stats():
    """WebSocket 연결 통계"""
    return {
        "status": "active",
        "connections": manager.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }


# 외부에서 사용할 수 있는 헬퍼 함수들
async def broadcast_price_update(stock_code: str, price: int, change_rate: float, volume: int):
    """실시간 시세 브로드캐스트"""
    message = {
        "type": "price_update",
        "data": {
            "stock_code": stock_code,
            "price": price,
            "change_rate": change_rate,
            "volume": volume,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    await manager.send_to_channel('market', message)


async def broadcast_order_filled(order_id: int, stock_code: str, quantity: int, price: int):
    """주문 체결 브로드캐스트"""
    message = {
        "type": "order_filled",
        "data": {
            "order_id": order_id,
            "stock_code": stock_code,
            "quantity": quantity,
            "price": price,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    await manager.send_to_channel('orders', message)


async def broadcast_position_update(position_data: dict):
    """포지션 업데이트 브로드캐스트"""
    message = {
        "type": "position_update",
        "data": position_data
    }
    await manager.send_to_channel('positions', message)


async def broadcast_surge_detected(surge_data: dict):
    """급등주 감지 브로드캐스트"""
    message = {
        "type": "surge_detected",
        "data": surge_data
    }
    await manager.send_to_channel('surge', message)

