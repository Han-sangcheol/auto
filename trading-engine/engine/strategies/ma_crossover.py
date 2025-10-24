"""
이동평균선 크로스오버 전략

[전략 개요]
단기 이동평균선과 장기 이동평균선의 교차를 이용한 추세 추종 전략

[매수 신호]
- 골든크로스: 단기 MA > 장기 MA (상향 돌파)

[매도 신호]
- 데드크로스: 단기 MA < 장기 MA (하향 돌파)
"""

from typing import List
from .base import BaseStrategy, SignalType
from ..indicators.technical import calculate_sma


class MACrossoverStrategy(BaseStrategy):
    """이동평균선 크로스오버 전략"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        super().__init__("이동평균선 크로스오버")
        self.short_period = short_period
        self.long_period = long_period
        self.prev_signal = SignalType.HOLD
    
    def generate_signal(self, prices: List[float]) -> SignalType:
        """
        이동평균선 크로스오버 신호 생성
        
        - 단기 이평선이 장기 이평선을 상향 돌파 → 매수 (골든크로스)
        - 단기 이평선이 장기 이평선을 하향 돌파 → 매도 (데드크로스)
        """
        if len(prices) < self.long_period + 1:
            return SignalType.HOLD
        
        # 현재 이동평균선
        sma_short = calculate_sma(prices, self.short_period)
        sma_long = calculate_sma(prices, self.long_period)
        
        # 이전 이동평균선
        sma_short_prev = calculate_sma(prices[:-1], self.short_period)
        sma_long_prev = calculate_sma(prices[:-1], self.long_period)
        
        if None in [sma_short, sma_long, sma_short_prev, sma_long_prev]:
            return SignalType.HOLD
        
        # 골든크로스: 단기선이 장기선을 상향 돌파
        if sma_short > sma_long and sma_short_prev <= sma_long_prev:
            return SignalType.BUY
        
        # 데드크로스: 단기선이 장기선을 하향 돌파
        elif sma_short < sma_long and sma_short_prev >= sma_long_prev:
            return SignalType.SELL
        
        return SignalType.HOLD
    
    def get_signal_strength(self, prices: List[float]) -> float:
        """신호 강도 계산 (이평선 간 거리 기반)"""
        sma_short = calculate_sma(prices, self.short_period)
        sma_long = calculate_sma(prices, self.long_period)
        
        if sma_short is None or sma_long is None:
            return 0.0
        
        # 이평선 간 거리 비율
        distance = abs(sma_short - sma_long) / sma_long * 100
        
        # 0~5% 거리를 0.0~1.0으로 매핑
        strength = min(distance / 5.0, 1.0)
        
        return strength

