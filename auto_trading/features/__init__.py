"""
고급 기능 모듈

이 패키지는 선택적으로 활성화 가능한 고급 기능을 포함합니다:
- surge_detector: 급등주 감지
- news_crawler: 뉴스 크롤링
- news_strategy: 뉴스 기반 전략
- sentiment_analyzer: 감성 분석
- market_scheduler: 시장 스케줄러
- scheduler: 자동 시작/종료
- health_monitor: 헬스 모니터
"""

__all__ = [
    'SurgeDetector',
    'NewsCrawler',
    'SentimentAnalyzer',
    'NewsBasedStrategy',
    'MarketScheduler',
    'TradingScheduler',
    'HealthMonitor',
]

