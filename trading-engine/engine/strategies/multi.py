"""
통합 전략 (Multi-Strategy)

[전략 개요]
여러 전략의 신호를 종합하여 최종 결정을 내리는 합의 알고리즘

[작동 방식]
1. 등록된 모든 전략의 신호를 수집
2. 각 신호의 강도를 계산
3. 최소 신호 강도 기준 이상일 때 최종 신호 생성
4. 예: 3개 전략 중 2개 이상이 매수 신호 → 최종 매수
"""

from typing import List, Dict
from .base import BaseStrategy, SignalType
from loguru import logger


class MultiStrategy:
    """
    여러 전략을 조합한 통합 전략
    
    합의 알고리즘: 여러 전략의 신호를 종합하여 최종 신호 결정
    """
    
    def __init__(self, strategies: List[BaseStrategy], min_signal_strength: int = 2):
        """
        Args:
            strategies: 전략 리스트
            min_signal_strength: 최소 동의 전략 수
        """
        self.strategies = strategies
        self.min_signal_strength = min_signal_strength
        logger.info(
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
        if not prices or len(prices) < 30:
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
                if not strategy.is_enabled():
                    continue
                
                signal = strategy.generate_signal(prices)
                strength = strategy.get_signal_strength(prices)
                
                signals[strategy.name] = {
                    'signal': signal,
                    'strength': strength
                }
                
                signal_count[signal] += 1
                
            except Exception as e:
                logger.error(f"전략 '{strategy.name}' 실행 중 오류: {e}")
                signals[strategy.name] = {
                    'signal': SignalType.HOLD,
                    'strength': 0.0
                }
                signal_count[SignalType.HOLD] += 1
        
        # 최종 신호 결정 (다수결)
        total_strategies = len([s for s in self.strategies if s.is_enabled()])
        
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
            logger.info(
                f"📊 통합 신호: {final_signal.value} | "
                f"강도: {avg_strength:.2f} | {reason}"
            )
            for name, data in signals.items():
                logger.debug(f"  - {name}: {data['signal'].value} (강도: {data['strength']:.2f})")
        
        return result

