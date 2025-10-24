"""
기본 전략 추상 클래스

[파일 역할]
모든 매매 전략이 상속해야 하는 기본 인터페이스를 정의합니다.

[전략 추가 방법]
1. BaseStrategy를 상속
2. generate_signal() 메서드 구현 (필수)
3. get_signal_strength() 메서드 구현 (선택)
4. strategies/__init__.py에 등록
"""

from enum import Enum
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class SignalType(Enum):
    """매매 신호 타입"""
    BUY = "매수"
    SELL = "매도"
    HOLD = "관망"
    
    def __str__(self):
        return self.value


class BaseStrategy(ABC):
    """기본 전략 추상 클래스"""
    
    def __init__(self, name: str):
        """
        Args:
            name: 전략 이름
        """
        self.name = name
        self.enabled = True
    
    @abstractmethod
    def generate_signal(self, prices: List[float]) -> SignalType:
        """
        매매 신호 생성 (하위 클래스에서 필수 구현)
        
        Args:
            prices: 가격 리스트 (최신 데이터가 마지막)
        
        Returns:
            매매 신호
        """
        pass
    
    def get_signal_strength(self, prices: List[float]) -> float:
        """
        신호 강도 반환 (0.0 ~ 1.0)
        
        Args:
            prices: 가격 리스트
        
        Returns:
            신호 강도 (0.0: 매우 약함, 1.0: 매우 강함)
        """
        return 0.5  # 기본값
    
    def enable(self):
        """전략 활성화"""
        self.enabled = True
    
    def disable(self):
        """전략 비활성화"""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """전략 활성화 여부"""
        return self.enabled
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"

