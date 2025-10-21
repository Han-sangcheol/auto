"""
매매 전략 모듈

[파일 역할]
다양한 매매 전략을 구현하고 매수/매도/관망 신호를 생성합니다.

[구현된 전략]
1. MovingAverageCrossStrategy: 이동평균선 크로스오버
   - 골든크로스: 단기 MA > 장기 MA → 매수
   - 데드크로스: 단기 MA < 장기 MA → 매도

2. RSIStrategy: RSI 기반 과매수/과매도
   - RSI < 30: 과매도 → 매수
   - RSI > 70: 과매수 → 매도

3. MACDStrategy: MACD 크로스오버
   - MACD > Signal: 상승 모멘텀 → 매수
   - MACD < Signal: 하락 모멘텀 → 매도

4. MultiStrategy: 다중 전략 통합 (합의 알고리즘)
   - 여러 전략의 신호를 종합하여 최종 결정
   - 2개 이상 전략 동의 시 실행 (기본값)

[사용 방법]
strategy = MovingAverageCrossStrategy()
signal = strategy.generate_signal(prices)

[전략 추가 방법]
BaseStrategy를 상속하여 generate_signal() 메서드 구현
"""

from enum import Enum
from typing import List, Dict, Optional
from indicators import calculate_sma, calculate_rsi, calculate_macd
from logger import log
from config import Config


class SignalType(Enum):
    """매매 신호 타입"""
    BUY = "매수"
    SELL = "매도"
    HOLD = "관망"


class BaseStrategy:
    """기본 전략 클래스"""
    
    def __init__(self, name: str):
        self.name = name
    
    def generate_signal(self, prices: List[float]) -> SignalType:
        """
        매매 신호 생성 (하위 클래스에서 구현)
        
        Args:
            prices: 가격 리스트
        
        Returns:
            매매 신호
        """
        raise NotImplementedError("하위 클래스에서 구현해야 합니다.")
    
    def get_signal_strength(self, prices: List[float]) -> float:
        """
        신호 강도 반환 (0.0 ~ 1.0)
        
        Args:
            prices: 가격 리스트
        
        Returns:
            신호 강도
        """
        return 0.5  # 기본값


class MACrossoverStrategy(BaseStrategy):
    """이동평균선 크로스오버 전략"""
    
    def __init__(self, short_period: int, long_period: int):
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
        
        # 이전 이동평균선 (크로스오버 확인용)
        sma_short_prev = calculate_sma(prices[:-1], self.short_period)
        sma_long_prev = calculate_sma(prices[:-1], self.long_period)
        
        if sma_short is None or sma_long is None:
            return SignalType.HOLD
        
        if sma_short_prev is None or sma_long_prev is None:
            return SignalType.HOLD
        
        # 골든크로스: 단기선이 장기선을 상향 돌파
        if sma_short > sma_long and sma_short_prev <= sma_long_prev:
            log.debug(
                f"[{self.name}] 골든크로스 발생: "
                f"단기 {sma_short:.0f} > 장기 {sma_long:.0f}"
            )
            return SignalType.BUY
        
        # 데드크로스: 단기선이 장기선을 하향 돌파
        elif sma_short < sma_long and sma_short_prev >= sma_long_prev:
            log.debug(
                f"[{self.name}] 데드크로스 발생: "
                f"단기 {sma_short:.0f} < 장기 {sma_long:.0f}"
            )
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


