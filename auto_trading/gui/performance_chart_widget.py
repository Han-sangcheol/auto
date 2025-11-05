"""
성과 분석 차트 위젯 모듈

[파일 역할]
매매 이력 데이터베이스를 기반으로 수익률 분석 차트를 생성하고 표시합니다.

[주요 기능]
- 누적 수익률 차트 (시간대별 자산 변화)
- 포지션별 수익률 차트 (개별 거래 성과)
- 일일 손익 차트 (날짜별 손익)
- 승률 분석 차트 (승/패 비율)
- 보유 기간 vs 수익률 산점도
- 통계 요약 패널 (승률, 평균 수익률, 샤프 비율 등)

[사용 방법]
from performance_chart_widget import PerformanceChartWidget
from trading_history_db import TradingHistoryDB

db = TradingHistoryDB("trading_history.db")
widget = PerformanceChartWidget(db)
# monitor_gui.py의 탭에 추가
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QGridLayout,
    QSplitter, QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np

from utils.logger import log
from database.trading_history_db import TradingHistoryDB


class PerformanceChartWidget(QWidget):
    """
    성과 분석 차트 위젯
    
    블랙박스 데이터베이스의 거래 이력을 분석하여
    다양한 시각화 차트를 제공합니다.
    """
    
    def __init__(self, history_db: TradingHistoryDB, parent=None):
        super().__init__(parent)
        self.history_db = history_db
        
        # 현재 선택된 차트 타입
        self.current_chart_type = "cumulative_return"
        
        # 데이터 캐시
        self.positions_cache: List[dict] = []
        self.trades_cache: List[dict] = []
        self.trade_details_cache: List[dict] = []  # 🆕 거래 상세 정보
        self.strategy_signals_cache: List[dict] = []  # 🆕 전략 신호
        self.last_refresh_time = None
        
        self.init_ui()
        
        # 초기 데이터 로드
        self.refresh_data()
        
        log.info("✅ PerformanceChartWidget 초기화 완료")
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        
        # --- 컨트롤 패널 ---
        control_layout = QHBoxLayout()
        
        # 차트 타입 선택
        control_layout.addWidget(QLabel("차트 종류:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "누적 수익률",
            "포지션별 수익률",
            "일일 손익",
            "승률 분석",
            "보유 기간 vs 수익률"
        ])
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        control_layout.addWidget(self.chart_type_combo)
        
        # 기간 필터
        control_layout.addWidget(QLabel("기간:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["전체", "1개월", "3개월", "6개월", "1년"])
        self.period_combo.currentTextChanged.connect(self.refresh_chart)
        control_layout.addWidget(self.period_combo)
        
        # 새로고침 버튼
        self.refresh_button = QPushButton("🔄 새로고침")
        self.refresh_button.clicked.connect(self.refresh_data)
        control_layout.addWidget(self.refresh_button)
        
        # 내보내기 버튼
        self.export_button = QPushButton("📥 CSV 내보내기")
        self.export_button.clicked.connect(self.export_data)
        control_layout.addWidget(self.export_button)
        
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # --- 메인 컨텐츠 ---
        splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 정보 탭 (통계 + 상세 정보)
        self.info_tabs = QTabWidget()
        
        # 탭 1: 통계 요약
        self.stats_panel = self.create_stats_panel()
        self.info_tabs.addTab(self.stats_panel, "📊 통계")
        
        # 탭 2: 거래 상세
        self.trade_detail_widget = self.create_trade_detail_widget()
        self.info_tabs.addTab(self.trade_detail_widget, "📝 거래상세")
        
        # 탭 3: 전략 신호
        self.strategy_signal_widget = self.create_strategy_signal_widget()
        self.info_tabs.addTab(self.strategy_signal_widget, "📡 매수/매도 신호")
        
        splitter.addWidget(self.info_tabs)
        
        # 오른쪽: 차트 영역
        self.web_view = QWebEngineView()
        splitter.addWidget(self.web_view)
        
        # 비율 설정 (정보:차트 = 1:2)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
    
    def create_stats_panel(self) -> QGroupBox:
        """통계 요약 패널 생성"""
        group = QGroupBox("📊 성과 요약")
        layout = QVBoxLayout()
        
        # 통계 라벨들
        self.stats_labels = {}
        
        stats_layout = QGridLayout()
        
        stats_items = [
            ("total_trades", "총 거래 수"),
            ("closed_positions", "청산 포지션"),
            ("total_profit", "총 손익"),
            ("win_rate", "승률"),
            ("avg_profit", "평균 수익률"),
            ("avg_holding", "평균 보유 시간"),
            ("best_trade", "최고 수익"),
            ("worst_trade", "최대 손실"),
            ("sharpe_ratio", "샤프 비율"),
            ("max_drawdown", "최대 낙폭")
        ]
        
        row = 0
        for key, label in stats_items:
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            value_widget = QLabel("-")
            value_widget.setStyleSheet("font-size: 14px;")
            
            stats_layout.addWidget(label_widget, row, 0, alignment=Qt.AlignRight)
            stats_layout.addWidget(value_widget, row, 1, alignment=Qt.AlignLeft)
            
            self.stats_labels[key] = value_widget
            row += 1
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_trade_detail_widget(self) -> QWidget:
        """🆕 거래 상세 정보 위젯 생성"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 테이블
        self.trade_detail_table = QTableWidget()
        self.trade_detail_table.setColumnCount(8)
        self.trade_detail_table.setHorizontalHeaderLabels([
            "날짜", "종목", "수량", "매수가", "매도가", "손익", "손익률", "설정값"
        ])
        self.trade_detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trade_detail_table.setAlternatingRowColors(True)
        self.trade_detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.trade_detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.trade_detail_table.itemDoubleClicked.connect(self.show_trade_config_detail)
        
        layout.addWidget(QLabel("💡 더블클릭하면 상세 설정값을 확인할 수 있습니다."))
        layout.addWidget(self.trade_detail_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_strategy_signal_widget(self) -> QWidget:
        """🆕 전략 신호 위젯 생성"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 테이블
        self.strategy_signal_table = QTableWidget()
        self.strategy_signal_table.setColumnCount(7)
        self.strategy_signal_table.setHorizontalHeaderLabels([
            "시간", "종목", "신호", "강도", "MA", "RSI", "MACD"
        ])
        self.strategy_signal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.strategy_signal_table.setAlternatingRowColors(True)
        self.strategy_signal_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.strategy_signal_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(QLabel("📡 전략 매수/매도 신호 이력"))
        layout.addWidget(self.strategy_signal_table)
        
        widget.setLayout(layout)
        return widget
    
    def show_trade_config_detail(self, item):
        """거래 설정값 상세 보기"""
        row = item.row()
        
        # positions_cache에서 데이터 가져오기
        if row < len(self.trade_details_cache):
            position = self.trade_details_cache[row]
            
            entry_config = position.get('entry_config', {})
            exit_config = position.get('exit_config', {})
            
            # 팝업으로 상세 정보 표시
            from PyQt5.QtWidgets import QDialog, QTextEdit, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"거래 상세: {position['stock_name']}")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout()
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            
            detail_text = f"""
<h3>{position['stock_name']} ({position['stock_code']})</h3>

<h4>📈 매수 정보</h4>
<ul>
<li><b>진입 시간:</b> {position['entry_time']}</li>
<li><b>진입 가격:</b> {position['entry_price']:,}원</li>
<li><b>수량:</b> {position['quantity']:,}주</li>
<li><b>총 투자:</b> {position['total_invested']:,}원</li>
<li><b>물타기 횟수:</b> {position.get('average_down_count', 0)}회</li>
</ul>

<h4>🎯 매수 시 설정</h4>
<ul>
<li><b>손절매 비율:</b> {entry_config.get('STOP_LOSS_PERCENT', '-')}%</li>
<li><b>익절매 비율:</b> {entry_config.get('TAKE_PROFIT_PERCENT', '-')}%</li>
<li><b>최대 보유 종목:</b> {entry_config.get('MAX_STOCKS', '-')}개</li>
<li><b>포지션 크기:</b> {entry_config.get('POSITION_SIZE_PERCENT', '-')}%</li>
<li><b>물타기 활성화:</b> {'예' if entry_config.get('ENABLE_AVERAGE_DOWN') else '아니오'}</li>
<li><b>뉴스 분석:</b> {'활성화' if entry_config.get('ENABLE_NEWS_ANALYSIS') else '비활성화'}</li>
</ul>

<h4>📉 매도 정보</h4>
<ul>
<li><b>청산 시간:</b> {position.get('exit_time', '-')}</li>
<li><b>청산 가격:</b> {position.get('exit_price', 0):,}원</li>
<li><b>청산 사유:</b> {position.get('exit_reason', '-')}</li>
<li><b>손익:</b> <span style="color:{'green' if position.get('profit_loss', 0) >= 0 else 'red'}">
    {position.get('profit_loss', 0):+,}원 ({position.get('profit_loss_percent', 0):+.2f}%)</span></li>
<li><b>보유 기간:</b> {position.get('holding_duration_seconds', 0) // 3600}시간 
    {(position.get('holding_duration_seconds', 0) % 3600) // 60}분</li>
</ul>

<h4>⚙️ 매도 시 설정</h4>
<ul>
<li><b>손절매 비율:</b> {exit_config.get('STOP_LOSS_PERCENT', '-')}%</li>
<li><b>익절매 비율:</b> {exit_config.get('TAKE_PROFIT_PERCENT', '-')}%</li>
<li><b>급등주 감지:</b> {'활성화' if exit_config.get('ENABLE_SURGE_DETECTION') else '비활성화'}</li>
</ul>
            """
            
            text_edit.setHtml(detail_text)
            layout.addWidget(text_edit)
            
            close_button = QPushButton("닫기")
            close_button.clicked.connect(dialog.close)
            layout.addWidget(close_button)
            
            dialog.setLayout(layout)
            dialog.exec_()
    
    def refresh_data(self):
        """데이터 새로고침"""
        try:
            log.info("🔄 성과 데이터 새로고침 중...")
            
            # 포지션 데이터 로드
            self.positions_cache = self.history_db.get_all_positions(status='CLOSED')
            
            # 🆕 거래 상세 정보 로드
            self.trade_details_cache = self.history_db.get_trade_details(limit=100)
            
            # 🆕 전략 신호 로드
            self.strategy_signals_cache = self.history_db.get_strategy_signals(limit=100)
            
            # 통계 업데이트
            self.update_statistics()
            
            # 🆕 테이블 업데이트
            self.update_trade_detail_table()
            self.update_strategy_signal_table()
            
            # 차트 업데이트
            self.refresh_chart()
            
            self.last_refresh_time = datetime.now()
            log.info(f"✅ 성과 데이터 새로고침 완료: {len(self.positions_cache)}개 포지션, "
                    f"{len(self.trade_details_cache)}개 거래 상세, "
                    f"{len(self.strategy_signals_cache)}개 신호")
            
        except Exception as e:
            log.error(f"❌ 성과 데이터 새로고침 실패: {e}")
            import traceback
            log.error(traceback.format_exc())
    
    def update_statistics(self):
        """통계 요약 업데이트"""
        try:
            if not self.positions_cache:
                for label in self.stats_labels.values():
                    label.setText("-")
                return
            
            summary = self.history_db.get_performance_summary()
            
            # 총 거래 수
            self.stats_labels['total_trades'].setText(f"{summary.get('total_trades', 0):,}건")
            
            # 청산 포지션
            closed_count = summary.get('total_positions', 0)
            self.stats_labels['closed_positions'].setText(f"{closed_count:,}개")
            
            # 총 손익
            total_profit = summary.get('total_profit_loss', 0)
            profit_color = "green" if total_profit >= 0 else "red"
            self.stats_labels['total_profit'].setText(
                f"<span style='color:{profit_color};'>{total_profit:+,}원</span>"
            )
            
            # 승률
            win_rate = summary.get('win_rate', 0)
            self.stats_labels['win_rate'].setText(f"{win_rate:.1f}%")
            
            # 평균 수익률
            avg_profit = summary.get('avg_profit_loss_percent', 0) or 0
            avg_color = "green" if avg_profit >= 0 else "red"
            self.stats_labels['avg_profit'].setText(
                f"<span style='color:{avg_color};'>{avg_profit:+.2f}%</span>"
            )
            
            # 평균 보유 시간
            avg_holding = summary.get('avg_holding_duration', 0) or 0
            hours = int(avg_holding / 3600)
            minutes = int((avg_holding % 3600) / 60)
            self.stats_labels['avg_holding'].setText(f"{hours}시간 {minutes}분")
            
            # 최고 수익
            best_trade = summary.get('best_trade_percent', 0) or 0
            self.stats_labels['best_trade'].setText(
                f"<span style='color:green;'>{best_trade:+.2f}%</span>"
            )
            
            # 최대 손실
            worst_trade = summary.get('worst_trade_percent', 0) or 0
            self.stats_labels['worst_trade'].setText(
                f"<span style='color:red;'>{worst_trade:+.2f}%</span>"
            )
            
            # 샤프 비율 (간단 계산)
            sharpe = self.calculate_sharpe_ratio()
            self.stats_labels['sharpe_ratio'].setText(f"{sharpe:.2f}")
            
            # 최대 낙폭
            max_dd = self.calculate_max_drawdown()
            self.stats_labels['max_drawdown'].setText(
                f"<span style='color:red;'>{max_dd:.2f}%</span>"
            )
            
            log.debug("✅ 통계 요약 업데이트 완료")
            
        except Exception as e:
            log.error(f"❌ 통계 업데이트 실패: {e}")
    
    def calculate_sharpe_ratio(self) -> float:
        """샤프 비율 계산"""
        try:
            if not self.positions_cache:
                return 0.0
            
            returns = [p['profit_loss_percent'] for p in self.positions_cache if p.get('profit_loss_percent')]
            
            if not returns:
                return 0.0
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0.0
            
            # 연간화 (일일 수익률 가정)
            sharpe_ratio = (mean_return / std_return) * np.sqrt(252)
            
            return sharpe_ratio
            
        except Exception as e:
            log.error(f"샤프 비율 계산 실패: {e}")
            return 0.0
    
    def calculate_max_drawdown(self) -> float:
        """최대 낙폭 계산"""
        try:
            if not self.positions_cache:
                return 0.0
            
            # 시간 순 정렬
            sorted_positions = sorted(
                self.positions_cache,
                key=lambda x: x.get('exit_time', '9999-12-31')
            )
            
            # 누적 손익 계산
            cumulative = 0
            peak = 0
            max_drawdown = 0
            
            for position in sorted_positions:
                profit_loss = position.get('profit_loss', 0) or 0
                cumulative += profit_loss
                
                if cumulative > peak:
                    peak = cumulative
                
                drawdown = ((peak - cumulative) / peak * 100) if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            log.error(f"최대 낙폭 계산 실패: {e}")
            return 0.0
    
    def on_chart_type_changed(self, chart_name: str):
        """차트 타입 변경 이벤트"""
        chart_type_map = {
            "누적 수익률": "cumulative_return",
            "포지션별 수익률": "position_returns",
            "일일 손익": "daily_pnl",
            "승률 분석": "win_rate",
            "보유 기간 vs 수익률": "holding_vs_return"
        }
        
        self.current_chart_type = chart_type_map.get(chart_name, "cumulative_return")
        self.refresh_chart()
    
    def get_filtered_positions(self) -> List[dict]:
        """기간 필터링된 포지션 데이터"""
        period = self.period_combo.currentText()
        
        if period == "전체" or not self.positions_cache:
            return self.positions_cache
        
        # 기간 계산
        now = datetime.now()
        period_map = {
            "1개월": timedelta(days=30),
            "3개월": timedelta(days=90),
            "6개월": timedelta(days=180),
            "1년": timedelta(days=365)
        }
        
        start_date = now - period_map.get(period, timedelta(days=365))
        
        # 필터링
        filtered = [
            p for p in self.positions_cache
            if p.get('exit_time') and datetime.fromisoformat(p['exit_time']) >= start_date
        ]
        
        return filtered
    
    def refresh_chart(self):
        """차트 새로고침"""
        try:
            positions = self.get_filtered_positions()
            
            if not positions:
                self.display_no_data_message()
                return
            
            # 차트 타입별 생성
            if self.current_chart_type == "cumulative_return":
                fig = self.create_cumulative_return_chart(positions)
            elif self.current_chart_type == "position_returns":
                fig = self.create_position_returns_chart(positions)
            elif self.current_chart_type == "daily_pnl":
                fig = self.create_daily_pnl_chart(positions)
            elif self.current_chart_type == "win_rate":
                fig = self.create_win_rate_chart(positions)
            elif self.current_chart_type == "holding_vs_return":
                fig = self.create_holding_vs_return_chart(positions)
            else:
                fig = self.create_cumulative_return_chart(positions)
            
            # 차트 표시
            self.web_view.setHtml(fig.to_html(include_plotlyjs='cdn'))
            
            log.debug(f"✅ 차트 업데이트 완료: {self.current_chart_type}")
            
        except Exception as e:
            log.error(f"❌ 차트 생성 실패: {e}")
            self.display_error_message(str(e))
    
    def create_cumulative_return_chart(self, positions: List[dict]) -> go.Figure:
        """누적 수익률 차트"""
        # 시간 순 정렬
        sorted_positions = sorted(
            positions,
            key=lambda x: x.get('exit_time', '9999-12-31')
        )
        
        # 누적 손익 계산
        timestamps = []
        cumulative_profit = []
        cumulative_sum = 0
        
        for position in sorted_positions:
            exit_time = position.get('exit_time')
            profit_loss = position.get('profit_loss', 0) or 0
            
            if exit_time:
                timestamps.append(datetime.fromisoformat(exit_time))
                cumulative_sum += profit_loss
                cumulative_profit.append(cumulative_sum)
        
        # 차트 생성
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=cumulative_profit,
            mode='lines+markers',
            name='누적 손익',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,100,255,0.1)'
        ))
        
        # 0선 추가
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title="📈 누적 수익률 (시간별)",
            xaxis_title="날짜",
            yaxis_title="누적 손익 (원)",
            hovermode="x unified",
            template="plotly_white",
            height=600
        )
        
        return fig
    
    def create_position_returns_chart(self, positions: List[dict]) -> go.Figure:
        """포지션별 수익률 차트"""
        # 종목명, 수익률 추출
        stock_names = []
        profit_loss_percents = []
        colors = []
        
        for position in positions:
            stock_name = position.get('stock_name', position.get('stock_code', 'Unknown'))
            profit_percent = position.get('profit_loss_percent', 0) or 0
            
            stock_names.append(f"{stock_name} ({position.get('stock_code', '')})")
            profit_loss_percents.append(profit_percent)
            
            # 색상 (수익: 초록, 손실: 빨강)
            colors.append('green' if profit_percent >= 0 else 'red')
        
        # 차트 생성
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=stock_names,
            y=profit_loss_percents,
            marker_color=colors,
            name='수익률',
            text=[f"{v:+.2f}%" for v in profit_loss_percents],
            textposition='outside'
        ))
        
        # 0선 추가
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title="📊 포지션별 수익률",
            xaxis_title="종목",
            yaxis_title="수익률 (%)",
            hovermode="x",
            template="plotly_white",
            height=600,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_daily_pnl_chart(self, positions: List[dict]) -> go.Figure:
        """일일 손익 차트"""
        # 날짜별 손익 집계
        daily_pnl = {}
        
        for position in positions:
            exit_time = position.get('exit_time')
            profit_loss = position.get('profit_loss', 0) or 0
            
            if exit_time:
                date = datetime.fromisoformat(exit_time).date()
                daily_pnl[date] = daily_pnl.get(date, 0) + profit_loss
        
        # 정렬
        sorted_dates = sorted(daily_pnl.keys())
        daily_profits = [daily_pnl[date] for date in sorted_dates]
        colors = ['green' if v >= 0 else 'red' for v in daily_profits]
        
        # 차트 생성
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=sorted_dates,
            y=daily_profits,
            marker_color=colors,
            name='일일 손익',
            text=[f"{v:+,}" for v in daily_profits],
            textposition='outside'
        ))
        
        # 0선 추가
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title="📅 일일 손익",
            xaxis_title="날짜",
            yaxis_title="손익 (원)",
            hovermode="x",
            template="plotly_white",
            height=600
        )
        
        return fig
    
    def create_win_rate_chart(self, positions: List[dict]) -> go.Figure:
        """승률 분석 차트"""
        # 승/패 카운트
        win_count = sum(1 for p in positions if (p.get('profit_loss', 0) or 0) > 0)
        loss_count = sum(1 for p in positions if (p.get('profit_loss', 0) or 0) < 0)
        break_even_count = len(positions) - win_count - loss_count
        
        # 파이 차트 생성
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=['승', '패', '본전'],
            values=[win_count, loss_count, break_even_count],
            marker_colors=['green', 'red', 'gray'],
            hole=0.4,
            textinfo='label+percent+value',
            textposition='outside'
        ))
        
        win_rate = (win_count / len(positions) * 100) if positions else 0
        
        fig.update_layout(
            title=f"🎯 승률 분석 (승률: {win_rate:.1f}%)",
            template="plotly_white",
            height=600,
            annotations=[dict(
                text=f'총 {len(positions)}건',
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )]
        )
        
        return fig
    
    def create_holding_vs_return_chart(self, positions: List[dict]) -> go.Figure:
        """보유 기간 vs 수익률 산점도"""
        holding_durations = []
        profit_percents = []
        stock_names = []
        colors = []
        
        for position in positions:
            duration = position.get('holding_duration_seconds', 0) or 0
            profit = position.get('profit_loss_percent', 0) or 0
            stock_name = position.get('stock_name', position.get('stock_code', 'Unknown'))
            
            # 시간 단위로 변환
            duration_hours = duration / 3600
            
            holding_durations.append(duration_hours)
            profit_percents.append(profit)
            stock_names.append(stock_name)
            colors.append('green' if profit >= 0 else 'red')
        
        # 산점도 생성
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=holding_durations,
            y=profit_percents,
            mode='markers',
            marker=dict(
                color=colors,
                size=10,
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            text=stock_names,
            hovertemplate='<b>%{text}</b><br>보유: %{x:.1f}시간<br>수익률: %{y:+.2f}%<extra></extra>'
        ))
        
        # 0선 추가
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title="⏱️ 보유 기간 vs 수익률",
            xaxis_title="보유 기간 (시간)",
            yaxis_title="수익률 (%)",
            hovermode="closest",
            template="plotly_white",
            height=600
        )
        
        return fig
    
    def display_no_data_message(self):
        """데이터 없음 메시지"""
        html_content = """
        <div style="text-align: center; padding: 50px; background-color: #f8f9fa; height: 100%;">
            <h2>📊 성과 분석</h2>
            <p>아직 청산된 포지션이 없습니다.</p>
            <p>매매가 실행되면 이곳에 성과 분석 차트가 표시됩니다.</p>
        </div>
        """
        self.web_view.setHtml(html_content)
    
    def display_error_message(self, error_msg: str):
        """오류 메시지"""
        html_content = f"""
        <div style="text-align: center; padding: 50px; background-color: #f8f9fa; height: 100%;">
            <h2>❌ 차트 생성 오류</h2>
            <p>{error_msg}</p>
            <p>데이터를 다시 로드해 주세요.</p>
        </div>
        """
        self.web_view.setHtml(html_content)
    
    def update_trade_detail_table(self):
        """🆕 거래 상세 테이블 업데이트"""
        try:
            self.trade_detail_table.setRowCount(0)
            
            for position in self.trade_details_cache:
                row = self.trade_detail_table.rowCount()
                self.trade_detail_table.insertRow(row)
                
                # 날짜
                entry_date = position['entry_time'][:10] if position['entry_time'] else "-"
                self.trade_detail_table.setItem(row, 0, QTableWidgetItem(entry_date))
                
                # 종목
                stock_info = f"{position['stock_name']}\n({position['stock_code']})"
                self.trade_detail_table.setItem(row, 1, QTableWidgetItem(stock_info))
                
                # 수량
                self.trade_detail_table.setItem(row, 2, QTableWidgetItem(f"{position['quantity']:,}"))
                
                # 매수가
                self.trade_detail_table.setItem(row, 3, QTableWidgetItem(f"{position['entry_price']:,}"))
                
                # 매도가
                exit_price = position.get('exit_price', 0)
                self.trade_detail_table.setItem(row, 4, QTableWidgetItem(f"{exit_price:,}"))
                
                # 손익
                profit_loss = position.get('profit_loss', 0)
                profit_item = QTableWidgetItem(f"{profit_loss:+,}원")
                profit_item.setForeground(Qt.darkGreen if profit_loss >= 0 else Qt.red)
                self.trade_detail_table.setItem(row, 5, profit_item)
                
                # 손익률
                profit_rate = position.get('profit_loss_percent', 0)
                rate_item = QTableWidgetItem(f"{profit_rate:+.2f}%")
                rate_item.setForeground(Qt.darkGreen if profit_rate >= 0 else Qt.red)
                self.trade_detail_table.setItem(row, 6, rate_item)
                
                # 설정값
                entry_config = position.get('entry_config', {})
                config_text = f"손절: {entry_config.get('STOP_LOSS_PERCENT', '-')}%\n"
                config_text += f"익절: {entry_config.get('TAKE_PROFIT_PERCENT', '-')}%"
                self.trade_detail_table.setItem(row, 7, QTableWidgetItem(config_text))
            
            self.trade_detail_table.resizeRowsToContents()
            
        except Exception as e:
            log.error(f"거래 상세 테이블 업데이트 실패: {e}")
    
    def update_strategy_signal_table(self):
        """🆕 전략 신호 테이블 업데이트"""
        try:
            self.strategy_signal_table.setRowCount(0)
            
            for signal in self.strategy_signals_cache:
                row = self.strategy_signal_table.rowCount()
                self.strategy_signal_table.insertRow(row)
                
                # 시간
                timestamp = signal['timestamp'][:16] if signal['timestamp'] else "-"
                self.strategy_signal_table.setItem(row, 0, QTableWidgetItem(timestamp))
                
                # 종목
                self.strategy_signal_table.setItem(row, 1, QTableWidgetItem(signal['stock_code']))
                
                # 신호
                signal_type = signal['signal_type']
                signal_item = QTableWidgetItem(signal_type)
                if signal_type == 'BUY':
                    signal_item.setForeground(Qt.blue)
                elif signal_type == 'SELL':
                    signal_item.setForeground(Qt.red)
                self.strategy_signal_table.setItem(row, 2, signal_item)
                
                # 강도
                strength = signal.get('signal_strength', 0)
                self.strategy_signal_table.setItem(row, 3, QTableWidgetItem(f"{strength:.2f}"))
                
                # 전략 점수
                strategy_scores = signal.get('strategy_scores', {})
                
                # MA
                ma_signal = strategy_scores.get('moving_average', '-')
                self.strategy_signal_table.setItem(row, 4, QTableWidgetItem(str(ma_signal)))
                
                # RSI
                rsi_signal = strategy_scores.get('rsi', '-')
                self.strategy_signal_table.setItem(row, 5, QTableWidgetItem(str(rsi_signal)))
                
                # MACD
                macd_signal = strategy_scores.get('macd', '-')
                self.strategy_signal_table.setItem(row, 6, QTableWidgetItem(str(macd_signal)))
            
            self.strategy_signal_table.resizeRowsToContents()
            
        except Exception as e:
            log.error(f"전략 신호 테이블 업데이트 실패: {e}")
    
    def export_data(self):
        """데이터 CSV로 내보내기"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import os
            
            # 저장 경로 선택
            default_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(default_dir, exist_ok=True)
            
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "CSV 내보내기 폴더 선택",
                default_dir
            )
            
            if dir_path:
                self.history_db.export_to_csv(dir_path)
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "내보내기 완료",
                    f"CSV 파일이 성공적으로 내보내졌습니다:\n{dir_path}"
                )
                
                log.success(f"✅ CSV 내보내기 완료: {dir_path}")
        
        except Exception as e:
            log.error(f"❌ CSV 내보내기 실패: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "내보내기 실패",
                f"CSV 내보내기 중 오류가 발생했습니다:\n{str(e)}"
            )


# 테스트 코드
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 더미 DB (테스트용)
    db = TradingHistoryDB("test_trading_history.db")
    
    # 테스트 데이터 생성
    for i in range(10):
        position_id = db.start_position({
            'stock_code': f'00{i:04d}',
            'stock_name': f'테스트{i}',
            'entry_time': (datetime.now() - timedelta(days=10-i)).isoformat(),
            'entry_price': 10000 + i * 100,
            'quantity': 10,
            'total_invested': (10000 + i * 100) * 10,
            'entry_config': '{}'
        })
        
        profit = (i - 5) * 1000  # 일부는 수익, 일부는 손실
        
        db.close_position(position_id, {
            'exit_time': (datetime.now() - timedelta(days=i)).isoformat(),
            'exit_price': 10000 + i * 100 + profit,
            'exit_reason': '익절매' if profit > 0 else '손절매',
            'profit_loss': profit,
            'profit_loss_percent': (profit / (10000 + i * 100)) * 100,
            'holding_duration_seconds': 3600 * (10 - i),
            'exit_config': '{}'
        })
    
    widget = PerformanceChartWidget(db)
    widget.setWindowTitle("성과 분석 차트 테스트")
    widget.resize(1400, 800)
    widget.show()
    
    sys.exit(app.exec_())

