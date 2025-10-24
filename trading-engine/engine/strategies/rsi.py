"""
RSI 전략

[전략 개요]
상대강도지수(RSI)를 이용한 과매수/과매도 전략

[매수 신호]
- RSI < 30 (과매도 구간) 에서 반등

[매도 신호]
- RSI > 70 (과매수 구간) 에서 하락
"""

from typing import List
from .base import BaseStrategy, SignalType
from ..indicators.technical import calculate_rsi


class RSIStrategy(BaseStrategy):
    """RSI 기반 전략"""
    
    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0
    ):
        super().__init__("RSI")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, prices: List[float]) -> SignalType:
        """
        RSI 기반 신호 생성
        
        - RSI < 30 (과매도) 에서 반등 → 매수
        - RSI > 70 (과매수) 에서 하락 → 매도
        """
        if len(prices) < self.period + 2:
            return SignalType.HOLD
        
        rsi = calculate_rsi(prices, self.period)
        rsi_prev = calculate_rsi(prices[:-1], self.period)
        
        if rsi is None or rsi_prev is None:
            return SignalType.HOLD
        
        # 과매도 구간에서 반등 시 매수
        if rsi < self.oversold and rsi > rsi_prev:
            return SignalType.BUY
        
        # 과매수 구간에서 하락 시 매도
        elif rsi > self.overbought and rsi < rsi_prev:
            return SignalType.SELL
        
        return SignalType.HOLD
    
    def get_signal_strength(self, prices: List[float]) -> float:
        """신호 강도 계산 (RSI 극단값 기반)"""
        rsi = calculate_rsi(prices, self.period)
        
        if rsi is None:
            return 0.0
        
        # RSI가 극단값에 가까울수록 강한 신호
        if rsi < self.oversold:
            strength = 1.0 - (rsi / self.oversold)
        elif rsi > self.overbought:
            strength = (rsi - self.overbought) / (100 - self.overbought)
        else:
            strength = 0.0
        
        return min(strength, 1.0)

