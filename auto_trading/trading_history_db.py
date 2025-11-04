"""
매매 이력 블랙박스 데이터베이스 모듈

[파일 역할]
모든 매매 거래를 상세하게 기록하는 블랙박스 시스템입니다.

[주요 기능]
- 거래 기록 (매수/매도)
- 포지션 추적 (진입/청산)
- 시장 스냅샷 기록
- 전략 신호 기록
- 일일 요약 통계
- CSV/JSON 내보내기
- 데이터베이스 백업

[테이블 구조]
- trades: 거래 기록
- positions: 포지션 기록
- market_snapshots: 시장 스냅샷
- strategy_signals: 전략 신호
- daily_summary: 일일 요약

[사용 방법]
from trading_history_db import TradingHistoryDB
db = TradingHistoryDB("trading_history.db")
trade_id = db.record_trade({...})
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from loguru import logger as log


class TradingHistoryDB:
    """
    매매 이력 블랙박스 데이터베이스
    
    모든 거래, 포지션, 시장 상황을 영구 기록하여
    프로그램 개선 및 성과 분석에 활용합니다.
    """
    
    def __init__(self, db_path: str = "trading_history.db"):
        """
        데이터베이스 초기화 및 테이블 생성
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.conn = None
        
        try:
            # 데이터베이스 연결
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            
            # 테이블 생성
            self._create_tables()
            
            log.success(f"📦 거래 이력 블랙박스 초기화 완료: {db_path}")
            
        except Exception as e:
            log.error(f"❌ 거래 이력 DB 초기화 실패: {e}")
            raise
    
    def _create_tables(self):
        """모든 테이블 생성"""
        cursor = self.conn.cursor()
        
        # 1. trades 테이블 (거래 기록)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                total_amount INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                order_id TEXT,
                account_number TEXT,
                reason TEXT,
                signal_strength REAL,
                position_id INTEGER,
                FOREIGN KEY (position_id) REFERENCES positions(position_id)
            )
        """)
        
        # 2. positions 테이블 (포지션 기록)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                entry_price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                total_invested INTEGER NOT NULL,
                average_down_count INTEGER DEFAULT 0,
                average_down_prices TEXT,
                exit_time TEXT,
                exit_price INTEGER,
                exit_reason TEXT,
                profit_loss INTEGER,
                profit_loss_percent REAL,
                holding_duration_seconds INTEGER,
                status TEXT NOT NULL,
                entry_config TEXT,
                exit_config TEXT,
                sell_blocked INTEGER DEFAULT 0
            )
        """)
        
        # 🆕 기존 테이블에 sell_blocked 컬럼 추가 (마이그레이션)
        try:
            cursor.execute("ALTER TABLE positions ADD COLUMN sell_blocked INTEGER DEFAULT 0")
            self.conn.commit()
            log.info("✅ positions 테이블에 sell_blocked 컬럼 추가")
        except sqlite3.OperationalError:
            # 이미 컬럼이 존재하는 경우
            pass
        
        # 3. market_snapshots 테이블 (시장 스냅샷)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                position_id INTEGER,
                market_state TEXT,
                total_balance INTEGER,
                total_asset INTEGER,
                available_cash INTEGER,
                stock_code TEXT,
                current_price INTEGER,
                change_rate REAL,
                volume INTEGER,
                FOREIGN KEY (position_id) REFERENCES positions(position_id)
            )
        """)
        
        # 4. strategy_signals 테이블 (전략 신호 기록)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_signals (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                signal_strength REAL,
                strategy_scores TEXT,
                news_score INTEGER,
                news_count INTEGER,
                latest_news TEXT,
                executed BOOLEAN,
                execution_reason TEXT,
                trade_id INTEGER,
                FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
            )
        """)
        
        # 5. daily_summary 테이블 (일일 요약)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_trades INTEGER,
                buy_count INTEGER,
                sell_count INTEGER,
                total_profit_loss INTEGER,
                win_count INTEGER,
                loss_count INTEGER,
                win_rate REAL,
                avg_profit_loss_percent REAL,
                avg_holding_duration_seconds INTEGER,
                final_balance INTEGER,
                final_total_asset INTEGER
            )
        """)
        
        # 인덱스 생성 (성능 최적화)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_stock ON trades(stock_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_stock ON positions(stock_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON strategy_signals(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_summary(date)")
        
        self.conn.commit()
        log.debug("✅ 데이터베이스 테이블 생성 완료")
    
    def record_trade(self, trade_data: dict) -> int:
        """
        거래 기록
        
        Args:
            trade_data: 거래 정보 딕셔너리
                - stock_code: 종목 코드
                - stock_name: 종목명
                - trade_type: 'BUY' or 'SELL'
                - quantity: 수량
                - price: 가격
                - total_amount: 총 금액
                - timestamp: 시간 (ISO 형식)
                - order_id: 주문 번호 (선택)
                - account_number: 계좌 번호 (선택)
                - reason: 거래 사유 (선택)
                - signal_strength: 신호 강도 (선택)
                - position_id: 관련 포지션 ID (선택)
        
        Returns:
            trade_id: 생성된 거래 ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO trades (
                    stock_code, stock_name, trade_type, quantity, price,
                    total_amount, timestamp, order_id, account_number,
                    reason, signal_strength, position_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data['stock_code'],
                trade_data['stock_name'],
                trade_data['trade_type'],
                trade_data['quantity'],
                trade_data['price'],
                trade_data['total_amount'],
                trade_data['timestamp'],
                trade_data.get('order_id'),
                trade_data.get('account_number'),
                trade_data.get('reason'),
                trade_data.get('signal_strength'),
                trade_data.get('position_id')
            ))
            self.conn.commit()
            
            trade_id = cursor.lastrowid
            log.debug(f"📝 거래 기록: {trade_data['trade_type']} {trade_data['stock_name']} (ID: {trade_id})")
            
            return trade_id
            
        except Exception as e:
            log.error(f"❌ 거래 기록 실패: {e}")
            self.conn.rollback()
            return -1
    
    def start_position(self, position_data: dict) -> int:
        """
        포지션 시작 (매수)
        
        Args:
            position_data: 포지션 정보 딕셔너리
                - stock_code: 종목 코드
                - stock_name: 종목명
                - entry_time: 진입 시간 (ISO 형식)
                - entry_price: 진입 가격
                - quantity: 수량
                - total_invested: 총 투자 금액
                - entry_config: 진입 시점 설정값 (JSON 문자열)
                - sell_blocked: 매도 금지 여부 (0 또는 1, 선택적)
        
        Returns:
            position_id: 생성된 포지션 ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO positions (
                    stock_code, stock_name, entry_time, entry_price,
                    quantity, total_invested, status, entry_config, sell_blocked
                ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
            """, (
                position_data['stock_code'],
                position_data['stock_name'],
                position_data['entry_time'],
                position_data['entry_price'],
                position_data['quantity'],
                position_data['total_invested'],
                position_data.get('entry_config'),
                position_data.get('sell_blocked', 0)
            ))
            self.conn.commit()
            
            position_id = cursor.lastrowid
            log.debug(f"📊 포지션 시작: {position_data['stock_name']} (ID: {position_id})")
            
            return position_id
            
        except Exception as e:
            log.error(f"❌ 포지션 시작 실패: {e}")
            self.conn.rollback()
            return -1
    
    def close_position(self, position_id: int, exit_data: dict):
        """
        포지션 종료 (매도)
        
        Args:
            position_id: 포지션 ID
            exit_data: 청산 정보 딕셔너리
                - exit_time: 청산 시간 (ISO 형식)
                - exit_price: 청산 가격
                - exit_reason: 청산 사유
                - profit_loss: 손익 (원)
                - profit_loss_percent: 손익률 (%)
                - holding_duration_seconds: 보유 기간 (초)
                - exit_config: 청산 시점 설정값 (JSON 문자열)
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE positions SET
                    exit_time = ?,
                    exit_price = ?,
                    exit_reason = ?,
                    profit_loss = ?,
                    profit_loss_percent = ?,
                    holding_duration_seconds = ?,
                    status = 'CLOSED',
                    exit_config = ?
                WHERE position_id = ?
            """, (
                exit_data['exit_time'],
                exit_data['exit_price'],
                exit_data['exit_reason'],
                exit_data['profit_loss'],
                exit_data['profit_loss_percent'],
                exit_data['holding_duration_seconds'],
                exit_data.get('exit_config'),
                position_id
            ))
            self.conn.commit()
            
            log.debug(f"📊 포지션 종료: ID {position_id} ({exit_data['exit_reason']})")
            
        except Exception as e:
            log.error(f"❌ 포지션 종료 실패: {e}")
            self.conn.rollback()
    
    def update_position(self, position_id: int, update_data: dict):
        """
        포지션 업데이트 (추가 매수 등)
        
        Args:
            position_id: 포지션 ID
            update_data: 업데이트 정보 딕셔너리
                - quantity: 새로운 수량
                - total_invested: 새로운 총 투자 금액
                - average_down_count: 추가 매수 횟수
                - average_down_prices: 추가 매수 가격 리스트 (JSON 문자열)
                - sell_blocked: 매도 금지 여부 (0 또는 1)
        """
        try:
            cursor = self.conn.cursor()
            
            # 업데이트할 필드만 동적으로 처리
            update_fields = []
            values = []
            
            if 'quantity' in update_data:
                update_fields.append("quantity = ?")
                values.append(update_data['quantity'])
            
            if 'total_invested' in update_data:
                update_fields.append("total_invested = ?")
                values.append(update_data['total_invested'])
            
            if 'average_down_count' in update_data:
                update_fields.append("average_down_count = ?")
                values.append(update_data['average_down_count'])
            
            if 'sell_blocked' in update_data:
                update_fields.append("sell_blocked = ?")
                values.append(1 if update_data['sell_blocked'] else 0)
            
            if 'average_down_prices' in update_data:
                update_fields.append("average_down_prices = ?")
                values.append(update_data['average_down_prices'])
            
            if update_fields:
                values.append(position_id)
                query = f"UPDATE positions SET {', '.join(update_fields)} WHERE position_id = ?"
                cursor.execute(query, values)
                self.conn.commit()
                
                log.debug(f"📊 포지션 업데이트: ID {position_id}")
            
        except Exception as e:
            log.error(f"❌ 포지션 업데이트 실패: {e}")
            self.conn.rollback()
    
    def record_market_snapshot(self, snapshot_data: dict):
        """
        시장 스냅샷 기록
        
        Args:
            snapshot_data: 스냅샷 정보 딕셔너리
                - timestamp: 시간 (ISO 형식)
                - position_id: 관련 포지션 ID (선택)
                - market_state: 시장 상태
                - total_balance: 총 잔고
                - total_asset: 총 자산
                - available_cash: 사용 가능 현금
                - stock_code: 종목 코드
                - current_price: 현재가
                - change_rate: 변동률
                - volume: 거래량
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO market_snapshots (
                    timestamp, position_id, market_state, total_balance,
                    total_asset, available_cash, stock_code, current_price,
                    change_rate, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_data['timestamp'],
                snapshot_data.get('position_id'),
                snapshot_data.get('market_state'),
                snapshot_data.get('total_balance'),
                snapshot_data.get('total_asset'),
                snapshot_data.get('available_cash'),
                snapshot_data.get('stock_code'),
                snapshot_data.get('current_price'),
                snapshot_data.get('change_rate'),
                snapshot_data.get('volume')
            ))
            self.conn.commit()
            
            log.debug(f"📸 시장 스냅샷 기록: {snapshot_data.get('stock_code', 'N/A')}")
            
        except Exception as e:
            log.error(f"❌ 시장 스냅샷 기록 실패: {e}")
            self.conn.rollback()
    
    def record_signal(self, signal_data: dict) -> int:
        """
        전략 신호 기록
        
        Args:
            signal_data: 신호 정보 딕셔너리
                - timestamp: 시간 (ISO 형식)
                - stock_code: 종목 코드
                - signal_type: 'BUY', 'SELL', 'HOLD'
                - signal_strength: 신호 강도
                - strategy_scores: 전략별 점수 (JSON 문자열)
                - news_score: 뉴스 점수
                - news_count: 뉴스 개수
                - latest_news: 최근 뉴스 (JSON 문자열)
                - executed: 실행 여부
                - execution_reason: 실행/미실행 사유
                - trade_id: 관련 거래 ID (선택)
        
        Returns:
            signal_id: 생성된 신호 ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO strategy_signals (
                    timestamp, stock_code, signal_type, signal_strength,
                    strategy_scores, news_score, news_count, latest_news,
                    executed, execution_reason, trade_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data['timestamp'],
                signal_data['stock_code'],
                signal_data['signal_type'],
                signal_data.get('signal_strength'),
                signal_data.get('strategy_scores'),
                signal_data.get('news_score'),
                signal_data.get('news_count'),
                signal_data.get('latest_news'),
                signal_data.get('executed', False),
                signal_data.get('execution_reason'),
                signal_data.get('trade_id')
            ))
            self.conn.commit()
            
            signal_id = cursor.lastrowid
            log.debug(f"🎯 전략 신호 기록: {signal_data['signal_type']} {signal_data['stock_code']} (ID: {signal_id})")
            
            return signal_id
            
        except Exception as e:
            log.error(f"❌ 전략 신호 기록 실패: {e}")
            self.conn.rollback()
            return -1
    
    def update_daily_summary(self, target_date: Optional[str] = None):
        """
        일일 요약 업데이트
        
        Args:
            target_date: 대상 날짜 (YYYY-MM-DD 형식, None이면 오늘)
        """
        try:
            if target_date is None:
                target_date = date.today().isoformat()
            
            cursor = self.conn.cursor()
            
            # 해당 날짜의 통계 계산
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN trade_type = 'BUY' THEN 1 ELSE 0 END) as buy_count,
                    SUM(CASE WHEN trade_type = 'SELL' THEN 1 ELSE 0 END) as sell_count
                FROM trades
                WHERE DATE(timestamp) = ?
            """, (target_date,))
            
            trade_stats = cursor.fetchone()
            
            # 포지션 통계 계산
            cursor.execute("""
                SELECT 
                    SUM(profit_loss) as total_profit_loss,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as win_count,
                    SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as loss_count,
                    AVG(profit_loss_percent) as avg_profit_loss_percent,
                    AVG(holding_duration_seconds) as avg_holding_duration_seconds
                FROM positions
                WHERE DATE(exit_time) = ? AND status = 'CLOSED'
            """, (target_date,))
            
            position_stats = cursor.fetchone()
            
            # 승률 계산
            win_count = position_stats['win_count'] or 0
            loss_count = position_stats['loss_count'] or 0
            total_closed = win_count + loss_count
            win_rate = (win_count / total_closed * 100) if total_closed > 0 else 0
            
            # INSERT OR REPLACE (UPSERT)
            cursor.execute("""
                INSERT OR REPLACE INTO daily_summary (
                    date, total_trades, buy_count, sell_count,
                    total_profit_loss, win_count, loss_count, win_rate,
                    avg_profit_loss_percent, avg_holding_duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                target_date,
                trade_stats['total_trades'],
                trade_stats['buy_count'],
                trade_stats['sell_count'],
                position_stats['total_profit_loss'] or 0,
                win_count,
                loss_count,
                win_rate,
                position_stats['avg_profit_loss_percent'],
                position_stats['avg_holding_duration_seconds']
            ))
            
            self.conn.commit()
            log.debug(f"📊 일일 요약 업데이트: {target_date}")
            
        except Exception as e:
            log.error(f"❌ 일일 요약 업데이트 실패: {e}")
            self.conn.rollback()
    
    def get_all_positions(self, status: Optional[str] = None) -> List[dict]:
        """
        모든 포지션 조회
        
        Args:
            status: 상태 필터 ('OPEN', 'CLOSED', None=전체)
        
        Returns:
            포지션 리스트
        """
        try:
            cursor = self.conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM positions WHERE status = ? ORDER BY entry_time DESC", (status,))
            else:
                cursor.execute("SELECT * FROM positions ORDER BY entry_time DESC")
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            log.error(f"❌ 포지션 조회 실패: {e}")
            return []
    
    def get_position_history(self, stock_code: str) -> List[dict]:
        """
        종목별 포지션 이력
        
        Args:
            stock_code: 종목 코드
        
        Returns:
            해당 종목의 포지션 리스트
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM positions
                WHERE stock_code = ?
                ORDER BY entry_time DESC
            """, (stock_code,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            log.error(f"❌ 종목별 포지션 조회 실패: {e}")
            return []
    
    def get_open_positions(self) -> list:
        """
        현재 열려있는 포지션 조회
        
        Returns:
            포지션 리스트 [{position_id, stock_code, sell_blocked, ...}, ...]
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT position_id, stock_code, stock_name, entry_price, 
                       quantity, sell_blocked
                FROM positions
                WHERE status = 'OPEN'
            """)
            
            columns = [desc[0] for desc in cursor.description]
            positions = []
            for row in cursor.fetchall():
                position = dict(zip(columns, row))
                positions.append(position)
            
            return positions
            
        except Exception as e:
            log.error(f"❌ 열린 포지션 조회 실패: {e}")
            return []
    
    def get_performance_summary(self) -> dict:
        """
        전체 성과 요약
        
        Returns:
            성과 지표 딕셔너리
        """
        try:
            cursor = self.conn.cursor()
            
            # 전체 포지션 통계
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_positions,
                    SUM(profit_loss) as total_profit_loss,
                    AVG(profit_loss_percent) as avg_profit_loss_percent,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as win_count,
                    SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as loss_count,
                    AVG(holding_duration_seconds) as avg_holding_duration,
                    MAX(profit_loss) as best_trade,
                    MIN(profit_loss) as worst_trade,
                    MAX(profit_loss_percent) as best_trade_percent,
                    MIN(profit_loss_percent) as worst_trade_percent
                FROM positions
                WHERE status = 'CLOSED'
            """)
            
            stats = dict(cursor.fetchone())
            
            # 승률 계산
            total_closed = stats['win_count'] + stats['loss_count']
            stats['win_rate'] = (stats['win_count'] / total_closed * 100) if total_closed > 0 else 0
            
            # 전체 거래 수
            cursor.execute("SELECT COUNT(*) as total_trades FROM trades")
            stats['total_trades'] = cursor.fetchone()['total_trades']
            
            return stats
            
        except Exception as e:
            log.error(f"❌ 성과 요약 조회 실패: {e}")
            return {}
    
    def get_trade_details(self, limit: int = 100) -> List[Dict]:
        """
        🆕 거래 상세 정보 조회 (설정값 포함)
        
        Args:
            limit: 최대 조회 개수
        
        Returns:
            거래 상세 정보 리스트
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.position_id,
                    p.stock_code,
                    p.stock_name,
                    p.entry_time,
                    p.entry_price,
                    p.quantity,
                    p.total_invested,
                    p.exit_time,
                    p.exit_price,
                    p.exit_reason,
                    p.profit_loss,
                    p.profit_loss_percent,
                    p.holding_duration_seconds,
                    p.entry_config,
                    p.exit_config,
                    p.average_down_count,
                    p.sell_blocked
                FROM positions p
                WHERE p.status = 'CLOSED'
                ORDER BY p.entry_time DESC
                LIMIT ?
            """, (limit,))
            
            positions = []
            for row in cursor.fetchall():
                position_dict = dict(row)
                
                # JSON 파싱
                if position_dict['entry_config']:
                    try:
                        position_dict['entry_config'] = json.loads(position_dict['entry_config'])
                    except:
                        position_dict['entry_config'] = {}
                else:
                    position_dict['entry_config'] = {}
                
                if position_dict['exit_config']:
                    try:
                        position_dict['exit_config'] = json.loads(position_dict['exit_config'])
                    except:
                        position_dict['exit_config'] = {}
                else:
                    position_dict['exit_config'] = {}
                
                positions.append(position_dict)
            
            return positions
            
        except Exception as e:
            log.error(f"❌ 거래 상세 정보 조회 실패: {e}")
            return []
    
    def get_strategy_signals(self, limit: int = 100) -> List[Dict]:
        """
        🆕 전략 신호 이력 조회
        
        Args:
            limit: 최대 조회 개수
        
        Returns:
            전략 신호 리스트
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    s.signal_id,
                    s.timestamp,
                    s.stock_code,
                    s.signal_type,
                    s.signal_strength,
                    s.strategy_scores,
                    s.news_score,
                    s.news_count,
                    s.latest_news,
                    s.executed,
                    s.execution_reason,
                    s.trade_id
                FROM strategy_signals s
                ORDER BY s.timestamp DESC
                LIMIT ?
            """, (limit,))
            
            signals = []
            for row in cursor.fetchall():
                signal_dict = dict(row)
                
                # JSON 파싱
                if signal_dict['strategy_scores']:
                    try:
                        signal_dict['strategy_scores'] = json.loads(signal_dict['strategy_scores'])
                    except:
                        signal_dict['strategy_scores'] = {}
                else:
                    signal_dict['strategy_scores'] = {}
                
                signals.append(signal_dict)
            
            return signals
            
        except Exception as e:
            log.error(f"❌ 전략 신호 조회 실패: {e}")
            return []
    
    def export_to_csv(self, output_dir: str):
        """
        CSV로 내보내기 (분석용)
        
        Args:
            output_dir: 출력 디렉토리
        """
        try:
            import csv
            
            os.makedirs(output_dir, exist_ok=True)
            
            cursor = self.conn.cursor()
            
            # trades.csv
            cursor.execute("SELECT * FROM trades ORDER BY timestamp")
            with open(os.path.join(output_dir, "trades.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([desc[0] for desc in cursor.description])
                writer.writerows(cursor.fetchall())
            
            # positions.csv
            cursor.execute("SELECT * FROM positions ORDER BY entry_time")
            with open(os.path.join(output_dir, "positions.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([desc[0] for desc in cursor.description])
                writer.writerows(cursor.fetchall())
            
            # daily_summary.csv
            cursor.execute("SELECT * FROM daily_summary ORDER BY date")
            with open(os.path.join(output_dir, "daily_summary.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([desc[0] for desc in cursor.description])
                writer.writerows(cursor.fetchall())
            
            log.success(f"✅ CSV 내보내기 완료: {output_dir}")
            
        except Exception as e:
            log.error(f"❌ CSV 내보내기 실패: {e}")
    
    def export_to_json(self, output_path: str):
        """
        JSON으로 내보내기 (백업용)
        
        Args:
            output_path: 출력 파일 경로
        """
        try:
            cursor = self.conn.cursor()
            
            data = {
                'exported_at': datetime.now().isoformat(),
                'trades': [],
                'positions': [],
                'daily_summary': []
            }
            
            # trades
            cursor.execute("SELECT * FROM trades ORDER BY timestamp")
            data['trades'] = [dict(row) for row in cursor.fetchall()]
            
            # positions
            cursor.execute("SELECT * FROM positions ORDER BY entry_time")
            data['positions'] = [dict(row) for row in cursor.fetchall()]
            
            # daily_summary
            cursor.execute("SELECT * FROM daily_summary ORDER BY date")
            data['daily_summary'] = [dict(row) for row in cursor.fetchall()]
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            log.success(f"✅ JSON 내보내기 완료: {output_path}")
            
        except Exception as e:
            log.error(f"❌ JSON 내보내기 실패: {e}")
    
    def backup_database(self, backup_path: str):
        """
        데이터베이스 백업
        
        Args:
            backup_path: 백업 파일 경로
        """
        try:
            # 백업 디렉토리 생성
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 데이터베이스 파일 복사
            shutil.copy2(self.db_path, backup_path)
            
            log.success(f"✅ 데이터베이스 백업 완료: {backup_path}")
            
        except Exception as e:
            log.error(f"❌ 데이터베이스 백업 실패: {e}")
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            log.debug("📦 거래 이력 DB 연결 종료")


