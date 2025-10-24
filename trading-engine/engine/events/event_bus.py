"""
이벤트 버스 시스템

[파일 역할]
Trading Engine 내부 및 외부 시스템 간 이벤트 기반 통신을 제공합니다.

[주요 기능]
- 이벤트 발행 (publish)
- 이벤트 구독 (subscribe)
- 비동기 이벤트 처리
- Redis Pub/Sub 연동 (옵션)

[사용 방법]
event_bus = EventBus()
event_bus.subscribe(EventType.ORDER_FILLED, on_order_filled)
event_bus.publish(EventType.ORDER_FILLED, order_data)
"""

from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
import asyncio
from datetime import datetime
from loguru import logger


class EventType(Enum):
    """이벤트 타입"""
    
    # 주문 관련
    ORDER_PLACED = "order_placed"           # 주문 실행
    ORDER_FILLED = "order_filled"           # 주문 체결
    ORDER_CANCELLED = "order_cancelled"     # 주문 취소
    ORDER_FAILED = "order_failed"           # 주문 실패
    
    # 포지션 관련
    POSITION_OPENED = "position_opened"     # 포지션 진입
    POSITION_CLOSED = "position_closed"     # 포지션 청산
    POSITION_UPDATED = "position_updated"   # 포지션 업데이트
    
    # 시세 관련
    PRICE_UPDATE = "price_update"           # 실시간 가격 업데이트
    
    # 전략 관련
    SIGNAL_GENERATED = "signal_generated"   # 매매 신호 생성
    SURGE_DETECTED = "surge_detected"       # 급등주 감지
    
    # 리스크 관련
    STOP_LOSS_TRIGGERED = "stop_loss"       # 손절매 발동
    TAKE_PROFIT_TRIGGERED = "take_profit"   # 익절매 발동
    DAILY_LOSS_LIMIT = "daily_loss_limit"   # 일일 손실 한도 초과
    
    # 시스템 관련
    ENGINE_STARTED = "engine_started"       # 엔진 시작
    ENGINE_STOPPED = "engine_stopped"       # 엔진 중지
    ERROR_OCCURRED = "error_occurred"       # 에러 발생


class Event:
    """이벤트 클래스"""
    
    def __init__(
        self,
        event_type: EventType,
        data: Any,
        timestamp: Optional[datetime] = None,
        source: str = "trading_engine"
    ):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.source = source
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'event_type': self.event_type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }
    
    def __repr__(self):
        return f"Event({self.event_type.value}, {self.data}, {self.timestamp})"


class EventBus:
    """이벤트 버스"""
    
    def __init__(self, use_redis: bool = False):
        """
        Args:
            use_redis: Redis Pub/Sub 사용 여부
        """
        # 로컬 구독자 (메모리 기반)
        self.subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        
        # Redis 연동 (옵션)
        self.use_redis = use_redis
        self.redis_client = None
        
        # 이벤트 히스토리 (최근 100개)
        self.event_history: List[Event] = []
        self.max_history = 100
        
        # 통계
        self.event_count = defaultdict(int)
        
        logger.info(f"EventBus 초기화 (Redis: {'활성화' if use_redis else '비활성화'})")
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """
        이벤트 구독
        
        Args:
            event_type: 이벤트 타입
            handler: 핸들러 함수 (event: Event) -> None
        """
        self.subscribers[event_type].append(handler)
        logger.debug(f"구독 등록: {event_type.value} -> {handler.__name__}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """이벤트 구독 해제"""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            logger.debug(f"구독 해제: {event_type.value} -> {handler.__name__}")
    
    def publish(self, event_type: EventType, data: Any, source: str = "trading_engine"):
        """
        이벤트 발행 (동기)
        
        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
            source: 이벤트 소스
        """
        event = Event(event_type, data, source=source)
        
        # 히스토리 저장
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # 통계 업데이트
        self.event_count[event_type] += 1
        
        # 구독자에게 전달
        for handler in self.subscribers[event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"이벤트 핸들러 오류: {handler.__name__} - {e}")
        
        # Redis 발행 (옵션)
        if self.use_redis and self.redis_client:
            try:
                self._publish_to_redis(event)
            except Exception as e:
                logger.error(f"Redis 발행 실패: {e}")
        
        logger.debug(f"이벤트 발행: {event_type.value}")
    
    async def publish_async(
        self,
        event_type: EventType,
        data: Any,
        source: str = "trading_engine"
    ):
        """이벤트 발행 (비동기)"""
        event = Event(event_type, data, source=source)
        
        # 히스토리 저장
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # 통계 업데이트
        self.event_count[event_type] += 1
        
        # 비동기 구독자 호출
        tasks = []
        for handler in self.subscribers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"이벤트 핸들러 오류: {handler.__name__} - {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"이벤트 발행 (비동기): {event_type.value}")
    
    def _publish_to_redis(self, event: Event):
        """Redis에 이벤트 발행"""
        if not self.redis_client:
            return
        
        # Backend와 호환되는 채널 매핑
        channel_mapping = {
            # 주문 관련 -> trading:orders
            EventType.ORDER_PLACED: 'trading:orders',
            EventType.ORDER_FILLED: 'trading:orders',
            EventType.ORDER_CANCELLED: 'trading:orders',
            EventType.ORDER_FAILED: 'trading:orders',
            
            # 포지션 관련 -> trading:positions
            EventType.POSITION_OPENED: 'trading:positions',
            EventType.POSITION_CLOSED: 'trading:positions',
            EventType.POSITION_UPDATED: 'trading:positions',
            
            # 시세 관련 -> market:data
            EventType.PRICE_UPDATE: 'market:data',
            
            # 급등주 -> trading:surge
            EventType.SURGE_DETECTED: 'trading:surge',
            
            # 거래 체결 -> trading:trades
            EventType.SIGNAL_GENERATED: 'trading:trades',
        }
        
        # 채널 결정
        channel = channel_mapping.get(event.event_type, 'trading:events')
        
        # 메시지 준비 (JSON으로 직렬화)
        import json
        message = json.dumps(event.to_dict())
        
        # Redis Pub/Sub
        self.redis_client.publish(channel, message)
        logger.debug(f"Redis 발행: {channel} - {event.event_type.value}")
    
    def connect_redis(self, redis_url: str = "redis://localhost:6379/0"):
        """Redis 연결"""
        try:
            import redis
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.success(f"Redis 연결 성공: {redis_url}")
            self.use_redis = True
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            self.use_redis = False
    
    def get_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """
        이벤트 히스토리 조회
        
        Args:
            event_type: 특정 이벤트 타입만 필터링 (선택)
        
        Returns:
            이벤트 목록
        """
        if event_type is None:
            return self.event_history
        
        return [e for e in self.event_history if e.event_type == event_type]
    
    def get_statistics(self) -> dict:
        """통계 정보 반환"""
        return {
            'total_events': sum(self.event_count.values()),
            'event_count': dict(self.event_count),
            'history_size': len(self.event_history),
            'subscribers_count': {
                event_type.value: len(handlers)
                for event_type, handlers in self.subscribers.items()
            }
        }
    
    def clear_history(self):
        """히스토리 초기화"""
        self.event_history.clear()
        logger.info("이벤트 히스토리 초기화")


# 전역 이벤트 버스 인스턴스
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """전역 이벤트 버스 인스턴스 가져오기"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus

