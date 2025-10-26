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
1. 전일 대비 상승률 >= 설정값 (기본: 5%)
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
        
        # 거래량 이력 (평균 계산용)
        self.volume_history: List[int] = [volume]
        self.max_volume_history = 10
        
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
    
    def is_surge_detected(
        self,
        min_change_rate: float,
        min_volume_ratio: float
    ) -> bool:
        """
        급등 조건 확인
        
        Args:
            min_change_rate: 최소 상승률 (%)
            min_volume_ratio: 최소 거래량 비율
        
        Returns:
            급등 여부
        """
        # 상승률 조건
        if self.current_change_rate < min_change_rate:
            return False
        
        # 거래량 조건
        volume_ratio = self.get_volume_ratio()
        if volume_ratio < min_volume_ratio:
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
        self.min_change_rate = Config.SURGE_MIN_CHANGE_RATE
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
        
        log.info(
            f"급등주 감지기 초기화: "
            f"후보 {self.candidate_count}개, "
            f"상승률 >= {self.min_change_rate}%, "
            f"거래량 >= {self.min_volume_ratio}배"
        )
    
    def initialize(self) -> bool:
        """
        초기화 및 후보군 로드
        
        Returns:
            초기화 성공 여부
        """
        try:
            log.info("급등주 후보군 로드 중...")
            
            # 거래대금 상위 종목 조회
            top_stocks = self.kiwoom.get_top_traded_stocks(self.candidate_count)
            
            if not top_stocks:
                log.error("거래대금 상위 종목 조회 실패")
                return False
            
            # 후보군 등록
            for stock in top_stocks:
                candidate = SurgeCandidate(
                    code=stock['code'],
                    name=stock['name'],
                    price=stock['price'],
                    change_rate=stock['change_rate'],
                    volume=stock['volume'],
                    trade_value=stock['trade_value']
                )
                self.candidates[stock['code']] = candidate
            
            log.success(f"급등주 후보군 로드 완료: {len(self.candidates)}개 종목")
            
            # 실시간 시세 등록
            candidate_codes = list(self.candidates.keys())
            self.kiwoom.register_real_data(candidate_codes)
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            log.error(f"급등주 감지기 초기화 중 오류: {e}")
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
            
            # 급등 조건 확인
            if not candidate.is_surge_detected(
                self.min_change_rate,
                self.min_volume_ratio
            ):
                return
            
            # 급등 감지!
            candidate.mark_detected()
            self.total_detected += 1
            self.detection_count[candidate.code] += 1
            
            volume_ratio = candidate.get_volume_ratio()
            
            log.warning(
                f"🚀 급등 감지! {candidate.name} ({candidate.code}) | "
                f"상승률: {candidate.current_change_rate:+.2f}% | "
                f"거래량: {volume_ratio:.2f}배 | "
                f"현재가: {candidate.current_price:,}원"
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
        return {
            'total_candidates': len(self.candidates),
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

