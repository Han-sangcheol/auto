"""
자동 시작/종료 스케줄러 모듈

Windows 작업 스케줄러와 연동하여 프로그램을 자동으로 시작/종료합니다.

주요 기능:
- 장 시작/종료 시간 체크
- 자동 종료 스케줄링
- 공휴일 감지 (선택적)
- 실행 시간 로깅
"""

import sys
import time
import threading
from datetime import datetime, time as dt_time
from typing import Optional, Callable
from logger import log


class TradingScheduler:
    """
    자동매매 스케줄러 클래스
    
    장 시작/종료 시간을 체크하고 자동으로 프로그램을 종료합니다.
    """
    
    # 거래 시간 설정 (한국 주식 시장)
    MARKET_OPEN_TIME = dt_time(9, 0)      # 09:00
    MARKET_CLOSE_TIME = dt_time(15, 30)   # 15:30
    AUTO_START_TIME = dt_time(8, 30)      # 08:30 (자동 시작)
    AUTO_STOP_TIME = dt_time(16, 0)       # 16:00 (자동 종료)
    
    def __init__(
        self,
        enable_auto_shutdown: bool = True,
        shutdown_callback: Optional[Callable] = None
    ):
        """
        초기화
        
        Args:
            enable_auto_shutdown: 자동 종료 활성화 여부
            shutdown_callback: 종료 전 호출할 콜백 함수
        """
        self.enable_auto_shutdown = enable_auto_shutdown
        self.shutdown_callback = shutdown_callback
        self.is_running = False
        self.scheduler_thread = None
        
        log.info(f"자동매매 스케줄러 초기화 (자동 종료: {self.enable_auto_shutdown})")
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            log.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        log.success("자동매매 스케줄러 시작")
    
    def stop(self):
        """스케줄러 중지"""
        if self.is_running:
            self.is_running = False
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            log.info("자동매매 스케줄러 중지")
    
    def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        log.info("스케줄러 루프 시작")
        
        while self.is_running:
            try:
                current_time = datetime.now().time()
                
                # 1분마다 체크
                if self.enable_auto_shutdown:
                    # 자동 종료 시간 체크
                    if current_time >= self.AUTO_STOP_TIME:
                        log.warning(f"자동 종료 시간 도달 ({self.AUTO_STOP_TIME})")
                        self._execute_shutdown()
                        break
                
                time.sleep(60)  # 1분마다 체크
                
            except Exception as e:
                log.error(f"스케줄러 루프 오류: {e}")
                time.sleep(60)
    
    def _execute_shutdown(self):
        """자동 종료 실행"""
        log.warning("=" * 70)
        log.warning("🛑 자동 종료 시작")
        log.warning("=" * 70)
        
        try:
            # 종료 콜백 실행 (매매 엔진 정리)
            if self.shutdown_callback:
                log.info("종료 전 콜백 실행 중...")
                self.shutdown_callback()
            
            log.success("자동 종료 완료. 프로그램을 종료합니다.")
            time.sleep(2)
            
            # 프로그램 종료
            sys.exit(0)
            
        except Exception as e:
            log.error(f"자동 종료 중 오류: {e}")
            sys.exit(1)
    
    @staticmethod
    def is_market_hours() -> bool:
        """
        현재 시간이 시장 거래 시간인지 확인
        
        Returns:
            거래 시간 여부
        """
        current_time = datetime.now().time()
        is_weekday = datetime.now().weekday() < 5  # 월~금 (0~4)
        
        return (
            is_weekday and
            TradingScheduler.MARKET_OPEN_TIME <= current_time <= TradingScheduler.MARKET_CLOSE_TIME
        )
    
    @staticmethod
    def is_before_market_open() -> bool:
        """
        시장 개장 전인지 확인
        
        Returns:
            개장 전 여부
        """
        current_time = datetime.now().time()
        is_weekday = datetime.now().weekday() < 5
        
        return is_weekday and current_time < TradingScheduler.MARKET_OPEN_TIME
    
    @staticmethod
    def is_after_market_close() -> bool:
        """
        시장 마감 후인지 확인
        
        Returns:
            마감 후 여부
        """
        current_time = datetime.now().time()
        is_weekday = datetime.now().weekday() < 5
        
        return is_weekday and current_time > TradingScheduler.MARKET_CLOSE_TIME
    
    @staticmethod
    def get_market_status() -> str:
        """
        현재 시장 상태 반환
        
        Returns:
            시장 상태 문자열
        """
        now = datetime.now()
        current_time = now.time()
        is_weekday = now.weekday() < 5
        
        if not is_weekday:
            return "주말 (휴장)"
        
        if current_time < TradingScheduler.MARKET_OPEN_TIME:
            return "개장 전"
        elif current_time < TradingScheduler.MARKET_CLOSE_TIME:
            return "거래 중"
        else:
            return "마감 후"
    
    @staticmethod
    def print_schedule_info():
        """스케줄 정보 출력"""
        log.info("=" * 70)
        log.info("📅 자동매매 스케줄 정보")
        log.info("=" * 70)
        log.info(f"  자동 시작 시간: {TradingScheduler.AUTO_START_TIME}")
        log.info(f"  시장 개장 시간: {TradingScheduler.MARKET_OPEN_TIME}")
        log.info(f"  시장 마감 시간: {TradingScheduler.MARKET_CLOSE_TIME}")
        log.info(f"  자동 종료 시간: {TradingScheduler.AUTO_STOP_TIME}")
        log.info(f"  현재 시장 상태: {TradingScheduler.get_market_status()}")
        log.info("=" * 70)


if __name__ == "__main__":
    """테스트 코드"""
    
    # 스케줄 정보 출력
    TradingScheduler.print_schedule_info()
    
    print("\n시장 시간 체크:")
    print(f"  - 거래 시간: {TradingScheduler.is_market_hours()}")
    print(f"  - 개장 전: {TradingScheduler.is_before_market_open()}")
    print(f"  - 마감 후: {TradingScheduler.is_after_market_close()}")
    print(f"  - 현재 상태: {TradingScheduler.get_market_status()}")
    
    print("\n스케줄러 테스트 (10초 후 종료):")
    
    # 테스트용 종료 콜백
    def test_callback():
        print("종료 전 콜백 실행됨!")
    
    # 테스트용 스케줄러 (10초 후 종료)
    original_stop_time = TradingScheduler.AUTO_STOP_TIME
    TradingScheduler.AUTO_STOP_TIME = dt_time(
        datetime.now().hour,
        datetime.now().minute,
        datetime.now().second + 10
    )
    
    scheduler = TradingScheduler(
        enable_auto_shutdown=True,
        shutdown_callback=test_callback
    )
    
    scheduler.start()
    
    print("스케줄러가 실행되었습니다. 10초 후 자동 종료됩니다...")
    print("(Ctrl+C로 중단 가능)")
    
    try:
        while scheduler.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n수동 중단됨")
        scheduler.stop()
    
    # 원래 시간으로 복구
    TradingScheduler.AUTO_STOP_TIME = original_stop_time

