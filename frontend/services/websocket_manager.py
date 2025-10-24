"""
WebSocket Manager

[파일 역할]
여러 WebSocket 채널을 관리하고 실시간 데이터를 분배
"""

import asyncio
from typing import Dict, Callable
from PySide6.QtCore import QObject, Signal, QThread
from .websocket_client import WebSocketClient


class WebSocketManager(QObject):
    """WebSocket 연결 관리자"""
    
    # Signals
    market_data_received = Signal(dict)       # 실시간 시세
    order_update_received = Signal(dict)      # 주문 업데이트
    position_update_received = Signal(dict)   # 포지션 업데이트
    surge_alert_received = Signal(dict)       # 급등주 알림
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        super().__init__()
        self.base_url = base_url
        self.clients: Dict[str, WebSocketClient] = {}
        self.running = False
        self.loop = None
        self.thread = None
    
    def start(self):
        """WebSocket 연결 시작"""
        if self.running:
            return
        
        self.running = True
        
        # 별도 스레드에서 asyncio 이벤트 루프 실행
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self._run_event_loop)
        self.thread.start()
    
    def _run_event_loop(self):
        """asyncio 이벤트 루프 실행"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # WebSocket 클라이언트 생성 및 연결
        self._setup_clients()
        
        # 이벤트 루프 실행
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
    
    def _setup_clients(self):
        """WebSocket 클라이언트 설정"""
        channels = {
            'market': self.market_data_received,
            'orders': self.order_update_received,
            'positions': self.position_update_received,
            'surge': self.surge_alert_received
        }
        
        for channel, signal in channels.items():
            client = WebSocketClient(self.base_url, channel)
            client.message_received.connect(signal.emit)
            self.clients[channel] = client
            
            # 연결 시작
            asyncio.ensure_future(client.connect(), loop=self.loop)
    
    def stop(self):
        """WebSocket 연결 중지"""
        if not self.running:
            return
        
        self.running = False
        
        # 모든 클라이언트 연결 해제
        for client in self.clients.values():
            if client.websocket:
                asyncio.ensure_future(client.disconnect(), loop=self.loop)
        
        # 이벤트 루프 중지
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # 스레드 종료
        if self.thread:
            self.thread.quit()
            self.thread.wait()
    
    def send_to_channel(self, channel: str, message: dict):
        """특정 채널로 메시지 전송"""
        if channel in self.clients:
            client = self.clients[channel]
            asyncio.ensure_future(client.send(message), loop=self.loop)