class RSIStrategy(BaseStrategy):
    """RSI 기반 전략"""
    
    def __init__(self, period: int, oversold: float, overbought: float):
        super().__init__("RSI")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, prices: List[float]) -> SignalType:
        """
        RSI 기반 신호 생성
        
        - RSI < 30 (과매도) → 매수 고려
        - RSI > 70 (과매수) → 매도 고려
        """
        if len(prices) < self.period + 2:
            return SignalType.HOLD
        
        rsi = calculate_rsi(prices, self.period)
        rsi_prev = calculate_rsi(prices[:-1], self.period)
        
        if rsi is None or rsi_prev is None:
            return SignalType.HOLD
        
        # 과매도 구간에서 반등 시 매수
        if rsi < self.oversold and rsi > rsi_prev:
            log.debug(f"[{self.name}] 과매도 구간 반등: RSI {rsi:.2f}")
            return SignalType.BUY
        
        # 과매수 구간에서 하락 시 매도
        elif rsi > self.overbought and rsi < rsi_prev:
            log.debug(f"[{self.name}] 과매수 구간 하락: RSI {rsi:.2f}")
            return SignalType.SELL
        
        return SignalType.HOLD
    
    def get_signal_strength(self, prices: List[float]) -> float:
        """신호 강도 계산 (RSI 극단값 기반)"""
        rsi = calculate_rsi(prices, self.period)
        
        if rsi is None:
            return 0.0
        
        # RSI가 극단값에 가까울수록 강한 신호
        if rsi < self.oversold:
            # 0~30 구간을 1.0~0.0으로 매핑
            strength = 1.0 - (rsi / self.oversold)
        elif rsi > self.overbought:
            # 70~100 구간을 0.0~1.0으로 매핑
            strength = (rsi - self.overbought) / (100 - self.overbought)
        else:
            strength = 0.0
        
        return min(strength, 1.0)


class MACDStrategy(BaseStrategy):
    """MACD 전략"""
    
    def __init__(self, fast: int, slow: int, signal: int):
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
            log.debug(f"[{self.name}] MACD 골든크로스: 히스토그램 {histogram:.2f}")
            return SignalType.BUY
        
        # MACD선이 시그널선을 하향 돌파
        elif histogram < 0 and histogram_prev >= 0:
            log.debug(f"[{self.name}] MACD 데드크로스: 히스토그램 {histogram:.2f}")
            return SignalType.SELL
        
        return SignalType.HOLD
    
    def get_signal_strength(self, prices: List[float]) -> float:
        """신호 강도 계산 (히스토그램 크기 기반)"""
        macd_result = calculate_macd(prices, self.fast, self.slow, self.signal)
        
        if macd_result is None:
            return 0.0
        
        _, _, histogram = macd_result
        
        # 히스토그램의 절대값이 클수록 강한 신호
        # 일반적으로 -5 ~ +5 범위
        strength = min(abs(histogram) / 5.0, 1.0)
        
        return strength


