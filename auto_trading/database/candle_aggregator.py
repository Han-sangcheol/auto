"""
1분봉 집계 모듈

[파일 역할]
실시간 틱 데이터를 받아서 1분봉(OHLCV)으로 집계하고 데이터베이스에 저장합니다.

[주요 기능]
- 실시간 틱 데이터 수신 및 집계
- 1분마다 자동으로 1분봉 생성
- 데이터베이스에 배치 저장
- 종목별 독립적인 집계

[사용 방법]
from candle_aggregator import CandleAggregator
from database import StockDatabase

db = StockDatabase()
aggregator = CandleAggregator(db)
aggregator.on_tick('005930', 75000, 1000)
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict
import threading

from PyQt5.QtCore import QTimer

from logger import log


class Candle:
    """1분봉 데이터 클래스"""
    
    def __init__(self, stock_code: str, timestamp: datetime):
        """
        Args:
            stock_code: 종목 코드
            timestamp: 1분봉 시작 시간 (초, 마이크로초는 0)
        """
        self.stock_code = stock_code
        self.timestamp = timestamp.replace(second=0, microsecond=0)
        
        # OHLCV
        self.open: Optional[float] = None
        self.high: Optional[float] = None
        self.low: Optional[float] = None
        self.close: Optional[float] = None
        self.volume: int = 0
        
        # 틱 카운트
        self.tick_count = 0
    
    def update(self, price: float, volume: int = 0):
        """
        새로운 틱 데이터로 1분봉 업데이트
        
        Args:
            price: 현재가
            volume: 거래량 (누적)
        """
        if self.open is None:
            # 첫 틱
            self.open = price
            self.high = price
            self.low = price
            self.close = price
        else:
            # 고가/저가/종가 업데이트
            self.high = max(self.high, price)
            self.low = min(self.low, price)
            self.close = price
        
        self.volume = volume
        self.tick_count += 1
    
    def is_complete(self) -> bool:
        """1분봉이 완성되었는지 확인 (최소 1개 틱 필요)"""
        return self.open is not None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'stock_code': self.stock_code,
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }
    
    def __repr__(self):
        return (
            f"Candle({self.stock_code}, {self.timestamp.strftime('%H:%M')}, "
            f"O:{self.open} H:{self.high} L:{self.low} C:{self.close} V:{self.volume})"
        )


class CandleAggregator:
    """
    실시간 틱 데이터를 1분봉으로 집계하는 클래스
    
    틱 데이터를 받아서 1분 단위로 OHLCV를 계산하고
    1분이 끝나면 자동으로 데이터베이스에 저장합니다.
    """
    
    def __init__(self, database, flush_interval_ms: int = 60000):
        """
        Args:
            database: StockDatabase 인스턴스
            flush_interval_ms: 플러시 간격 (밀리초, 기본 60000 = 1분)
        """
        self.database = database
        self.flush_interval_ms = flush_interval_ms
        
        # 종목별 현재 진행 중인 1분봉
        self.current_candles: Dict[str, Candle] = {}
        
        # 저장 대기 중인 1분봉 (플러시 전까지 버퍼)
        self.pending_candles: list = []
        
        # 통계
        self.total_ticks = 0
        self.total_candles_saved = 0
        
        # 스레드 안전성
        self.lock = threading.Lock()
        
        # 1분마다 자동 플러시 타이머
        self.timer = QTimer()
        self.timer.timeout.connect(self._flush_candles)
        self.timer.start(flush_interval_ms)
        
        log.info(f"CandleAggregator 초기화 완료 (플러시 간격: {flush_interval_ms/1000:.0f}초)")
    
    def on_tick(self, stock_code: str, price: float, volume: int = 0):
        """
        실시간 틱 데이터 수신
        
        Args:
            stock_code: 종목 코드
            price: 현재가
            volume: 거래량 (누적)
        """
        with self.lock:
            now = datetime.now()
            candle_time = now.replace(second=0, microsecond=0)
            
            # 현재 1분봉 가져오기 또는 생성
            if stock_code not in self.current_candles:
                self.current_candles[stock_code] = Candle(stock_code, candle_time)
            
            candle = self.current_candles[stock_code]
            
            # 1분이 지나서 새로운 분이 시작된 경우
            if candle.timestamp != candle_time:
                # 이전 1분봉을 저장 대기열에 추가
                if candle.is_complete():
                    self.pending_candles.append(candle.to_dict())
                
                # 새로운 1분봉 시작
                self.current_candles[stock_code] = Candle(stock_code, candle_time)
                candle = self.current_candles[stock_code]
            
            # 현재 1분봉 업데이트
            candle.update(price, volume)
            self.total_ticks += 1
    
    def _flush_candles(self):
        """
        대기 중인 1분봉을 데이터베이스에 저장
        
        1분마다 타이머에 의해 자동 호출됩니다.
        """
        with self.lock:
            if not self.pending_candles:
                return
            
            # 데이터베이스에 배치 저장
            if self.database and self.database.enabled:
                saved_count = self.database.save_candles_batch(self.pending_candles)
                
                if saved_count > 0:
                    self.total_candles_saved += saved_count
                    log.debug(
                        f"1분봉 저장: {saved_count}개 "
                        f"(총 {self.total_candles_saved}개, 틱 {self.total_ticks}개)"
                    )
                
                # 저장 완료된 1분봉 제거
                self.pending_candles.clear()
            else:
                log.warning("데이터베이스가 비활성화되어 1분봉을 저장할 수 없습니다.")
    
    def force_flush(self):
        """
        즉시 플러시 (프로그램 종료 시 사용)
        
        진행 중인 1분봉도 포함하여 모두 저장합니다.
        """
        with self.lock:
            # 진행 중인 1분봉도 저장
            for stock_code, candle in self.current_candles.items():
                if candle.is_complete():
                    self.pending_candles.append(candle.to_dict())
            
            # 모두 저장
            self._flush_candles()
            
            log.info("강제 플러시 완료")
    
    def get_current_candle(self, stock_code: str) -> Optional[Candle]:
        """
        현재 진행 중인 1분봉 조회
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            현재 1분봉 또는 None
        """
        with self.lock:
            return self.current_candles.get(stock_code)
    
    def get_statistics(self) -> Dict:
        """
        집계 통계 반환
        
        Returns:
            통계 정보 딕셔너리
        """
        with self.lock:
            return {
                'total_ticks': self.total_ticks,
                'total_candles_saved': self.total_candles_saved,
                'pending_candles': len(self.pending_candles),
                'active_stocks': len(self.current_candles),
                'stocks': list(self.current_candles.keys())
            }
    
    def stop(self):
        """
        집계기 중지 및 데이터 저장
        
        프로그램 종료 시 호출하여 모든 데이터를 저장합니다.
        """
        log.info("CandleAggregator 중지 중...")
        
        # 타이머 중지
        self.timer.stop()
        
        # 모든 데이터 저장
        self.force_flush()
        
        log.info("CandleAggregator 중지 완료")
    
    def __del__(self):
        """소멸자 - 타이머 정리"""
        if hasattr(self, 'timer'):
            self.timer.stop()


if __name__ == "__main__":
    # 테스트 코드
    import time
    from database import StockDatabase
    from PyQt5.QtWidgets import QApplication
    import sys
    
    print("=" * 70)
    print("CandleAggregator 테스트")
    print("=" * 70)
    
    # Qt 애플리케이션 (QTimer 사용을 위해 필요)
    app = QApplication(sys.argv)
    
    # 테스트용 데이터베이스
    db = StockDatabase("data/test_stocks.duckdb", "data/test_parquet")
    
    if not db.enabled:
        print("DuckDB가 설치되지 않았습니다.")
        exit(1)
    
    # 집계기 생성 (테스트를 위해 5초마다 플러시)
    aggregator = CandleAggregator(db, flush_interval_ms=5000)
    
    print("\n1. 틱 데이터 전송 중...")
    
    # 10초 동안 틱 데이터 전송
    start_time = time.time()
    tick_count = 0
    
    def send_ticks():
        global tick_count
        import random
        
        # 삼성전자 틱 데이터 시뮬레이션
        base_price = 75000
        price = base_price + random.randint(-500, 500)
        volume = 1000000 + random.randint(-10000, 10000)
        
        aggregator.on_tick('005930', price, volume)
        tick_count += 1
        
        if time.time() - start_time < 10:
            QTimer.singleShot(100, send_ticks)  # 0.1초마다
        else:
            # 테스트 종료
            print(f"   총 {tick_count}개 틱 전송 완료")
            
            # 통계 출력
            print("\n2. 집계 통계:")
            stats = aggregator.get_statistics()
            print(f"   총 틱: {stats['total_ticks']}개")
            print(f"   저장된 1분봉: {stats['total_candles_saved']}개")
            print(f"   대기 중: {stats['pending_candles']}개")
            print(f"   활성 종목: {stats['active_stocks']}개")
            
            # 현재 1분봉 확인
            print("\n3. 현재 진행 중인 1분봉:")
            candle = aggregator.get_current_candle('005930')
            if candle:
                print(f"   {candle}")
            
            # 강제 플러시
            print("\n4. 강제 플러시...")
            aggregator.force_flush()
            
            # DB에서 조회
            print("\n5. 데이터베이스 조회:")
            start_date = datetime.now() - timedelta(minutes=10)
            end_date = datetime.now()
            candles = db.get_candles('005930', start_date, end_date)
            print(f"   조회된 1분봉: {len(candles)}개")
            
            if candles:
                for c in candles[-3:]:  # 최근 3개
                    print(f"   {c['timestamp'].strftime('%H:%M')} - "
                          f"O:{c['open']:,.0f} H:{c['high']:,.0f} "
                          f"L:{c['low']:,.0f} C:{c['close']:,.0f} "
                          f"V:{c['volume']:,}")
            
            print("\n" + "=" * 70)
            print("테스트 완료!")
            print("=" * 70)
            
            # 앱 종료
            QTimer.singleShot(1000, app.quit)
    
    # 틱 전송 시작
    QTimer.singleShot(100, send_ticks)
    
    # 이벤트 루프 실행
    sys.exit(app.exec_())

