"""
Redis Event Publisher

[파일 역할]
Trading Engine에서 발생한 이벤트를 Redis Pub/Sub을 통해 Backend로 전송
"""

import redis
import json
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger


class RedisEventPublisher:
    """Redis를 통한 이벤트 발행자"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Args:
            redis_url: Redis 서버 URL
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"✅ Redis 연결 성공: {redis_url}")
        except Exception as e:
            logger.error(f"❌ Redis 연결 실패: {e}")
            self.redis_client = None
    
    def publish_event(self, channel: str, event_type: str, data: Dict[str, Any]) -> bool:
        """
        이벤트 발행
        
        Args:
            channel: Redis 채널 (예: 'trading', 'market', 'surge')
            event_type: 이벤트 타입 (예: 'ORDER_EXECUTED', 'SURGE_DETECTED')
            data: 이벤트 데이터
        
        Returns:
            발행 성공 여부
        """
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않음")
            return False
        
        try:
            message = {
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            # Redis Pub/Sub으로 발행
            subscribers = self.redis_client.publish(channel, json.dumps(message))
            
            logger.debug(f"📤 이벤트 발행: {channel}/{event_type} (구독자: {subscribers}명)")
            return True
        
        except Exception as e:
            logger.error(f"이벤트 발행 실패: {e}")
            return False
    
    def publish_order_event(self, order_data: Dict[str, Any]) -> bool:
        """
        주문 이벤트 발행
        
        Args:
            order_data: 주문 데이터
        """
        return self.publish_event('trading:orders', 'ORDER_EVENT', order_data)
    
    def publish_position_event(self, position_data: Dict[str, Any]) -> bool:
        """
        포지션 이벤트 발행
        
        Args:
            position_data: 포지션 데이터
        """
        return self.publish_event('trading:positions', 'POSITION_EVENT', position_data)
    
    def publish_market_data(self, market_data: Dict[str, Any]) -> bool:
        """
        시세 데이터 발행
        
        Args:
            market_data: 시세 데이터
        """
        return self.publish_event('market:data', 'MARKET_DATA', market_data)
    
    def publish_surge_alert(self, surge_data: Dict[str, Any]) -> bool:
        """
        급등주 알림 발행
        
        Args:
            surge_data: 급등주 데이터
        """
        return self.publish_event('trading:surge', 'SURGE_ALERT', surge_data)
    
    def publish_trade_event(self, trade_data: Dict[str, Any]) -> bool:
        """
        거래 체결 이벤트 발행
        
        Args:
            trade_data: 거래 데이터
        """
        return self.publish_event('trading:trades', 'TRADE_EVENT', trade_data)
    
    def publish_log(self, level: str, module: str, message: str) -> bool:
        """
        로그 이벤트 발행
        
        Args:
            level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
            module: 모듈 이름
            message: 로그 메시지
        """
        log_data = {
            'level': level,
            'module': module,
            'message': message
        }
        return self.publish_event('system:logs', 'LOG_EVENT', log_data)
    
    def close(self):
        """Redis 연결 종료"""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis 연결 종료")

