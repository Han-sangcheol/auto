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
- Stochastic: 스토캐스틱

[사용 방법]
from indicators import calculate_sma, calculate_rsi
sma_5 = calculate_sma(prices, 5)
rsi = calculate_rsi(prices, 14)

[참고]
- 모든 함수는 순수 함수 (side effect 없음)
- prices는 시간 순서대로 정렬된 리스트
- 데이터 부족 시 None 반환
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
    
    # numpy를 사용한 EMA 계산
    prices_array = np.array(prices)
    multiplier = 2 / (period + 1)
    ema = prices_array[0]  # 첫 값으로 초기화
    
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
    
    # 가격 변화량 계산
    deltas = np.diff(prices)
    
    # 상승/하락 분리
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 평균 상승/하락 계산
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    # 0으로 나누기 방지
    if avg_loss == 0:
        return 100.0
    
    # RSI 계산
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
    
    # numpy 배열로 변환
    prices_array = np.array(prices)
    
    # EMA 계산 함수 (내부 헬퍼)
    def calc_ema_array(data, span):
        multiplier = 2 / (span + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        return ema
    
    # EMA 계산
    ema_fast = calc_ema_array(prices_array, fast)
    ema_slow = calc_ema_array(prices_array, slow)
    
    # MACD선 계산
    macd_line = ema_fast - ema_slow
    
    # 시그널선 계산
    signal_line = calc_ema_array(macd_line, signal)
    
    # 히스토그램 계산
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
    
    # 중심선 (SMA)
    middle_band = calculate_sma(prices, period)
    
    # 표준편차 계산
    std = np.std(prices[-period:])
    
    # 상단/하단 밴드
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)
    
    return (upper_band, middle_band, lower_band)


def calculate_all_indicators(prices: List[float], config) -> dict:
    """
    모든 지표를 한번에 계산
    
    Args:
        prices: 가격 리스트
        config: Config 객체
    
    Returns:
        지표 딕셔너리
    """
    indicators = {}
    
    # 이동평균선
    indicators['sma_short'] = calculate_sma(prices, config.MA_SHORT_PERIOD)
    indicators['sma_long'] = calculate_sma(prices, config.MA_LONG_PERIOD)
    
    # RSI
    indicators['rsi'] = calculate_rsi(prices, config.RSI_PERIOD)
    
    # MACD
    macd_result = calculate_macd(
        prices,
        config.MACD_FAST,
        config.MACD_SLOW,
        config.MACD_SIGNAL
    )
    if macd_result:
        indicators['macd'], indicators['macd_signal'], indicators['macd_hist'] = macd_result
    else:
        indicators['macd'] = None
        indicators['macd_signal'] = None
        indicators['macd_hist'] = None
    
    # 볼린저 밴드
    bb_result = calculate_bollinger_bands(prices)
    if bb_result:
        indicators['bb_upper'], indicators['bb_middle'], indicators['bb_lower'] = bb_result
    else:
        indicators['bb_upper'] = None
        indicators['bb_middle'] = None
        indicators['bb_lower'] = None
    
    return indicators


# 테스트 코드
if __name__ == "__main__":
    # 테스트 데이터 (삼성전자 주가 예시)
    test_prices = [
        70000, 70500, 71000, 70800, 71500,
        72000, 72500, 71800, 72200, 73000,
        73500, 73200, 74000, 74500, 75000,
        74800, 75500, 76000, 75500, 76500,
        77000, 76800, 77500, 78000, 77500,
        78500, 79000, 78500, 79500, 80000
    ]
    
    print("기술적 지표 테스트")
    print("=" * 60)
    
    # SMA 테스트
    sma_5 = calculate_sma(test_prices, 5)
    sma_20 = calculate_sma(test_prices, 20)
    print(f"SMA(5):  {sma_5:,.0f}원" if sma_5 else "SMA(5): 데이터 부족")
    print(f"SMA(20): {sma_20:,.0f}원" if sma_20 else "SMA(20): 데이터 부족")
    
    # EMA 테스트
    ema_12 = calculate_ema(test_prices, 12)
    print(f"EMA(12): {ema_12:,.0f}원" if ema_12 else "EMA(12): 데이터 부족")
    
    # RSI 테스트
    rsi = calculate_rsi(test_prices, 14)
    print(f"RSI(14): {rsi:.2f}" if rsi else "RSI(14): 데이터 부족")
    if rsi:
        if rsi < 30:
            print("  ⚠️  과매도 구간")
        elif rsi > 70:
            print("  ⚠️  과매수 구간")
        else:
            print("  ✓ 정상 구간")
    
    # MACD 테스트
    macd_result = calculate_macd(test_prices)
    if macd_result:
        macd, signal, hist = macd_result
        print(f"MACD: {macd:.2f}")
        print(f"Signal: {signal:.2f}")
        print(f"Histogram: {hist:.2f}")
        if hist > 0:
            print("  📈 상승 추세")
        else:
            print("  📉 하락 추세")
    else:
        print("MACD: 데이터 부족")
    
    # 볼린저 밴드 테스트
    bb_result = calculate_bollinger_bands(test_prices, 20)
    if bb_result:
        upper, middle, lower = bb_result
        current_price = test_prices[-1]
        print(f"볼린저 밴드:")
        print(f"  상단: {upper:,.0f}원")
        print(f"  중심: {middle:,.0f}원")
        print(f"  하단: {lower:,.0f}원")
        print(f"  현재가: {current_price:,.0f}원")
        
        if current_price > upper:
            print("  ⚠️  상단 밴드 돌파 (과매수)")
        elif current_price < lower:
            print("  ⚠️  하단 밴드 이탈 (과매도)")
    else:
        print("볼린저 밴드: 데이터 부족")
    
    print("=" * 60)

