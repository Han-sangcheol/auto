"""
급등주 감지 모듈

[파일 역할]
거래대금 상위 종목을 실시간으로 모니터링하여 급등하는 종목을 감지합니다.

[주요 기능]
- 거래대금 상위 종목 후보군 관리
- 실시간 가격/거래량 모니터링
- 급등 조건 감지 (상승률 + 거래량 급증)
- 중복 감지 방지 (쿨다운 타임)

[급등 기준]
1. 모니터링 시작 이후 추가 상승률 >= 설정값 (기본: 5%)
2. 거래량 >= 평균 거래량 x 배수 (기본: 2배)

[사용 방법]
detector = SurgeDetector(kiwoom_api, callback)
detector.initialize()
detector.start_monitoring()
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import time
from logger import log
from config import Config


class SurgeCandidate:
    """급등주 후보 종목 정보"""
    
    def __init__(
        self,
        code: str,
        name: str,
        price: int,
        change_rate: float,
        volume: int,
        trade_value: int
    ):
        self.code = code
        self.name = name
        self.price = price
        self.change_rate = change_rate
        self.volume = volume
        self.trade_value = trade_value
        
        # 모니터링 데이터
        self.initial_price = price
        self.initial_volume = volume
        self.current_price = price
        self.current_volume = volume
        self.current_change_rate = change_rate
        
        # 🆕 모니터링 시작 시점 기준 (급등 판단용)
        self.monitoring_start_price = price  # 모니터링 시작 시점 가격
        self.monitoring_start_change_rate = change_rate  # 모니터링 시작 시점 전일 대비 상승률
        
        # 거래량 이력 (평균 계산용)
        self.volume_history: List[int] = [volume]
        self.max_volume_history = 10
        
        # 🆕 뉴스 감성 분석 결과
        self.news_score = 0  # -100 ~ +100 (부정 ~ 긍정)
        self.news_count = 0  # 분석된 뉴스 개수
        self.latest_news = []  # 최근 뉴스 제목 리스트 (최대 3개)
        
        # 🆕 호가 데이터 (선제적 매수 판단)
        self.bid_volume = 0  # 매수 총잔량
        self.ask_volume = 0  # 매도 총잔량
        self.execution_strength = 0  # 체결강도 (%)
        self.bid_ask_ratio = 0  # 매수/매도 잔량 비율
        
        # 감지 시간
        self.last_detected_time: Optional[datetime] = None
    
    def update_price(self, price: int, change_rate: float):
        """가격 업데이트"""
        self.current_price = price
        self.current_change_rate = change_rate
    
    def update_volume(self, volume: int):
        """거래량 업데이트"""
        self.current_volume = volume
        self.volume_history.append(volume)
        
        # 최근 N개만 유지
        if len(self.volume_history) > self.max_volume_history:
            self.volume_history = self.volume_history[-self.max_volume_history:]
    
    def update_order_book(self, bid_volume: int, ask_volume: int, execution_strength: int):
        """
        호가 데이터 업데이트 (선제적 매수 판단)
        
        Args:
            bid_volume: 매수 총잔량
            ask_volume: 매도 총잔량
            execution_strength: 체결강도 (%)
        """
        self.bid_volume = bid_volume
        self.ask_volume = ask_volume
        self.execution_strength = execution_strength
        
        # 매수/매도 잔량 비율 계산
        if ask_volume > 0:
            self.bid_ask_ratio = bid_volume / ask_volume
        else:
            self.bid_ask_ratio = 0
    
    def update_news_sentiment(self, news_score: int, news_count: int, news_titles: List[str]):
        """
        🆕 뉴스 감성 분석 결과 업데이트
        
        Args:
            news_score: 뉴스 감성 점수 (-100 ~ +100)
            news_count: 분석된 뉴스 개수
            news_titles: 뉴스 제목 리스트
        """
        self.news_score = news_score
        self.news_count = news_count
        self.latest_news = news_titles[:3]  # 최대 3개만 저장
    
    def get_buying_pressure(self) -> float:
        """
        매수 압력 점수 계산 (0~100)
        
        Returns:
            높을수록 매수세 강함
        """
        score = 0
        
        # 1. 매수/매도 잔량 비율 (최대 40점)
        if self.bid_ask_ratio > 2.0:
            score += 40
        elif self.bid_ask_ratio > 1.5:
            score += 30
        elif self.bid_ask_ratio > 1.0:
            score += 20
        elif self.bid_ask_ratio > 0.8:
            score += 10
        
        # 2. 체결강도 (최대 40점)
        if self.execution_strength > 200:
            score += 40
        elif self.execution_strength > 150:
            score += 30
        elif self.execution_strength > 120:
            score += 20
        elif self.execution_strength > 100:
            score += 10
        
        # 3. 상승률 (최대 20점)
        if self.current_change_rate > 7:
            score += 20
        elif self.current_change_rate > 5:
            score += 15
        elif self.current_change_rate > 3:
            score += 10
        elif self.current_change_rate > 1:
            score += 5
        
        return min(score, 100)
    
    def get_average_volume(self) -> float:
        """평균 거래량 계산"""
        if not self.volume_history:
            return 0
        return sum(self.volume_history) / len(self.volume_history)
    
    def get_volume_ratio(self) -> float:
        """현재 거래량 / 평균 거래량 비율"""
        avg_volume = self.get_average_volume()
        if avg_volume == 0:
            return 0
        return self.current_volume / avg_volume
    
    def get_monitoring_change_rate(self) -> float:
        """
        모니터링 시작 시점 대비 추가 상승률 계산
        
        Returns:
            추가 상승률 (%) 
            예: 시작 시 10% → 현재 15% = 추가 상승 5%
        """
        return self.current_change_rate - self.monitoring_start_change_rate
    
    def get_adjusted_surge_threshold(self, base_threshold: float) -> float:
        """
        🆕 뉴스 점수에 따른 급등 기준 동적 조정
        
        Args:
            base_threshold: 기본 급등 기준 (%)
        
        Returns:
            조정된 급등 기준 (%)
            
        Examples:
            - 뉴스 점수 +50 (호재), 기본 5% → 2.5% (50% 완화)
            - 뉴스 점수 0 (중립), 기본 5% → 5% (조정 없음)
            - 뉴스 점수 -50 (악재), 기본 5% → 5% (급등 기준은 유지)
        """
        from config import Config
        
        # 뉴스 분석이 비활성화되었거나 뉴스가 없으면 기본값
        if not Config.ENABLE_NEWS_ANALYSIS or self.news_count == 0:
            return base_threshold
        
        # 긍정 뉴스 (호재): 급등 기준 완화
        if self.news_score >= Config.NEWS_BUY_THRESHOLD:
            # 점수 비율 계산 (0 ~ 1)
            score_ratio = min(self.news_score / 100, 1.0)
            # 완화 비율 적용 (예: 50% 완화)
            adjust_ratio = Config.NEWS_POSITIVE_SURGE_ADJUST / 100
            adjusted_threshold = base_threshold * (1 - adjust_ratio * score_ratio)
            return adjusted_threshold
        
        # 부정 뉴스 또는 중립: 급등 기준 유지
        return base_threshold
    
    def is_surge_detected(
        self,
        min_monitoring_change_rate: float,
        min_volume_ratio: float,
        min_buying_pressure: float = 60.0  # 최소 매수 압력 점수
    ) -> bool:
        """
        급등 조건 확인 (모니터링 시작 시점 대비, 뉴스 점수 반영)
        
        Args:
            min_monitoring_change_rate: 모니터링 시작 이후 최소 추가 상승률 (%)
            min_volume_ratio: 최소 거래량 비율
            min_buying_pressure: 최소 매수 압력 점수 (0~100, 기본 60)
        
        Returns:
            급등 여부
        """
        # 1. 기본 조건: 모니터링 시작 이후 추가 상승률 (🆕 뉴스 점수 반영)
        adjusted_threshold = self.get_adjusted_surge_threshold(min_monitoring_change_rate)
        monitoring_change = self.get_monitoring_change_rate()
        if monitoring_change < adjusted_threshold:
            return False
        
        # 2. 기본 조건: 거래량 비율
        volume_ratio = self.get_volume_ratio()
        if volume_ratio < min_volume_ratio:
            return False
        
        # 3. 🆕 고급 조건: 매수 압력 (선제적 감지)
        # 호가 데이터가 있으면 매수세 강도를 확인
        if self.bid_volume > 0 or self.ask_volume > 0:
            buying_pressure = self.get_buying_pressure()
            if buying_pressure < min_buying_pressure:
                return False
        
        return True
    
    def can_detect_again(self, cooldown_minutes: int) -> bool:
        """
        재감지 가능 여부 (쿨다운 확인)
        
        Args:
            cooldown_minutes: 쿨다운 시간 (분)
        
        Returns:
            재감지 가능 여부
        """
        if self.last_detected_time is None:
            return True
        
        elapsed = datetime.now() - self.last_detected_time
        return elapsed.total_seconds() >= (cooldown_minutes * 60)
    
    def mark_detected(self):
        """감지 시간 기록"""
        self.last_detected_time = datetime.now()
    
    def __repr__(self):
        return (
            f"SurgeCandidate({self.code} {self.name}, "
            f"가격: {self.current_price:,}원, "
            f"상승률: {self.current_change_rate:+.2f}%, "
            f"거래량 비율: {self.get_volume_ratio():.2f}배)"
        )


class SurgeDetector:
    """급등주 감지 클래스"""
    
    def __init__(self, kiwoom, surge_callback: Optional[Callable] = None):
        """
        초기화
        
        Args:
            kiwoom: KiwoomAPI 인스턴스
            surge_callback: 급등 감지 시 호출할 콜백 함수 (stock_code, candidate)
        """
        self.kiwoom = kiwoom
        self.surge_callback = surge_callback
        
        # 설정값
        self.candidate_count = Config.SURGE_CANDIDATE_COUNT
        self.min_change_rate = Config.SURGE_MIN_CHANGE_RATE  # 전일 대비 (레퍼런스용)
        self.min_monitoring_change_rate = Config.SURGE_MONITORING_CHANGE_RATE  # 🆕 모니터링 시작 이후 추가 상승률
        self.min_volume_ratio = Config.SURGE_MIN_VOLUME_RATIO
        self.cooldown_minutes = Config.SURGE_COOLDOWN_MINUTES
        
        # 후보군
        self.candidates: Dict[str, SurgeCandidate] = {}
        
        # 실행 상태
        self.is_initialized = False
        self.is_monitoring = False
        
        # 통계
        self.total_detected = 0
        self.detection_count = defaultdict(int)
        
        # 🆕 뉴스 분석 (선택적)
        self.news_crawler = None
        self.sentiment_analyzer = None
        if Config.ENABLE_NEWS_ANALYSIS:
            try:
                from news_crawler import NewsCrawler
                from sentiment_analyzer import SentimentAnalyzer
                
                self.news_crawler = NewsCrawler()
                self.sentiment_analyzer = SentimentAnalyzer()
                log.info("✅ 뉴스 분석 모듈 로드 완료")
            except Exception as e:
                log.warning(f"⚠️  뉴스 분석 모듈 로드 실패 (기능 비활성화): {e}")
        
        log.info(
            f"급등주 감지기 초기화: "
            f"후보 {self.candidate_count}개, "
            f"모니터링 추가 상승률 >= {self.min_monitoring_change_rate}%, "
            f"거래량 >= {self.min_volume_ratio}배, "
            f"뉴스 분석: {'활성화' if self.news_crawler else '비활성화'}"
        )
    
    def initialize(self) -> bool:
        """
        초기화 및 후보군 로드
        
        Returns:
            초기화 성공 여부
        """
        try:
            log.info("=" * 70)
            log.info("🚀 급등주 감지기 초기화 시작")
            log.info("=" * 70)
            log.info(f"📊 설정: 후보 {self.candidate_count}개, 모니터링 추가 상승률 >={self.min_monitoring_change_rate}%, 거래량 >={self.min_volume_ratio}배")
            
            # 거래대금 상위 종목 조회 (🆕 연속조회 지원)
            log.info("1️⃣ 거래대금 상위 종목 조회 중...")
            from config import Config
            top_stocks = self.kiwoom.get_top_traded_stocks(
                count=self.candidate_count,
                use_continuous=Config.SURGE_USE_CONTINUOUS,
                max_continuous=Config.SURGE_MAX_CONTINUOUS
            )
            
            if not top_stocks:
                log.error("❌ 거래대금 상위 종목 조회 실패 - 결과가 비어있습니다.")
                return False
            
            log.info(f"✅ 조회 성공: {len(top_stocks)}개 종목")
            
            # 후보군 등록
            log.info("2️⃣ 급등주 후보군 등록 중...")
            for i, stock in enumerate(top_stocks, 1):
                candidate = SurgeCandidate(
                    code=stock['code'],
                    name=stock['name'],
                    price=stock['price'],
                    change_rate=stock['change_rate'],
                    volume=stock['volume'],
                    trade_value=stock['trade_value']
                )
                self.candidates[stock['code']] = candidate
                
                # 처음 5개만 로그 출력
                if i <= 5:
                    log.info(
                        f"   {i}. {stock['name']}({stock['code']}) "
                        f"{stock['price']:,}원 ({stock['change_rate']:+.2f}%) "
                        f"거래대금: {stock['trade_value']:,}원"
                    )
            
            if len(top_stocks) > 5:
                log.info(f"   ... 외 {len(top_stocks) - 5}개")
            
            log.success(f"✅ 급등주 후보군 등록 완료: {len(self.candidates)}개 종목")
            
            # 🆕 뉴스 분석 (선택적)
            if self.news_crawler and self.sentiment_analyzer:
                log.info("2-1️⃣ 뉴스 분석 중...")
                self._analyze_news_for_candidates()
            
            # 실시간 시세 등록
            log.info("3️⃣ 급등주 후보군 실시간 시세 등록 중...")
            candidate_codes = list(self.candidates.keys())
            
            # 배치로 나눠서 등록 (API 과부하 방지)
            batch_size = 50
            for i in range(0, len(candidate_codes), batch_size):
                batch = candidate_codes[i:i+batch_size]
                log.info(f"   📡 배치 {i//batch_size + 1}: {len(batch)}개 종목 등록 중...")
                self.kiwoom.register_real_data(batch)
                
                # 배치 간 대기
                if i + batch_size < len(candidate_codes):
                    import time
                    time.sleep(1)
            
            log.success(f"✅ 실시간 시세 등록 완료: {len(candidate_codes)}개 종목")
            
            self.is_initialized = True
            log.info("=" * 70)
            log.success("✅ 급등주 감지기 초기화 완료!")
            log.info("=" * 70)
            return True
            
        except Exception as e:
            log.error("=" * 70)
            log.error(f"❌ 급등주 감지기 초기화 중 오류!")
            log.error(f"   에러 타입: {type(e).__name__}")
            log.error(f"   에러 메시지: {e}")
            import traceback
            log.error(f"   상세: {traceback.format_exc()}")
            log.error("=" * 70)
            return False
    
    def start_monitoring(self):
        """실시간 모니터링 시작"""
        if not self.is_initialized:
            log.error("초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
            return
        
        self.is_monitoring = True
        log.success(f"🚀 급등주 모니터링 시작!")
        log.info(f"   📋 후보군: {len(self.candidates)}개 종목")
        log.info(f"   📊 조건: 상승률 >= {self.min_change_rate}%, 거래량 >= {self.min_volume_ratio}배")
        
        # 후보군 샘플 출력 (처음 5개)
        sample_codes = list(self.candidates.keys())[:5]
        for code in sample_codes:
            candidate = self.candidates[code]
            log.info(f"   • {candidate.name}({code})")
        if len(self.candidates) > 5:
            log.info(f"   ... 외 {len(self.candidates) - 5}개")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
        log.info("급등주 모니터링 중지")
    
    def _analyze_news_for_candidates(self):
        """
        🆕 후보군 종목들의 뉴스 분석
        
        각 후보 종목에 대해 최신 뉴스를 수집하고 감성 분석을 수행합니다.
        뉴스 점수는 급등 기준 조정에 사용됩니다.
        """
        if not self.news_crawler or not self.sentiment_analyzer:
            return
        
        try:
            analyzed_count = 0
            positive_count = 0
            negative_count = 0
            
            for stock_code, candidate in self.candidates.items():
                try:
                    # 뉴스 수집 (최대 10개)
                    news_list = self.news_crawler.get_latest_news(stock_code, max_count=10)
                    
                    if len(news_list) >= Config.NEWS_MIN_COUNT:
                        # 감성 분석
                        analysis = self.sentiment_analyzer.analyze_news_list(news_list)
                        
                        # 후보 종목에 뉴스 점수 업데이트
                        news_titles = [news.title for news in news_list[:3]]
                        candidate.update_news_sentiment(
                            news_score=analysis['average_score'],
                            news_count=len(news_list),
                            news_titles=news_titles
                        )
                        
                        analyzed_count += 1
                        
                        # 통계
                        if analysis['average_score'] >= Config.NEWS_BUY_THRESHOLD:
                            positive_count += 1
                            log.info(
                                f"   ✅ 호재: {candidate.name}({stock_code}) "
                                f"점수: {analysis['average_score']:+d}/100 "
                                f"(뉴스 {len(news_list)}개)"
                            )
                        elif analysis['average_score'] <= Config.NEWS_SELL_THRESHOLD:
                            negative_count += 1
                            log.warning(
                                f"   ⚠️  악재: {candidate.name}({stock_code}) "
                                f"점수: {analysis['average_score']:+d}/100 "
                                f"(뉴스 {len(news_list)}개)"
                            )
                    
                    # API 과부하 방지
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    log.debug(f"   뉴스 분석 실패 ({stock_code}): {e}")
            
            log.success(
                f"✅ 뉴스 분석 완료: {analyzed_count}개 종목 "
                f"(호재: {positive_count}개, 악재: {negative_count}개)"
            )
            
        except Exception as e:
            log.error(f"뉴스 분석 중 오류: {e}")
    
    def on_price_update(self, stock_code: str, price_data: Dict):
        """
        실시간 가격 데이터 처리
        
        Args:
            stock_code: 종목 코드
            price_data: 가격 데이터 {'current_price', 'change_rate', 'volume'}
        """
        if not self.is_monitoring:
            return
        
        # 후보군에 없는 종목은 무시
        if stock_code not in self.candidates:
            return
        
        try:
            candidate = self.candidates[stock_code]
            
            # 가격 업데이트
            current_price = price_data.get('current_price')
            change_rate = price_data.get('change_rate')
            volume = price_data.get('volume')
            
            if current_price:
                candidate.update_price(current_price, change_rate)
            
            if volume:
                candidate.update_volume(volume)
            
            # 급등 조건 확인
            self._check_surge(candidate)
            
        except Exception as e:
            log.error(f"가격 업데이트 처리 중 오류: {e}")
    
    def on_order_book_update(self, stock_code: str, order_book_data: Dict):
        """
        🆕 실시간 호가 데이터 처리 (선제적 매수 판단)
        
        Args:
            stock_code: 종목 코드
            order_book_data: 호가 데이터 {
                'bid_volume': 매수 총잔량,
                'ask_volume': 매도 총잔량,
                'execution_strength': 체결강도
            }
        """
        if not self.is_monitoring:
            return
        
        # 후보군에 없는 종목은 무시
        if stock_code not in self.candidates:
            return
        
        try:
            candidate = self.candidates[stock_code]
            
            # 호가 데이터 업데이트
            bid_volume = order_book_data.get('bid_volume', 0)
            ask_volume = order_book_data.get('ask_volume', 0)
            execution_strength = order_book_data.get('execution_strength', 0)
            
            candidate.update_order_book(bid_volume, ask_volume, execution_strength)
            
            # 호가 데이터 기록 (디버깅용, 처음 3번만)
            if not hasattr(self, '_orderbook_log_count'):
                self._orderbook_log_count = {}
            if stock_code not in self._orderbook_log_count:
                self._orderbook_log_count[stock_code] = 0
            
            self._orderbook_log_count[stock_code] += 1
            if self._orderbook_log_count[stock_code] <= 3:
                buying_pressure = candidate.get_buying_pressure()
                log.debug(
                    f"📊 호가: {candidate.name}({stock_code}) | "
                    f"매수세: {buying_pressure:.0f}점 | "
                    f"잔량비: {candidate.bid_ask_ratio:.2f} | "
                    f"체결강도: {execution_strength}%"
                )
            
        except Exception as e:
            log.error(f"호가 데이터 처리 중 오류 ({stock_code}): {e}")
    
    def _check_surge(self, candidate: SurgeCandidate):
        """
        급등 조건 확인 및 콜백 호출
        
        Args:
            candidate: 후보 종목
        """
        try:
            # 쿨다운 체크
            if not candidate.can_detect_again(self.cooldown_minutes):
                return
            
            # 급등 조건 확인 (모니터링 시작 이후 추가 상승률 기준)
            if not candidate.is_surge_detected(
                self.min_monitoring_change_rate,
                self.min_volume_ratio
            ):
                return
            
            # 급등 감지!
            candidate.mark_detected()
            self.total_detected += 1
            self.detection_count[candidate.code] += 1
            
            volume_ratio = candidate.get_volume_ratio()
            buying_pressure = candidate.get_buying_pressure()
            monitoring_change = candidate.get_monitoring_change_rate()
            
            # 🆕 호가 정보 포함
            orderbook_info = ""
            if candidate.bid_volume > 0 or candidate.ask_volume > 0:
                orderbook_info = (
                    f" | 매수세: {buying_pressure:.0f}점 "
                    f"(잔량비 {candidate.bid_ask_ratio:.2f}, "
                    f"체결강도 {candidate.execution_strength}%)"
                )
            
            # 🆕 뉴스 정보 포함
            news_info = ""
            if candidate.news_count > 0:
                news_sentiment = "호재" if candidate.news_score >= Config.NEWS_BUY_THRESHOLD else \
                                "악재" if candidate.news_score <= Config.NEWS_SELL_THRESHOLD else "중립"
                news_info = f" | 뉴스: {news_sentiment} ({candidate.news_score:+d}점, {candidate.news_count}개)"
                
                # 조정된 급등 기준 표시
                adjusted_threshold = candidate.get_adjusted_surge_threshold(self.min_monitoring_change_rate)
                if adjusted_threshold != self.min_monitoring_change_rate:
                    news_info += f" → 기준 {self.min_monitoring_change_rate:.1f}%→{adjusted_threshold:.1f}%"
            
            log.warning(
                f"🚀 급등 감지! {candidate.name} ({candidate.code}) | "
                f"전일대비: {candidate.current_change_rate:+.2f}% "
                f"(시작시점: {candidate.monitoring_start_change_rate:+.2f}%, 추가상승: {monitoring_change:+.2f}%) | "
                f"거래량: {volume_ratio:.2f}배 | "
                f"현재가: {candidate.current_price:,}원"
                f"{orderbook_info}"
                f"{news_info}"
            )
            
            # 콜백 호출
            if self.surge_callback:
                self.surge_callback(candidate.code, candidate)
                
        except Exception as e:
            log.error(f"급등 확인 중 오류: {e}")
    
    def get_candidate(self, stock_code: str) -> Optional[SurgeCandidate]:
        """
        후보 종목 조회
        
        Args:
            stock_code: 종목 코드
        
        Returns:
            후보 종목 정보 또는 None
        """
        return self.candidates.get(stock_code)
    
    def get_statistics(self) -> Dict:
        """
        통계 정보 반환
        
        Returns:
            통계 딕셔너리
        """
        candidates_count = len(self.candidates)
        return {
            # 새로운 키 이름 (trading_engine.py, monitor_gui.py 호환)
            'candidate_count': candidates_count,
            'detected_count': self.total_detected,
            # 기존 키 이름 유지 (하위 호환성)
            'total_candidates': candidates_count,
            'total_detected': self.total_detected,
            'is_monitoring': self.is_monitoring,
            'detection_count': dict(self.detection_count)
        }
    
    def print_status(self):
        """현재 상태 출력"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("급등주 감지기 현황")
        print("=" * 60)
        print(f"후보 종목 수:   {stats['total_candidates']:>15}개")
        print(f"총 감지 횟수:   {stats['total_detected']:>15}회")
        print(f"모니터링 상태: {'실행 중' if stats['is_monitoring'] else '중지':>16}")
        
        if stats['detection_count']:
            print(f"\n종목별 감지 횟수:")
            for code, count in stats['detection_count'].items():
                if code in self.candidates:
                    name = self.candidates[code].name
                    print(f"  {code} ({name}): {count}회")
        
        print("=" * 60 + "\n")


# 테스트 코드
if __name__ == "__main__":
    print("급등주 감지기 테스트")
    print("=" * 60)
    
    # 테스트 콜백
    def test_callback(stock_code, candidate):
        print(f"\n[콜백] 급등 감지: {candidate}")
    
    # 급등주 감지기는 실제 키움 API 연결 필요
    print("실제 테스트는 키움 API 연결 후 가능합니다.")
    print("=" * 60)

