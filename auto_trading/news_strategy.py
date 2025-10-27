"""
뉴스 기반 매매 전략 모듈

[파일 역할]
뉴스 감성 분석 결과를 매매 신호로 전환합니다.

[주요 기능]
- 뉴스 점수를 매수/매도 신호로 변환
- 기존 기술적 분석과 결합
- 신호 강도 계산

[신호 생성 규칙]
- 긍정 뉴스 >= 70점: 매수 신호 강도 +1
- 부정 뉴스 <= -70점 & 보유 중: 매도 신호 강도 +1
- -70 ~ +70: 중립 (신호 없음)

[사용 방법]
strategy = NewsBasedStrategy(news_crawler, sentiment_analyzer)
signal = strategy.generate_signal(stock_code)
"""

from typing import Dict, Optional
from enum import Enum

from news_crawler import NewsCrawler
from sentiment_analyzer import SentimentAnalyzer
from strategies import SignalType, BaseStrategy
from logger import log


class NewsBasedStrategy(BaseStrategy):
    """뉴스 기반 매매 전략"""
    
    def __init__(
        self,
        news_crawler: NewsCrawler,
        sentiment_analyzer: SentimentAnalyzer,
        buy_threshold: int = 30,  # 매수 신호 임계값
        sell_threshold: int = -30,  # 매도 신호 임계값
        min_news_count: int = 3  # 최소 뉴스 개수
    ):
        super().__init__("뉴스 감성")
        self.news_crawler = news_crawler
        self.sentiment_analyzer = sentiment_analyzer
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.min_news_count = min_news_count
        
        log.info(
            f"뉴스 기반 전략 초기화: "
            f"매수 임계값 {buy_threshold}, 매도 임계값 {sell_threshold}"
        )
    
    def generate_signal_for_stock(
        self,
        stock_code: str,
        is_holding: bool = False
    ) -> Dict:
        """
        특정 종목의 뉴스 기반 신호 생성
        
        Args:
            stock_code: 종목 코드
            is_holding: 현재 보유 중 여부
        
        Returns:
            신호 정보 딕셔너리
        """
        try:
            # 뉴스 가져오기 (캐시 우선)
            news_list = self.news_crawler.get_cached_news(stock_code)
            
            # 뉴스가 없거나 부족하면 새로 가져오기
            if len(news_list) < self.min_news_count:
                log.debug(f"뉴스 부족 - 새로 가져오기: {stock_code}")
                news_list = self.news_crawler.get_latest_news(stock_code, max_count=20)
            
            # 여전히 부족하면 중립
            if len(news_list) < self.min_news_count:
                return {
                    'signal': SignalType.HOLD,
                    'strength': 0.0,
                    'reason': f'뉴스 부족 ({len(news_list)}개)',
                    'news_score': 0
                }
            
            # 뉴스 감성 분석
            analysis = self.sentiment_analyzer.analyze_news_list(news_list)
            average_score = analysis['average_score']
            
            # 신호 생성
            signal = SignalType.HOLD
            reason = f"뉴스 점수: {average_score:+d}/100"
            
            # 매수 신호
            if average_score >= self.buy_threshold:
                signal = SignalType.BUY
                reason = (
                    f"긍정 뉴스 ({analysis['positive_count']}개), "
                    f"점수: {average_score:+d}/100"
                )
            
            # 매도 신호 (보유 중일 때만)
            elif is_holding and average_score <= self.sell_threshold:
                signal = SignalType.SELL
                reason = (
                    f"부정 뉴스 ({analysis['negative_count']}개), "
                    f"점수: {average_score:+d}/100"
                )
            
            # 신호 강도 계산 (0.0 ~ 1.0)
            strength = self.calculate_strength(average_score, signal)
            
            return {
                'signal': signal,
                'strength': strength,
                'reason': reason,
                'news_score': average_score,
                'news_count': len(news_list),
                'analysis': analysis
            }
            
        except Exception as e:
            log.error(f"뉴스 신호 생성 오류 ({stock_code}): {e}")
            return {
                'signal': SignalType.HOLD,
                'strength': 0.0,
                'reason': f'분석 오류: {e}',
                'news_score': 0
            }
    
    def calculate_strength(self, score: int, signal: SignalType) -> float:
        """
        신호 강도 계산
        
        Args:
            score: 뉴스 점수 (-100 ~ +100)
            signal: 신호 타입
        
        Returns:
            신호 강도 (0.0 ~ 1.0)
        """
        if signal == SignalType.HOLD:
            return 0.0
        
        # 절대값 사용
        abs_score = abs(score)
        
        # 30 ~ 100 범위를 0.0 ~ 1.0으로 매핑
        if abs_score >= 100:
            return 1.0
        elif abs_score >= 70:
            return 0.8
        elif abs_score >= 50:
            return 0.6
        elif abs_score >= 30:
            return 0.4
        else:
            return 0.2
    
    def generate_signal(self, prices: list) -> SignalType:
        """
        BaseStrategy 인터페이스 구현
        (가격 데이터가 아닌 종목 코드 기반이므로 직접 사용 안 함)
        
        Args:
            prices: 가격 리스트 (사용 안 함)
        
        Returns:
            관망 신호
        """
        # 이 메서드는 MultiStrategy 호환을 위한 것
        # 실제로는 generate_signal_for_stock() 사용
        return SignalType.HOLD
    
    def get_signal_strength(self, prices: list) -> float:
        """
        BaseStrategy 인터페이스 구현
        
        Args:
            prices: 가격 리스트 (사용 안 함)
        
        Returns:
            0.0
        """
        return 0.0


