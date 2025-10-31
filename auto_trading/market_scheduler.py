"""
시장 스케줄러 모듈

[파일 역할]
한국 주식시장의 운영 시간을 관리하고 현재 시장 상태를 제공합니다.

[주요 기능]
1. 시장 상태 감지
   - 장 시작 전 (동시호가)
   - 정규 거래 시간
   - 시간외 매매
   - 장 마감
   - 주말/공휴일

2. 시간 계산
   - 장 시작까지 남은 시간
   - 장 마감까지 남은 시간
   - 다음 거래일 계산

3. 스케줄링
   - 자동 시작 예약
   - 자동 종료 예약
   - 시간대별 알림

[사용 방법]
scheduler = MarketScheduler()
state = scheduler.get_current_market_state()
if state == MarketState.OPEN:
    # 정규장 거래 로직
"""

from enum import Enum
from datetime import datetime, time as dt_time, timedelta
from typing import Optional, Callable
from PyQt5.QtCore import QTimer
from logger import log


class MarketState(Enum):
    """시장 상태"""
    CLOSED = "장외시간"
    PRE_OPEN = "장시작전"
    OPEN = "정규장"
    AFTER_HOURS = "시간외"
    WEEKEND = "주말"
    HOLIDAY = "공휴일"


class MarketScheduler:
    """시장 스케줄러 클래스"""
    
    def __init__(self):
        """초기화"""
        from config import Config
        
        # 시간 설정 로드
        self.pre_open_time = self._parse_time(Config.MARKET_PRE_OPEN_TIME)
        self.open_time = self._parse_time(Config.MARKET_OPEN_TIME)
        self.close_time = self._parse_time(Config.MARKET_CLOSE_TIME)
        self.after_hours_start = self._parse_time(Config.MARKET_AFTER_HOURS_START)
        self.after_hours_end = self._parse_time(Config.MARKET_AFTER_HOURS_END)
        
        # 자동 시작/종료 설정
        self.auto_start_enabled = Config.AUTO_START_ENABLED
        self.auto_start_time = self._parse_time(Config.AUTO_START_TIME)
        self.auto_stop_time = self._parse_time(Config.AUTO_STOP_TIME)
        
        # 타이머
        self.auto_start_timer: Optional[QTimer] = None
        self.auto_stop_timer: Optional[QTimer] = None
        
        # 2025년 공휴일 (간단 구현)
        self.holidays_2025 = [
            (1, 1),   # 신정
            (1, 28),  # 설날 전날
            (1, 29),  # 설날
            (1, 30),  # 설날 다음날
            (3, 1),   # 삼일절
            (5, 5),   # 어린이날
            (5, 15),  # 부처님오신날
            (6, 6),   # 현충일
            (8, 15),  # 광복절
            (9, 28),  # 추석 전날
            (9, 29),  # 추석
            (9, 30),  # 추석 다음날
            (10, 3),  # 개천절
            (10, 9),  # 한글날
            (12, 25), # 성탄절
        ]
        
        log.info("시장 스케줄러 초기화 완료")
    
    def _parse_time(self, time_str: str) -> dt_time:
        """
        시간 문자열을 time 객체로 변환
        
        Args:
            time_str: "HH:MM" 형식의 시간 문자열
        
        Returns:
            time 객체
        """
        try:
            hour, minute = map(int, time_str.split(':'))
            return dt_time(hour, minute)
        except Exception as e:
            log.error(f"시간 파싱 오류: {time_str} - {e}")
            return dt_time(9, 0)  # 기본값
    
    def is_holiday(self, date: Optional[datetime] = None) -> bool:
        """
        공휴일 여부 확인
        
        Args:
            date: 확인할 날짜 (None이면 오늘)
        
        Returns:
            공휴일이면 True
        """
        if date is None:
            date = datetime.now()
        
        # 주말 체크
        if date.weekday() >= 5:  # 토요일(5), 일요일(6)
            return True
        
        # 공휴일 체크 (2025년만)
        if date.year == 2025:
            date_tuple = (date.month, date.day)
            if date_tuple in self.holidays_2025:
                return True
        
        return False
    
    def get_current_market_state(self) -> MarketState:
        """
        현재 시장 상태 반환
        
        Returns:
            현재 시장 상태
        """
        now = datetime.now()
        current_time = now.time()
        
        # 주말/공휴일 체크
        if self.is_holiday(now):
            if now.weekday() >= 5:
                return MarketState.WEEKEND
            else:
                return MarketState.HOLIDAY
        
        # 시간대별 상태 체크
        if self.pre_open_time <= current_time < self.open_time:
            return MarketState.PRE_OPEN
        elif self.open_time <= current_time < self.close_time:
            return MarketState.OPEN
        elif self.after_hours_start <= current_time < self.after_hours_end:
            return MarketState.AFTER_HOURS
        else:
            return MarketState.CLOSED
    
    def is_trading_allowed(self) -> bool:
        """
        매매 가능 여부 확인
        
        Returns:
            매매 가능하면 True
        """
        state = self.get_current_market_state()
        
        # 정규장은 항상 허용
        if state == MarketState.OPEN:
            return True
        
        # 시간외는 설정에 따라
        from config import Config
        if state == MarketState.AFTER_HOURS and Config.ENABLE_AFTER_HOURS_TRADING:
            return True
        
        return False
    
    def get_time_until_market_open(self) -> int:
        """
        장 시작까지 남은 시간 (분)
        
        Returns:
            남은 시간 (분), 이미 장중이면 0
        """
        now = datetime.now()
        state = self.get_current_market_state()
        
        # 이미 장중이면 0
        if state in [MarketState.OPEN, MarketState.PRE_OPEN]:
            return 0
        
        # 오늘 장 시작 시간
        today_open = now.replace(
            hour=self.open_time.hour,
            minute=self.open_time.minute,
            second=0,
            microsecond=0
        )
        
        # 오늘 장이 이미 끝났으면 다음 거래일
        if now.time() >= self.close_time:
            # 다음 날부터 시작
            next_day = now + timedelta(days=1)
            while self.is_holiday(next_day):
                next_day += timedelta(days=1)
            
            next_open = next_day.replace(
                hour=self.open_time.hour,
                minute=self.open_time.minute,
                second=0,
                microsecond=0
            )
            
            delta = next_open - now
            return int(delta.total_seconds() / 60)
        
        # 오늘 장이 아직 시작 안 했으면
        if self.is_holiday(now):
            # 다음 거래일 찾기
            next_day = now + timedelta(days=1)
            while self.is_holiday(next_day):
                next_day += timedelta(days=1)
            
            next_open = next_day.replace(
                hour=self.open_time.hour,
                minute=self.open_time.minute,
                second=0,
                microsecond=0
            )
            
            delta = next_open - now
            return int(delta.total_seconds() / 60)
        
        # 오늘 장 시작까지
        delta = today_open - now
        return max(0, int(delta.total_seconds() / 60))
    
    def get_time_until_market_close(self) -> int:
        """
        장 마감까지 남은 시간 (분)
        
        Returns:
            남은 시간 (분), 이미 장 마감이면 0
        """
        now = datetime.now()
        state = self.get_current_market_state()
        
        # 장중이 아니면 0
        if state != MarketState.OPEN:
            return 0
        
        # 오늘 장 마감 시간
        today_close = now.replace(
            hour=self.close_time.hour,
            minute=self.close_time.minute,
            second=0,
            microsecond=0
        )
        
        delta = today_close - now
        return max(0, int(delta.total_seconds() / 60))
    
    def schedule_auto_start(self, callback: Callable):
        """
        자동 시작 예약
        
        Args:
            callback: 시작 시 호출할 함수
        """
        if not self.auto_start_enabled:
            log.info("자동 시작이 비활성화되어 있습니다.")
            return
        
        now = datetime.now()
        
        # 오늘 자동 시작 시간
        target_time = now.replace(
            hour=self.auto_start_time.hour,
            minute=self.auto_start_time.minute,
            second=0,
            microsecond=0
        )
        
        # 이미 지났으면 다음 거래일
        if now >= target_time or self.is_holiday(now):
            next_day = now + timedelta(days=1)
            while self.is_holiday(next_day):
                next_day += timedelta(days=1)
            
            target_time = next_day.replace(
                hour=self.auto_start_time.hour,
                minute=self.auto_start_time.minute,
                second=0,
                microsecond=0
            )
        
        # 대기 시간 계산
        delta = target_time - now
        wait_ms = int(delta.total_seconds() * 1000)
        
        log.info(f"자동 시작 예약: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log.info(f"대기 시간: {int(delta.total_seconds() / 60)}분")
        
        # QTimer 설정
        if self.auto_start_timer:
            self.auto_start_timer.stop()
        
        self.auto_start_timer = QTimer()
        self.auto_start_timer.setSingleShot(True)
        self.auto_start_timer.timeout.connect(callback)
        self.auto_start_timer.start(wait_ms)
    
    def schedule_auto_stop(self, callback: Callable):
        """
        자동 종료 예약
        
        Args:
            callback: 종료 시 호출할 함수
        """
        now = datetime.now()
        
        # 오늘 자동 종료 시간
        target_time = now.replace(
            hour=self.auto_stop_time.hour,
            minute=self.auto_stop_time.minute,
            second=0,
            microsecond=0
        )
        
        # 이미 지났으면 예약 안 함
        if now >= target_time:
            log.info("오늘 자동 종료 시간이 이미 지났습니다.")
            return
        
        # 대기 시간 계산
        delta = target_time - now
        wait_ms = int(delta.total_seconds() * 1000)
        
        log.info(f"자동 종료 예약: {target_time.strftime('%H:%M:%S')}")
        log.info(f"대기 시간: {int(delta.total_seconds() / 60)}분")
        
        # QTimer 설정
        if self.auto_stop_timer:
            self.auto_stop_timer.stop()
        
        self.auto_stop_timer = QTimer()
        self.auto_stop_timer.setSingleShot(True)
        self.auto_stop_timer.timeout.connect(callback)
        self.auto_stop_timer.start(wait_ms)
    
    def cancel_scheduled_tasks(self):
        """예약된 작업 취소"""
        if self.auto_start_timer:
            self.auto_start_timer.stop()
            self.auto_start_timer = None
            log.info("자동 시작 예약 취소")
        
        if self.auto_stop_timer:
            self.auto_stop_timer.stop()
            self.auto_stop_timer = None
            log.info("자동 종료 예약 취소")
    
    def print_market_status(self):
        """시장 상태 출력"""
        state = self.get_current_market_state()
        now = datetime.now()
        
        print("=" * 60)
        print("📊 시장 상태")
        print("=" * 60)
        print(f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"시장 상태: {state.value}")
        print(f"매매 가능: {'예' if self.is_trading_allowed() else '아니오'}")
        
        if state in [MarketState.CLOSED, MarketState.WEEKEND, MarketState.HOLIDAY]:
            minutes_until_open = self.get_time_until_market_open()
            hours = minutes_until_open // 60
            mins = minutes_until_open % 60
            print(f"장 시작까지: {hours}시간 {mins}분")
        elif state == MarketState.OPEN:
            minutes_until_close = self.get_time_until_market_close()
            hours = minutes_until_close // 60
            mins = minutes_until_close % 60
            print(f"장 마감까지: {hours}시간 {mins}분")
        
        print("=" * 60)


# 테스트 코드
if __name__ == "__main__":
    scheduler = MarketScheduler()
    scheduler.print_market_status()
    
    # 상태별 테스트
    print("\n테스트 결과:")
    print(f"주말 여부: {scheduler.is_holiday()}")
    print(f"거래 가능: {scheduler.is_trading_allowed()}")
    print(f"장 시작까지: {scheduler.get_time_until_market_open()}분")

