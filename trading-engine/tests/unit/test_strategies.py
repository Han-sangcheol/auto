"""
매매 전략 테스트
"""

import pytest
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.strategies.base import SignalType
from engine.strategies.ma_crossover import MACrossoverStrategy
from engine.strategies.rsi import RSIStrategy
from engine.strategies.macd import MACDStrategy


@pytest.mark.unit
class TestMACrossoverStrategy:
    """이동평균 전략 테스트"""
    
    def test_buy_signal(self):
        """매수 신호 테스트"""
        strategy = MACrossoverStrategy(short_period=5, long_period=20)
        
        # 상승 추세 데이터 (단기MA > 장기MA)
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
                  120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140]
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.BUY
    
    def test_sell_signal(self):
        """매도 신호 테스트"""
        strategy = MACrossoverStrategy(short_period=5, long_period=20)
        
        # 하락 추세 데이터 (단기MA < 장기MA)
        prices = [140, 138, 136, 134, 132, 130, 128, 126, 124, 122,
                  120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.SELL
    
    def test_hold_signal(self):
        """관망 신호 테스트"""
        strategy = MACrossoverStrategy(short_period=5, long_period=20)
        
        # 횡보 데이터
        prices = [100, 101, 100, 101, 100] * 5
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.HOLD
    
    def test_insufficient_data(self):
        """데이터 부족 시 테스트"""
        strategy = MACrossoverStrategy(short_period=5, long_period=20)
        
        # 데이터 부족 (< 20개)
        prices = [100, 101, 102]
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.HOLD


@pytest.mark.unit
class TestRSIStrategy:
    """RSI 전략 테스트"""
    
    def test_buy_signal_oversold(self):
        """과매도 매수 신호 테스트"""
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        
        # 급격한 하락 후 데이터 (RSI < 30)
        prices = [100] * 10 + [90, 85, 80, 75, 70, 65, 60, 55, 50, 45]
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.BUY
    
    def test_sell_signal_overbought(self):
        """과매수 매도 신호 테스트"""
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        
        # 급격한 상승 데이터 (RSI > 70)
        prices = [100] * 10 + [110, 115, 120, 125, 130, 135, 140, 145, 150, 155]
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.SELL
    
    def test_hold_signal(self):
        """관망 신호 테스트"""
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        
        # 정상 범위 데이터 (30 < RSI < 70)
        prices = [100 + i * 0.5 for i in range(20)]
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.HOLD


@pytest.mark.unit
class TestMACDStrategy:
    """MACD 전략 테스트"""
    
    def test_buy_signal(self):
        """매수 신호 테스트 (MACD > Signal)"""
        strategy = MACDStrategy()
        
        # 상승 추세 데이터
        prices = list(range(100, 150))
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.BUY
    
    def test_sell_signal(self):
        """매도 신호 테스트 (MACD < Signal)"""
        strategy = MACDStrategy()
        
        # 하락 추세 데이터
        prices = list(range(150, 100, -1))
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.SELL
    
    def test_insufficient_data(self):
        """데이터 부족 시 테스트"""
        strategy = MACDStrategy()
        
        # 데이터 부족 (< 35개)
        prices = [100, 101, 102]
        
        signal = strategy.generate_signal(prices)
        assert signal == SignalType.HOLD


@pytest.mark.unit
def test_signal_strength():
    """신호 강도 테스트"""
    strategy = MACrossoverStrategy(short_period=5, long_period=20)
    
    # 충분한 데이터
    prices = list(range(100, 130))
    
    strength = strategy.get_signal_strength(prices)
    assert 0.0 <= strength <= 1.0

