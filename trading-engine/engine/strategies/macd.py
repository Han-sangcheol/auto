"""
MACD 전략

[전략 개요]
MACD(Moving Average Convergence Divergence)를 이용한 모멘텀 전략

[매수 신호]
- MACD선이 시그널선을 상향 돌파

[매도 신호]
- MACD선이 시그널선을 하향 돌파
"""

from typing import List
from .base import BaseStrategy, SignalType
from ..indicators.technical import calculate_macd


class MACDStrategy(BaseStrategy):
    """MACD 전략"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__("MACD")
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def generate_signal(self, prices: List[float]) -> SignalType:
        """
        MACD 기반 신호 생성
        
        - MACD선이 시그널선을 상향 돌파 → 매수
        - MACD선이 시그널선을 하향 돌파 → 매도
        """
        if len(prices) < self.slow + self.signal + 1:
            return SignalType.HOLD
        
        # 현재 MACD
        macd_result = calculate_macd(prices, self.fast, self.slow, self.signal)
        if macd_result is None:
            return SignalType.HOLD
        
        macd, signal_line, histogram = macd_result
        
        # 이전 MACD
        macd_result_prev = calculate_macd(prices[:-1], self.fast, self.slow, self.signal)
        if macd_result_prev is None:
            return SignalType.HOLD
        
        macd_prev, signal_prev, histogram_prev = macd_result_prev
        
        # MACD선이 시그널선을 상향 돌파
        if histogram > 0 and histogram_prev <= 0:
            return SignalType.BUY
        
        # MACD선이 시그널선을 하향 돌파
        elif histogram < 0 and histogram_prev >= 0:
            return SignalType.SELL
        
        return SignalType.HOLD
    
    def get_signal_strength(self, prices: List[float]) -> float:
        """신호 강도 계산 (히스토그램 크기 기반)"""
        macd_result = calculate_macd(prices, self.fast, self.slow, self.signal)
        
        if macd_result is None:
            return 0.0
        
        _, _, histogram = macd_result
        
        # 히스토그램의 절대값이 클수록 강한 신호
        strength = min(abs(histogram) / 5.0, 1.0)
        
        return strength

