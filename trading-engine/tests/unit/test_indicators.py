"""
기술적 지표 테스트
"""

import pytest
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.indicators.technical import (
    calculate_sma, calculate_ema, calculate_rsi,
    calculate_macd, calculate_bollinger_bands
)


@pytest.mark.unit
class TestSMA:
    """SMA (단순 이동평균) 테스트"""
    
    def test_calculate_sma(self):
        """SMA 계산 테스트"""
        prices = [100, 102, 104, 106, 108]
        sma = calculate_sma(prices, period=5)
        
        assert sma is not None
        assert sma == 104.0  # (100+102+104+106+108)/5
    
    def test_sma_insufficient_data(self):
        """데이터 부족 시 테스트"""
        prices = [100, 102, 104]
        sma = calculate_sma(prices, period=5)
        
        assert sma is None
    
    def test_sma_different_periods(self):
        """다양한 기간 테스트"""
        prices = list(range(100, 120))
        
        sma_5 = calculate_sma(prices, period=5)
        sma_10 = calculate_sma(prices, period=10)
        sma_20 = calculate_sma(prices, period=20)
        
        assert sma_5 is not None
        assert sma_10 is not None
        assert sma_20 is None  # 데이터 부족


@pytest.mark.unit
class TestEMA:
    """EMA (지수 이동평균) 테스트"""
    
    def test_calculate_ema(self):
        """EMA 계산 테스트"""
        prices = [100, 102, 104, 106, 108, 110]
        ema = calculate_ema(prices, period=5)
        
        assert ema is not None
        assert ema > 100
        assert ema < 110
    
    def test_ema_insufficient_data(self):
        """데이터 부족 시 테스트"""
        prices = [100, 102]
        ema = calculate_ema(prices, period=5)
        
        assert ema is None


@pytest.mark.unit
class TestRSI:
    """RSI (상대강도지수) 테스트"""
    
    def test_calculate_rsi_oversold(self):
        """과매도 RSI 테스트"""
        # 급격한 하락
        prices = [100] * 5 + list(range(100, 70, -2))
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is not None
        assert rsi < 40  # 과매도 구간
    
    def test_calculate_rsi_overbought(self):
        """과매수 RSI 테스트"""
        # 급격한 상승
        prices = [100] * 5 + list(range(100, 130, 2))
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is not None
        assert rsi > 60  # 과매수 구간
    
    def test_rsi_insufficient_data(self):
        """데이터 부족 시 테스트"""
        prices = [100, 102, 104]
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is None
    
    def test_rsi_range(self):
        """RSI 범위 테스트 (0 ~ 100)"""
        prices = list(range(100, 150))
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is not None
        assert 0 <= rsi <= 100


@pytest.mark.unit
class TestMACD:
    """MACD 테스트"""
    
    def test_calculate_macd(self):
        """MACD 계산 테스트"""
        prices = list(range(100, 150))
        macd, signal, histogram = calculate_macd(prices)
        
        assert macd is not None
        assert signal is not None
        assert histogram is not None
    
    def test_macd_insufficient_data(self):
        """데이터 부족 시 테스트"""
        prices = [100, 102, 104]
        macd, signal, histogram = calculate_macd(prices)
        
        assert macd is None
        assert signal is None
        assert histogram is None
    
    def test_macd_histogram(self):
        """히스토그램 = MACD - Signal"""
        prices = list(range(100, 150))
        macd, signal, histogram = calculate_macd(prices)
        
        if macd and signal:
            assert abs(histogram - (macd - signal)) < 0.01


@pytest.mark.unit
class TestBollingerBands:
    """볼린저 밴드 테스트"""
    
    def test_calculate_bollinger_bands(self):
        """볼린저 밴드 계산 테스트"""
        prices = [100 + i * 0.5 for i in range(30)]
        upper, middle, lower = calculate_bollinger_bands(prices, period=20)
        
        assert upper is not None
        assert middle is not None
        assert lower is not None
        assert upper > middle > lower
    
    def test_bollinger_insufficient_data(self):
        """데이터 부족 시 테스트"""
        prices = [100, 102, 104]
        upper, middle, lower = calculate_bollinger_bands(prices, period=20)
        
        assert upper is None
        assert middle is None
        assert lower is None
    
    def test_bollinger_relationship(self):
        """Upper >= Middle >= Lower"""
        prices = list(range(100, 130))
        upper, middle, lower = calculate_bollinger_bands(prices, period=20)
        
        assert upper >= middle
        assert middle >= lower