class NewsEnhancedMultiStrategy:
    """
    뉴스 분석이 통합된 다중 전략
    
    기술적 분석 + 뉴스 감성 분석을 결합하여 최종 신호 생성
    """
    
    def __init__(
        self,
        technical_strategies: list,
        news_strategy: NewsBasedStrategy,
        min_technical_signals: int = 2,
        news_weight: float = 1.0
    ):
        """
        초기화
        
        Args:
            technical_strategies: 기술적 분석 전략 리스트
            news_strategy: 뉴스 기반 전략
            min_technical_signals: 기술적 분석 최소 신호 수
            news_weight: 뉴스 신호 가중치 (0.0 ~ 2.0)
        """
        self.technical_strategies = technical_strategies
        self.news_strategy = news_strategy
        self.min_technical_signals = min_technical_signals
        self.news_weight = news_weight
        
        log.info(
            f"뉴스 통합 전략 초기화: "
            f"기술 전략 {len(technical_strategies)}개, "
            f"뉴스 가중치 {news_weight}"
        )
    
    def generate_signal(
        self,
        stock_code: str,
        prices: list,
        is_holding: bool = False
    ) -> Dict:
        """
        통합 신호 생성
        
        Args:
            stock_code: 종목 코드
            prices: 가격 리스트
            is_holding: 보유 중 여부
        
        Returns:
            신호 정보 딕셔너리
        """
        # 1. 기술적 분석 신호
        technical_buy_count = 0
        technical_sell_count = 0
        technical_signals = {}
        
        for strategy in self.technical_strategies:
            try:
                signal = strategy.generate_signal(prices)
                strength = strategy.get_signal_strength(prices)
                
                technical_signals[strategy.name] = {
                    'signal': signal,
                    'strength': strength
                }
                
                if signal == SignalType.BUY:
                    technical_buy_count += 1
                elif signal == SignalType.SELL:
                    technical_sell_count += 1
                    
            except Exception as e:
                log.error(f"기술 전략 '{strategy.name}' 오류: {e}")
        
        # 2. 뉴스 기반 신호
        news_result = self.news_strategy.generate_signal_for_stock(stock_code, is_holding)
        news_signal = news_result['signal']
        news_strength = news_result['strength']
        news_score = news_result['news_score']
        
        # 3. 통합 판단
        final_signal = SignalType.HOLD
        reason_parts = []
        
        # 기술적 분석 결과
        if technical_buy_count >= self.min_technical_signals:
            final_signal = SignalType.BUY
            reason_parts.append(
                f"기술 분석 매수 {technical_buy_count}/{len(self.technical_strategies)}"
            )
        elif technical_sell_count >= self.min_technical_signals:
            final_signal = SignalType.SELL
            reason_parts.append(
                f"기술 분석 매도 {technical_sell_count}/{len(self.technical_strategies)}"
            )
        
        # 뉴스 신호 반영
        if news_signal != SignalType.HOLD:
            # 뉴스가 기술 분석과 같은 방향이면 강화
            if news_signal == final_signal:
                reason_parts.append(f"뉴스 동의 (점수: {news_score:+d})")
            # 뉴스가 강한 신호이고 기술 분석이 약하면 뉴스 우선
            elif news_strength >= 0.6 and final_signal == SignalType.HOLD:
                final_signal = news_signal
                reason_parts.append(f"뉴스 주도 (점수: {news_score:+d})")
            # 뉴스가 반대 방향이면 약화
            elif news_signal != final_signal and news_strength >= 0.5:
                final_signal = SignalType.HOLD
                reason_parts.append(f"뉴스 상충 (점수: {news_score:+d})")
        
        # 이유 조합
        if not reason_parts:
            reason = "신호 없음 (관망)"
        else:
            reason = ", ".join(reason_parts)
        
        # 신호 강도 계산
        total_strength = 0.0
        for sig in technical_signals.values():
            total_strength += sig['strength']
        
        if news_signal == final_signal:
            total_strength += news_strength * self.news_weight
        
        avg_strength = total_strength / (len(self.technical_strategies) + self.news_weight)
        
        return {
            'signal': final_signal,
            'strength': avg_strength,
            'reason': reason,
            'technical_signals': technical_signals,
            'news_result': news_result,
            'news_score': news_score
        }


# 테스트 코드
if __name__ == "__main__":
    print("뉴스 기반 전략 테스트")
    print("=" * 60)
    
    # 모듈 임포트 테스트
    print("✅ 뉴스 기반 전략 모듈 로드 완료")
    print("=" * 60)

