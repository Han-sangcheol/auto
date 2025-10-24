"""
WebSocket 클라이언트

실시간 데이터 스트리밍을 처리합니다.
"""

import asyncio
import websockets
import json
from typing import Callable, Optional
from PySide6.QtCore import QObject, Signal


class WebSocketClient(QObject):
    """WebSocket 클라이언트"""
    
    # Qt Signals
    message_received = Signal(dict)
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, url: str, channel: str):
        super().__init__()
        self.url = f"{url}/ws/{channel}"
        self.channel = channel
        self.websocket = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
    
    async def connect(self):
        """WebSocket 연결"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.running = True
            self.reconnect_attempts = 0
            self.connected.emit()
            print(f"✅ Connected to {self.channel}")
            
            # 메시지 수신 시작
            await self.receive_messages()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            print(f"❌ Connection error: {e}")
            
            # 재연결 시도
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                await asyncio.sleep(2 ** self.reconnect_attempts)  # 지수 백오프
                await self.connect()
    
    async def receive_messages(self):
        """메시지 수신"""
        try:
            while self.running and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                self.message_received.emit(data)
        
        except websockets.ConnectionClosed:
            self.disconnected.emit()
            print(f"Connection closed: {self.channel}")
            
            # 재연결 시도
            if self.running:
                await self.connect()
        
        except Exception as e:
            self.error_occurred.emit(str(e))
            print(f"Receive error: {e}")
    
    async def send(self, message: dict):
        """메시지 전송"""
        if self.websocket and self.running:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                self.error_occurred.emit(str(e))
    
    async def disconnect(self):
        """연결 해제"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.disconnected.emit()
    
    async def ping(self):
        """Ping (Keep-alive)"""
        while self.running:
            if self.websocket:
                try:
                    await self.websocket.send("ping")
                    await asyncio.sleep(30)  # 30초마다 ping
                except Exception as e:
                    print(f"Ping error: {e}")
                    break