class MultiStrategy:
    """
    여러 전략을 조합한 통합 전략
    
    합의 알고리즘: 여러 전략의 신호를 종합하여 최종 신호 결정
    """
    
    def __init__(self, strategies: List[BaseStrategy], min_signal_strength: int = 2):
        self.strategies = strategies
        self.min_signal_strength = min_signal_strength
        log.info(
            f"통합 전략 초기화: {len(strategies)}개 전략, "
            f"최소 신호 강도 {min_signal_strength}"
        )
    
    def generate_signal(self, prices: List[float]) -> Dict:
        """
        통합 매매 신호 생성
        
        Args:
            prices: 가격 리스트
        
        Returns:
            신호 정보 딕셔너리
        """
        if not prices or len(prices) < 30:  # 최소 30일 데이터 필요
            return {
                'signal': SignalType.HOLD,
                'strength': 0,
                'strategies': {},
                'reason': '데이터 부족'
            }
        
        # 각 전략별 신호 수집
        signals = {}
        signal_count = {
            SignalType.BUY: 0,
            SignalType.SELL: 0,
            SignalType.HOLD: 0
        }
        
        for strategy in self.strategies:
            try:
                signal = strategy.generate_signal(prices)
                strength = strategy.get_signal_strength(prices)
                
                signals[strategy.name] = {
                    'signal': signal,
                    'strength': strength
                }
                
                signal_count[signal] += 1
                
            except Exception as e:
                log.error(f"전략 '{strategy.name}' 실행 중 오류: {e}")
                signals[strategy.name] = {
                    'signal': SignalType.HOLD,
                    'strength': 0.0
                }
                signal_count[SignalType.HOLD] += 1
        
        # 최종 신호 결정 (다수결)
        total_strategies = len(self.strategies)
        
        # 매수 신호가 기준 이상
        if signal_count[SignalType.BUY] >= self.min_signal_strength:
            final_signal = SignalType.BUY
            reason = f"{signal_count[SignalType.BUY]}/{total_strategies} 전략이 매수 신호"
        
        # 매도 신호가 기준 이상
        elif signal_count[SignalType.SELL] >= self.min_signal_strength:
            final_signal = SignalType.SELL
            reason = f"{signal_count[SignalType.SELL]}/{total_strategies} 전략이 매도 신호"
        
        # 그 외: 관망
        else:
            final_signal = SignalType.HOLD
            reason = (
                f"신호 불일치 (매수: {signal_count[SignalType.BUY]}, "
                f"매도: {signal_count[SignalType.SELL]}, "
                f"관망: {signal_count[SignalType.HOLD]})"
            )
        
        # 신호 강도 계산 (각 전략의 강도 평균)
        total_strength = sum(s['strength'] for s in signals.values())
        avg_strength = total_strength / total_strategies if total_strategies > 0 else 0.0
        
        result = {
            'signal': final_signal,
            'strength': avg_strength,
            'signal_count': signal_count,
            'strategies': signals,
            'reason': reason
        }
        
        # 로그 출력
        if final_signal != SignalType.HOLD:
            log.info(
                f"📊 통합 신호: {final_signal.value} | "
                f"강도: {avg_strength:.2f} | {reason}"
            )
            for name, data in signals.items():
                log.debug(f"  - {name}: {data['signal'].value} (강도: {data['strength']:.2f})")
        
        return result


# 전략 팩토리 함수
def create_default_strategies(config: Config) -> List[BaseStrategy]:
    """
    기본 전략 세트 생성
    
    Args:
        config: Config 객체
    
    Returns:
        전략 리스트
    """
    strategies = [
        MACrossoverStrategy(config.MA_SHORT_PERIOD, config.MA_LONG_PERIOD),
        RSIStrategy(config.RSI_PERIOD, config.RSI_OVERSOLD, config.RSI_OVERBOUGHT),
        MACDStrategy(config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL),
    ]
    
    log.info(f"기본 전략 세트 생성 완료: {len(strategies)}개")
    return strategies


# 테스트 코드
if __name__ == "__main__":
    from config import Config
    
    # 테스트 데이터
    test_prices = [
        70000, 70500, 71000, 70800, 71500,
        72000, 72500, 71800, 72200, 73000,
        73500, 73200, 74000, 74500, 75000,
        74800, 75500, 76000, 75500, 76500,
        77000, 76800, 77500, 78000, 77500,
        78500, 79000, 78500, 79500, 80000
    ]
    
    print("매매 전략 테스트")
    print("=" * 60)
    
    # 개별 전략 테스트
    strategies = create_default_strategies(Config)
    
    for strategy in strategies:
        signal = strategy.generate_signal(test_prices)
        strength = strategy.get_signal_strength(test_prices)
        print(f"\n[{strategy.name}]")
        print(f"  신호: {signal.value}")
        print(f"  강도: {strength:.2f}")
    
    # 통합 전략 테스트
    print("\n" + "=" * 60)
    print("[통합 전략]")
    multi_strategy = MultiStrategy(strategies, Config.MIN_SIGNAL_STRENGTH)
    result = multi_strategy.generate_signal(test_prices)
    
    print(f"최종 신호: {result['signal'].value}")
    print(f"평균 강도: {result['strength']:.2f}")
    print(f"사유: {result['reason']}")
    print("\n전략별 상세:")
    for name, data in result['strategies'].items():
        print(f"  - {name}: {data['signal'].value} (강도: {data['strength']:.2f})")
    
    print("=" * 60)

