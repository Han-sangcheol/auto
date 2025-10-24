"""
Redis Event Subscriber

Backend에서 Trading Engine의 이벤트를 구독하고 WebSocket으로 브로드캐스트
"""

import redis
import json
import asyncio
from typing import Callable, Dict
from loguru import logger


class RedisEventSubscriber:
    """Redis 이벤트 구독자"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Args:
            redis_url: Redis 서버 URL
        """
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None
        self.handlers: Dict[str, Callable] = {}
        self.running = False
    
    def connect(self):
        """Redis 연결"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            logger.info(f"✅ Redis 구독자 연결 성공: {self.redis_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Redis 연결 실패: {e}")
            return False
    
    def subscribe(self, channel: str, handler: Callable):
        """
        채널 구독
        
        Args:
            channel: 구독할 채널 (예: 'trading:orders')
            handler: 메시지 처리 핸들러
        """
        if not self.pubsub:
            logger.error("Redis가 연결되지 않음")
            return
        
        try:
            self.pubsub.subscribe(channel)
            self.handlers[channel] = handler
            logger.info(f"📥 채널 구독: {channel}")
        except Exception as e:
            logger.error(f"채널 구독 실패 ({channel}): {e}")
    
    async def start_listening(self):
        """
        메시지 수신 시작 (비동기)
        """
        if not self.pubsub:
            logger.error("Redis가 연결되지 않음")
            return
        
        self.running = True
        logger.info("🎧 Redis 이벤트 수신 시작...")
        
        try:
            while self.running:
                # 메시지 수신 (블로킹)
                message = self.pubsub.get_message()
                
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    # 핸들러 호출
                    if channel in self.handlers:
                        try:
                            # JSON 파싱
                            event_data = json.loads(data)
                            
                            # 핸들러 실행
                            handler = self.handlers[channel]
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event_data)
                            else:
                                handler(event_data)
                        
                        except json.JSONDecodeError:
                            logger.error(f"JSON 파싱 실패: {data}")
                        except Exception as e:
                            logger.error(f"핸들러 실행 오류: {e}")
                
                # CPU 부하 방지
                await asyncio.sleep(0.01)
        
        except Exception as e:
            logger.error(f"메시지 수신 오류: {e}")
        
        finally:
            logger.info("Redis 이벤트 수신 종료")
    
    def stop(self):
        """메시지 수신 중지"""
        self.running = False
        
        if self.pubsub:
            self.pubsub.unsubscribe()
            self.pubsub.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("Redis 구독자 종료")

