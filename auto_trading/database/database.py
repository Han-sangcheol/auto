"""
데이터베이스 모듈

[파일 역할]
주식 가격 데이터를 DuckDB + Parquet 형식으로 저장하고 조회합니다.
고성능 시계열 데이터베이스로 대용량 데이터를 효율적으로 관리합니다.

[주요 기능]
- 1분봉 OHLCV 데이터 저장 및 조회
- 일별 Parquet 파일 파티션
- 빠른 시계열 쿼리 (시간 범위, 종목별)
- 자동 압축 및 백업
- 통계 및 분석 쿼리

[사용 방법]
from database import StockDatabase

db = StockDatabase()
db.save_candle('005930', datetime.now(), 75000, 75500, 74800, 75300, 1000000)
candles = db.get_candles('005930', start_date, end_date)
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import csv

from utils.logger import log


class StockDatabase:
    """
    주식 가격 데이터베이스 클래스
    
    SQLite를 사용하여 시계열 데이터를 효율적으로 저장하고 조회합니다.
    32비트/64비트 Python 모두 지원합니다.
    """
    
    def __init__(self, db_path: str = "data/stocks.db", parquet_dir: str = "data/parquet"):
        """
        Args:
            db_path: SQLite 데이터베이스 파일 경로
            parquet_dir: CSV 파일 저장 디렉토리 (Parquet 대신 CSV 사용)
        """
        self.db_path = db_path
        self.parquet_dir = parquet_dir
        self.enabled = True
        
        # 디렉토리 생성
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(parquet_dir).mkdir(parents=True, exist_ok=True)
        
        # 백업 디렉토리
        self.backup_dir = os.path.join(parquet_dir, "backups")
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # 스레드 로컬 연결 (멀티스레드 지원)
        self._local = threading.local()
        
        # 테이블 초기화
        self._init_tables()
        
        log.success(f"✅ 데이터베이스 초기화 완료: {db_path}")
    
    def _get_connection(self):
        """스레드별 독립적인 SQLite 연결 반환"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            # Row factory 설정 (딕셔너리처럼 접근 가능)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_tables(self):
        """테이블 생성 및 인덱스 설정"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # OHLCV 1분봉 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                stock_code TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                date TEXT NOT NULL,
                PRIMARY KEY (stock_code, timestamp)
            )
        """)
        
        # 인덱스 생성 (쿼리 성능 향상)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candles_stock_date ON candles(stock_code, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candles_timestamp ON candles(timestamp)")
        
        conn.commit()
        log.info("데이터베이스 테이블 초기화 완료")
    
    def save_candle(
        self,
        stock_code: str,
        timestamp: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: int
    ) -> bool:
        """
        1분봉 데이터 저장
        
        Args:
            stock_code: 종목 코드
            timestamp: 시간 (분 단위)
            open_price: 시가
            high: 고가
            low: 저가
            close: 종가
            volume: 거래량
            
        Returns:
            저장 성공 여부
        """
        if not self.enabled:
            return False
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            date = timestamp.strftime('%Y-%m-%d')
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # INSERT OR REPLACE (중복 시 업데이트)
            cursor.execute("""
                INSERT OR REPLACE INTO candles 
                (stock_code, timestamp, open, high, low, close, volume, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (stock_code, timestamp_str, open_price, high, low, close, volume, date))
            
            conn.commit()
            return True
            
        except Exception as e:
            log.error(f"1분봉 저장 오류 ({stock_code}): {e}")
            return False
    
    def save_candles_batch(self, candles: List[Dict]) -> int:
        """
        여러 1분봉 데이터를 배치로 저장 (고성능)
        
        Args:
            candles: 1분봉 데이터 리스트
                    [{'stock_code': str, 'timestamp': datetime, 'open': float, ...}, ...]
        
        Returns:
            저장된 레코드 수
        """
        if not self.enabled or not candles:
            return 0
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 배치 삽입 (매우 빠름)
            data = []
            for candle in candles:
                timestamp_str = candle['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                date_str = candle['timestamp'].strftime('%Y-%m-%d')
                data.append((
                    candle['stock_code'],
                    timestamp_str,
                    candle['open'],
                    candle['high'],
                    candle['low'],
                    candle['close'],
                    candle['volume'],
                    date_str
                ))
            
            cursor.executemany("""
                INSERT OR REPLACE INTO candles 
                (stock_code, timestamp, open, high, low, close, volume, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            
            conn.commit()
            log.debug(f"배치 저장 완료: {len(candles)}개")
            return len(candles)
            
        except Exception as e:
            log.error(f"배치 저장 오류: {e}")
            return 0
    
    def get_candles(
        self,
        stock_code: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        특정 기간의 1분봉 데이터 조회
        
        Args:
            stock_code: 종목 코드
            start_date: 시작 시간
            end_date: 종료 시간
            
        Returns:
            1분봉 데이터 리스트
        """
        if not self.enabled:
            return []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT stock_code, timestamp, open, high, low, close, volume
                FROM candles
                WHERE stock_code = ?
                  AND timestamp >= ?
                  AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (stock_code, start_str, end_str))
            
            candles = []
            for row in cursor.fetchall():
                candles.append({
                    'stock_code': row[0],
                    'timestamp': datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'),
                    'open': row[2],
                    'high': row[3],
                    'low': row[4],
                    'close': row[5],
                    'volume': row[6]
                })
            
            return candles
            
        except Exception as e:
            log.error(f"1분봉 조회 오류 ({stock_code}): {e}")
            return []
    
    def get_latest_candle(self, stock_code: str) -> Optional[Dict]:
        """
        최신 1분봉 데이터 조회
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            최신 1분봉 데이터 또는 None
        """
        if not self.enabled:
            return None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT stock_code, timestamp, open, high, low, close, volume
                FROM candles
                WHERE stock_code = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (stock_code,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'stock_code': result[0],
                    'timestamp': datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S'),
                    'open': result[2],
                    'high': result[3],
                    'low': result[4],
                    'close': result[5],
                    'volume': result[6]
                }
            
            return None
            
        except Exception as e:
            log.error(f"최신 1분봉 조회 오류 ({stock_code}): {e}")
            return None
    
    def get_latest_price(self, stock_code: str) -> Optional[float]:
        """
        최신 종가 조회
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            최신 종가 또는 None
        """
        candle = self.get_latest_candle(stock_code)
        return candle['close'] if candle else None
    
    def get_stock_list(self) -> List[str]:
        """
        저장된 종목 코드 목록 조회
        
        Returns:
            종목 코드 리스트
        """
        if not self.enabled:
            return []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT stock_code
                FROM candles
                ORDER BY stock_code
            """)
            
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            log.error(f"종목 목록 조회 오류: {e}")
            return []
    
    def get_statistics(self, stock_code: str, days: int = 7) -> Optional[Dict]:
        """
        종목 통계 조회
        
        Args:
            stock_code: 종목 코드
            days: 통계 기간 (일)
            
        Returns:
            통계 정보 딕셔너리
        """
        if not self.enabled:
            return None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            start_date = datetime.now() - timedelta(days=days)
            start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as candle_count,
                    MIN(low) as min_price,
                    MAX(high) as max_price,
                    AVG(close) as avg_price,
                    SUM(volume) as total_volume,
                    MIN(timestamp) as first_time,
                    MAX(timestamp) as last_time
                FROM candles
                WHERE stock_code = ?
                  AND timestamp >= ?
            """, (stock_code, start_str))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                return {
                    'stock_code': stock_code,
                    'candle_count': result[0],
                    'min_price': result[1],
                    'max_price': result[2],
                    'avg_price': result[3],
                    'total_volume': result[4],
                    'first_time': datetime.strptime(result[5], '%Y-%m-%d %H:%M:%S'),
                    'last_time': datetime.strptime(result[6], '%Y-%m-%d %H:%M:%S'),
                    'days': days
                }
            
            return None
            
        except Exception as e:
            log.error(f"통계 조회 오류 ({stock_code}): {e}")
            return None
    
    def export_to_csv(self, stock_code: str, date: datetime.date) -> bool:
        """
        특정 날짜의 데이터를 CSV 파일로 내보내기
        
        Args:
            stock_code: 종목 코드
            date: 날짜
            
        Returns:
            내보내기 성공 여부
        """
        if not self.enabled:
            return False
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 월별 폴더 생성
            month_dir = os.path.join(self.parquet_dir, date.strftime("%Y-%m"))
            Path(month_dir).mkdir(parents=True, exist_ok=True)
            
            # CSV 파일 경로
            filename = f"{stock_code}_{date.strftime('%Y-%m-%d')}.csv"
            filepath = os.path.join(month_dir, filename)
            
            # CSV로 내보내기
            date_str = date.strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT stock_code, timestamp, open, high, low, close, volume
                FROM candles
                WHERE stock_code = ?
                  AND date = ?
                ORDER BY timestamp
            """, (stock_code, date_str))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['stock_code', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
                writer.writerows(cursor.fetchall())
            
            log.info(f"CSV 내보내기 완료: {filepath}")
            return True
            
        except Exception as e:
            log.error(f"CSV 내보내기 오류 ({stock_code}, {date}): {e}")
            return False
    
    def cleanup_old_data(self, days: int) -> int:
        """
        오래된 데이터 삭제
        
        Args:
            days: 보관 기간 (일). 이보다 오래된 데이터 삭제
            
        Returns:
            삭제된 레코드 수
        """
        if not self.enabled or days <= 0:
            return 0
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                DELETE FROM candles
                WHERE timestamp < ?
            """, (cutoff_str,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                log.info(f"오래된 데이터 삭제 완료: {deleted_count}개 ({days}일 이전)")
            
            return deleted_count
            
        except Exception as e:
            log.error(f"데이터 삭제 오류: {e}")
            return 0
    
    def vacuum(self):
        """데이터베이스 최적화 (공간 회수)"""
        if not self.enabled:
            return
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            conn.commit()
            log.info("데이터베이스 최적화 완료")
        except Exception as e:
            log.error(f"데이터베이스 최적화 오류: {e}")
    
    def close(self):
        """데이터베이스 연결 종료"""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            try:
                self._local.conn.close()
                self._local.conn = None
                log.info("데이터베이스 연결 종료")
            except:
                pass
    
    def __del__(self):
        """소멸자"""
        self.close()


# 싱글톤 인스턴스 (전역 접근용)
_db_instance: Optional[StockDatabase] = None


def get_database() -> StockDatabase:
    """
    데이터베이스 싱글톤 인스턴스 반환
    
    Returns:
        StockDatabase 인스턴스
    """
    global _db_instance
    
    if _db_instance is None:
        _db_instance = StockDatabase()
    
    return _db_instance


if __name__ == "__main__":
    # 테스트 코드
    print("=" * 70)
    print("StockDatabase 테스트")
    print("=" * 70)
    
    # 테스트용 데이터베이스
    db = StockDatabase("data/test_stocks.db", "data/test_csv")
    
    # 1. 데이터 저장 테스트
    print("\n1. 1분봉 데이터 저장 테스트...")
    now = datetime.now().replace(second=0, microsecond=0)
    
    test_data = []
    for i in range(10):
        timestamp = now - timedelta(minutes=i)
        candle = {
            'stock_code': '005930',
            'timestamp': timestamp,
            'open': 75000 + i * 100,
            'high': 75500 + i * 100,
            'low': 74800 + i * 100,
            'close': 75300 + i * 100,
            'volume': 1000000 + i * 10000
        }
        test_data.append(candle)
    
    saved_count = db.save_candles_batch(test_data)
    print(f"   저장 완료: {saved_count}개")
    
    # 2. 데이터 조회 테스트
    print("\n2. 1분봉 데이터 조회 테스트...")
    start_date = now - timedelta(minutes=20)
    end_date = now
    
    candles = db.get_candles('005930', start_date, end_date)
    print(f"   조회 완료: {len(candles)}개")
    if candles:
        print(f"   최신: {candles[-1]['timestamp']} / {candles[-1]['close']:,}원")
    
    # 3. 최신 가격 조회 테스트
    print("\n3. 최신 가격 조회 테스트...")
    latest_price = db.get_latest_price('005930')
    print(f"   최신 가격: {latest_price:,}원" if latest_price else "   데이터 없음")
    
    # 4. 통계 조회 테스트
    print("\n4. 통계 조회 테스트...")
    stats = db.get_statistics('005930', days=1)
    if stats:
        print(f"   1분봉 개수: {stats['candle_count']}개")
        print(f"   최저가: {stats['min_price']:,}원")
        print(f"   최고가: {stats['max_price']:,}원")
        print(f"   평균가: {stats['avg_price']:,.0f}원")
        print(f"   총 거래량: {stats['total_volume']:,}")
    
    # 5. 종목 목록 조회
    print("\n5. 저장된 종목 목록...")
    stocks = db.get_stock_list()
    print(f"   종목: {', '.join(stocks)}")
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)

