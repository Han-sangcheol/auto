"""
통계 대시보드 위젯 모듈

[파일 역할]
자동매매 프로그램의 상세 통계를 표시하는 PyQt5 위젯입니다.

[주요 기능]
- 일별/주별/월별 수익률
- 전략별 성과 분석
- 승률, 평균 수익, 최대 손실
- 거래 히스토리 테이블

[사용 방법]
from statistics_widget import StatisticsWidget
stats = StatisticsWidget(trading_engine)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QGroupBox, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List


class StatisticsWidget(QWidget):
    """
    상세 통계 대시보드 위젯
    """
    def __init__(self, trading_engine, parent=None):
        super().__init__(parent)
        self.trading_engine = trading_engine
        self.init_ui()
        
        # 자동 업데이트 타이머 (5초마다)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(5000)
    
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 1. 전체 요약
        summary_group = self.create_summary_group()
        scroll_layout.addWidget(summary_group)
        
        # 2. 기간별 수익률
        period_group = self.create_period_group()
        scroll_layout.addWidget(period_group)
        
        # 3. 거래 통계
        trade_group = self.create_trade_stats_group()
        scroll_layout.addWidget(trade_group)
        
        # 4. 거래 히스토리
        history_group = self.create_history_group()
        scroll_layout.addWidget(history_group)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
        
        # 초기 업데이트
        self.update_statistics()
    
    def create_summary_group(self) -> QGroupBox:
        """전체 요약 그룹"""
        group = QGroupBox("📊 전체 요약")
        layout = QGridLayout()
        
        # 레이블 생성
        self.total_profit_label = QLabel("총 손익: 계산 중...")
        self.total_profit_label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        
        self.profit_rate_label = QLabel("수익률: 0.00%")
        self.profit_rate_label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        
        self.trade_count_label = QLabel("총 거래: 0회")
        self.trade_count_label.setFont(QFont("맑은 고딕", 11))
        
        self.win_rate_label = QLabel("승률: 0.00%")
        self.win_rate_label.setFont(QFont("맑은 고딕", 11))
        
        self.avg_profit_label = QLabel("평균 수익: 0원")
        self.avg_profit_label.setFont(QFont("맑은 고딕", 11))
        
        self.max_profit_label = QLabel("최대 수익: 0원")
        self.max_profit_label.setFont(QFont("맑은 고딕", 11))
        
        self.max_loss_label = QLabel("최대 손실: 0원")
        self.max_loss_label.setFont(QFont("맑은 고딕", 11))
        
        self.fees_label = QLabel("총 수수료: 0원")
        self.fees_label.setFont(QFont("맑은 고딕", 11))
        
        # 배치
        layout.addWidget(self.total_profit_label, 0, 0)
        layout.addWidget(self.profit_rate_label, 0, 1)
        layout.addWidget(self.trade_count_label, 1, 0)
        layout.addWidget(self.win_rate_label, 1, 1)
        layout.addWidget(self.avg_profit_label, 2, 0)
        layout.addWidget(self.max_profit_label, 2, 1)
        layout.addWidget(self.max_loss_label, 3, 0)
        layout.addWidget(self.fees_label, 3, 1)
        
        group.setLayout(layout)
        return group
    
    def create_period_group(self) -> QGroupBox:
        """기간별 수익률 그룹"""
        group = QGroupBox("📅 기간별 수익률")
        layout = QVBoxLayout()
        
        # 테이블 생성
        self.period_table = QTableWidget()
        self.period_table.setColumnCount(4)
        self.period_table.setHorizontalHeaderLabels([
            "기간", "거래 횟수", "수익/손실", "수익률"
        ])
        self.period_table.horizontalHeader().setStretchLastSection(True)
        self.period_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.period_table.setMaximumHeight(200)
        
        layout.addWidget(self.period_table)
        group.setLayout(layout)
        return group
    
    def create_trade_stats_group(self) -> QGroupBox:
        """거래 통계 그룹"""
        group = QGroupBox("📈 거래 통계")
        layout = QGridLayout()
        
        # 레이블 생성
        self.total_buy_label = QLabel("총 매수: 0회")
        self.total_sell_label = QLabel("총 매도: 0회")
        self.holding_count_label = QLabel("현재 보유: 0종목")
        self.holding_value_label = QLabel("보유 평가액: 0원")
        
        self.avg_holding_period_label = QLabel("평균 보유 기간: -")
        self.quickest_trade_label = QLabel("최단 거래: -")
        self.longest_trade_label = QLabel("최장 거래: -")
        
        self.stop_loss_count_label = QLabel("손절매: 0회")
        self.take_profit_count_label = QLabel("익절매: 0회")
        self.total_trades_today_label = QLabel("오늘 거래: 0회")
        
        # 배치
        layout.addWidget(self.total_buy_label, 0, 0)
        layout.addWidget(self.total_sell_label, 0, 1)
        layout.addWidget(self.holding_count_label, 1, 0)
        layout.addWidget(self.holding_value_label, 1, 1)
        layout.addWidget(self.avg_holding_period_label, 2, 0)
        layout.addWidget(self.quickest_trade_label, 2, 1)
        layout.addWidget(self.longest_trade_label, 3, 0)
        layout.addWidget(self.stop_loss_count_label, 4, 0)
        layout.addWidget(self.take_profit_count_label, 4, 1)
        layout.addWidget(self.total_trades_today_label, 5, 0)
        
        group.setLayout(layout)
        return group
    
    def create_history_group(self) -> QGroupBox:
        """거래 히스토리 그룹"""
        group = QGroupBox("📜 거래 히스토리 (최근 50개)")
        layout = QVBoxLayout()
        
        # 테이블 생성
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "시간", "종목", "유형", "수량", "가격", "손익", "수익률"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.history_table)
        group.setLayout(layout)
        return group
    
    def update_statistics(self):
        """통계 업데이트"""
        try:
            # 전체 요약 업데이트
            self.update_summary()
            
            # 기간별 수익률 업데이트
            self.update_period_stats()
            
            # 거래 통계 업데이트
            self.update_trade_stats()
            
            # 거래 히스토리 업데이트
            self.update_history()
            
        except Exception as e:
            print(f"통계 업데이트 오류: {e}")
    
    def update_summary(self):
        """전체 요약 업데이트"""
        try:
            stats = self.trading_engine.risk_manager.get_statistics()
            
            # 총 손익
            total_profit = stats.get('total_profit_loss', 0)
            self.total_profit_label.setText(f"총 손익: {total_profit:+,}원")
            
            # 색상 변경
            if total_profit >= 0:
                self.total_profit_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.total_profit_label.setStyleSheet("color: blue; font-weight: bold;")
            
            # 수익률
            initial_balance = stats.get('initial_balance', 10000000)
            profit_rate = (total_profit / initial_balance) * 100 if initial_balance > 0 else 0
            self.profit_rate_label.setText(f"수익률: {profit_rate:+.2f}%")
            
            if profit_rate >= 0:
                self.profit_rate_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.profit_rate_label.setStyleSheet("color: blue; font-weight: bold;")
            
            # 거래 횟수
            trade_count = stats.get('total_trades', 0)
            self.trade_count_label.setText(f"총 거래: {trade_count}회")
            
            # 승률
            win_count = stats.get('win_count', 0)
            win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
            self.win_rate_label.setText(f"승률: {win_rate:.2f}%")
            
            # 평균 수익
            avg_profit = stats.get('average_profit_loss', 0)
            self.avg_profit_label.setText(f"평균 수익: {avg_profit:+,}원")
            
            # 최대 수익
            max_profit = stats.get('max_profit', 0)
            self.max_profit_label.setText(f"최대 수익: {max_profit:+,}원")
            
            # 최대 손실
            max_loss = stats.get('max_loss', 0)
            self.max_loss_label.setText(f"최대 손실: {max_loss:+,}원")
            
            # 총 수수료
            total_fees = stats.get('total_fees_paid', 0)
            self.fees_label.setText(f"총 수수료: {total_fees:,}원")
            
        except Exception as e:
            print(f"전체 요약 업데이트 오류: {e}")
    
    def update_period_stats(self):
        """기간별 수익률 업데이트"""
        try:
            # 더미 데이터 (실제로는 거래 히스토리에서 계산)
            periods = [
                ("오늘", 0, 0, 0.0),
                ("이번 주", 0, 0, 0.0),
                ("이번 달", 0, 0, 0.0),
                ("전체", 0, 0, 0.0)
            ]
            
            # 실제 통계 가져오기
            stats = self.trading_engine.risk_manager.get_statistics()
            total_trades = stats.get('total_trades', 0)
            total_profit = stats.get('total_profit_loss', 0)
            initial_balance = stats.get('initial_balance', 10000000)
            profit_rate = (total_profit / initial_balance) * 100 if initial_balance > 0 else 0
            
            periods[-1] = ("전체", total_trades, total_profit, profit_rate)
            
            # 테이블 업데이트
            self.period_table.setRowCount(len(periods))
            
            for row, (period, count, profit, rate) in enumerate(periods):
                self.period_table.setItem(row, 0, QTableWidgetItem(period))
                self.period_table.setItem(row, 1, QTableWidgetItem(f"{count}회"))
                
                # 수익/손실 (색상 적용)
                profit_item = QTableWidgetItem(f"{profit:+,}원")
                if profit >= 0:
                    profit_item.setForeground(QColor(255, 0, 0))
                else:
                    profit_item.setForeground(QColor(0, 0, 255))
                self.period_table.setItem(row, 2, profit_item)
                
                # 수익률 (색상 적용)
                rate_item = QTableWidgetItem(f"{rate:+.2f}%")
                if rate >= 0:
                    rate_item.setForeground(QColor(255, 0, 0))
                else:
                    rate_item.setForeground(QColor(0, 0, 255))
                self.period_table.setItem(row, 3, rate_item)
            
        except Exception as e:
            print(f"기간별 수익률 업데이트 오류: {e}")
    
    def update_trade_stats(self):
        """거래 통계 업데이트"""
        try:
            # 매수/매도 횟수 (실제로는 거래 히스토리에서 계산)
            self.total_buy_label.setText(f"총 매수: 0회")
            self.total_sell_label.setText(f"총 매도: 0회")
            
            # 현재 보유
            positions = self.trading_engine.risk_manager.positions
            holding_count = len(positions)
            self.holding_count_label.setText(f"현재 보유: {holding_count}종목")
            
            # 보유 평가액 (현재가 기준)
            holding_value = sum(
                p.quantity * p.current_price
                for p in positions.values()
            )
            self.holding_value_label.setText(f"보유 평가액: {holding_value:,}원")
            
            # 평균 보유 기간 (실제로는 거래 히스토리에서 계산)
            self.avg_holding_period_label.setText(f"평균 보유 기간: -")
            self.quickest_trade_label.setText(f"최단 거래: -")
            self.longest_trade_label.setText(f"최장 거래: -")
            
            # 손절/익절 (실제로는 거래 히스토리에서 계산)
            self.stop_loss_count_label.setText(f"손절매: 0회")
            self.take_profit_count_label.setText(f"익절매: 0회")
            
            # 오늘 거래
            self.total_trades_today_label.setText(f"오늘 거래: 0회")
            
        except Exception as e:
            print(f"거래 통계 업데이트 오류: {e}")
    
    def update_history(self):
        """거래 히스토리 업데이트"""
        try:
            # risk_manager에서 거래 히스토리 가져오기
            trades = self.trading_engine.risk_manager.trades
            
            # 최근 50개만 표시
            recent_trades = trades[-50:] if len(trades) > 50 else trades
            
            # 테이블 업데이트
            self.history_table.setRowCount(len(recent_trades))
            
            for row, trade in enumerate(reversed(recent_trades)):  # 최신순
                # 시간
                time_str = trade.timestamp.strftime("%H:%M:%S")
                self.history_table.setItem(row, 0, QTableWidgetItem(time_str))
                
                # 종목
                self.history_table.setItem(row, 1, QTableWidgetItem(trade.stock_code))
                
                # 유형 (매수/매도)
                trade_type_item = QTableWidgetItem(trade.trade_type)
                if trade.trade_type == "BUY":
                    trade_type_item.setForeground(QColor(255, 0, 0))  # 빨간색
                else:
                    trade_type_item.setForeground(QColor(0, 0, 255))  # 파란색
                self.history_table.setItem(row, 2, trade_type_item)
                
                # 수량
                self.history_table.setItem(row, 3, QTableWidgetItem(f"{trade.quantity}주"))
                
                # 가격
                self.history_table.setItem(row, 4, QTableWidgetItem(f"{trade.price:,}원"))
                
                # 손익 (매도 시에만)
                if trade.trade_type == "SELL" and hasattr(trade, 'profit_loss'):
                    profit_loss = trade.profit_loss
                    profit_item = QTableWidgetItem(f"{profit_loss:+,}원")
                    if profit_loss >= 0:
                        profit_item.setForeground(QColor(255, 0, 0))
                    else:
                        profit_item.setForeground(QColor(0, 0, 255))
                    self.history_table.setItem(row, 5, profit_item)
                    
                    # 수익률 (매도 시에만)
                    if hasattr(trade, 'profit_rate'):
                        rate_item = QTableWidgetItem(f"{trade.profit_rate:+.2f}%")
                        if trade.profit_rate >= 0:
                            rate_item.setForeground(QColor(255, 0, 0))
                        else:
                            rate_item.setForeground(QColor(0, 0, 255))
                        self.history_table.setItem(row, 6, rate_item)
                else:
                    self.history_table.setItem(row, 5, QTableWidgetItem("-"))
                    self.history_table.setItem(row, 6, QTableWidgetItem("-"))
            
        except Exception as e:
            print(f"거래 히스토리 업데이트 오류: {e}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # 테스트용 더미 엔진
    class DummyRiskManager:
        def get_statistics(self):
            return {
                'total_profit_loss': 150000,
                'initial_balance': 10000000,
                'total_trades': 25,
                'win_count': 15,
                'average_profit_loss': 6000,
                'max_profit': 50000,
                'max_loss': -30000,
                'total_fees_paid': 5000
            }
        
        positions = {}
    
    class DummyEngine:
        risk_manager = DummyRiskManager()
    
    app = QApplication(sys.argv)
    
    window = StatisticsWidget(DummyEngine())
    window.setWindowTitle("통계 대시보드 테스트")
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec_())

