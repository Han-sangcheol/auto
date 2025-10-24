"""
기술적 지표 계산 모듈

[파일 역할]
매매 전략에 필요한 기술적 지표(Technical Indicators)를 계산합니다.

[구현된 지표]
- SMA (Simple Moving Average): 단순 이동평균
- EMA (Exponential Moving Average): 지수 이동평균
- RSI (Relative Strength Index): 상대강도지수
- MACD (Moving Average Convergence Divergence): 이동평균수렴확산
- Bollinger Bands: 볼린저 밴드

[사용 방법]
from indicators.technical import calculate_sma, calculate_rsi
sma_5 = calculate_sma(prices, 5)
rsi = calculate_rsi(prices, 14)
"""

import numpy as np
from typing import List, Tuple, Optional


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """
    단순 이동평균(SMA) 계산
    
    Args:
        prices: 가격 리스트 (최신 데이터가 마지막)
        period: 이동평균 기간
    
    Returns:
        SMA 값 또는 None (데이터 부족시)
    """
    if len(prices) < period:
        return None
    
    return np.mean(prices[-period:])


def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """
    지수 이동평균(EMA) 계산
    
    Args:
        prices: 가격 리스트
        period: 이동평균 기간
    
    Returns:
        EMA 값 또는 None (데이터 부족시)
    """
    if len(prices) < period:
        return None
    
    prices_array = np.array(prices)
    multiplier = 2 / (period + 1)
    ema = prices_array[0]
    
    for price in prices_array[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return float(ema)


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    RSI (Relative Strength Index) 계산
    
    Args:
        prices: 가격 리스트
        period: RSI 계산 기간 (기본 14일)
    
    Returns:
        RSI 값 (0-100) 또는 None (데이터 부족시)
    """
    if len(prices) < period + 1:
        return None
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Optional[Tuple[float, float, float]]:
    """
    MACD (Moving Average Convergence Divergence) 계산
    
    Args:
        prices: 가격 리스트
        fast: 빠른 EMA 기간 (기본 12)
        slow: 느린 EMA 기간 (기본 26)
        signal: 시그널선 기간 (기본 9)
    
    Returns:
        (MACD선, 시그널선, 히스토그램) 튜플 또는 None (데이터 부족시)
    """
    if len(prices) < slow + signal:
        return None
    
    prices_array = np.array(prices)
    
    def calc_ema_array(data, span):
        multiplier = 2 / (span + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        return ema
    
    ema_fast = calc_ema_array(prices_array, fast)
    ema_slow = calc_ema_array(prices_array, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema_array(macd_line, signal)
    histogram = macd_line - signal_line
    
    return (
        float(macd_line[-1]),
        float(signal_line[-1]),
        float(histogram[-1])
    )


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Optional[Tuple[float, float, float]]:
    """
    볼린저 밴드 계산
    
    Args:
        prices: 가격 리스트
        period: 이동평균 기간 (기본 20)
        std_dev: 표준편차 배수 (기본 2.0)
    
    Returns:
        (상단밴드, 중심선, 하단밴드) 튜플 또는 None (데이터 부족시)
    """
    if len(prices) < period:
        return None
    
    middle_band = calculate_sma(prices, period)
    std = np.std(prices[-period:])
    
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)
    
    return (upper_band, middle_band, lower_band)

