"""
실시간 모니터링 GUI 모듈

[파일 역할]
자동매매 프로그램의 실시간 상태를 GUI로 표시합니다.

[주요 기능]
- 실시간 잔고 표시
- 보유 종목 및 수익률 표시
- 급등주 감지 현황
- 최근 매매 내역
- 실시간 로그 표시

[사용 방법]
from monitor_gui import MonitorWindow
window = MonitorWindow(trading_engine)
window.show()
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QTableWidgetItem, QTextEdit, QGroupBox, QTabWidget,
    QPushButton, QMessageBox, QMenuBar, QAction, QCheckBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from typing import Optional
from market_scheduler import MarketScheduler, MarketState
from config import Config

# 차트 위젯 (선택적 로드)
try:
    from advanced_chart_widget import AdvancedChartWidget
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    print("⚠️  advanced_chart_widget.py를 로드할 수 없습니다.")

# 통계 위젯 (선택적 로드)
try:
    from statistics_widget import StatisticsWidget
    STATISTICS_AVAILABLE = True
except ImportError:
    STATISTICS_AVAILABLE = False
    print("⚠️  statistics_widget.py를 로드할 수 없습니다.")

# 설정 대화상자 (선택적 로드)
try:
    from settings_dialog import SettingsDialog
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    print("⚠️  settings_dialog.py를 로드할 수 없습니다.")


class MonitorWindow(QMainWindow):
    """실시간 모니터링 GUI 창"""
    
    def __init__(self, trading_engine, parent=None):
        super().__init__(parent)
        self.trading_engine = trading_engine
        self.chart_widget = None  # 차트 위젯 참조
        self.market_scheduler = MarketScheduler()  # 시장 스케줄러
        
        # 🆕 뉴스 크롤러 (선택적)
        self.news_crawler = None
        if Config.ENABLE_NEWS_ANALYSIS:
            try:
                from news_crawler import NewsCrawler
                self.news_crawler = NewsCrawler()
                print("✅ 뉴스 크롤러 초기화 완료")
            except Exception as e:
                print(f"⚠️  뉴스 크롤러 로드 실패: {e}")
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("CleonAI 자동매매 실시간 모니터")
        self.setGeometry(100, 100, 1200, 800)
        
        # 메인 위젯
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        
        # 탭 1: 모니터링
        monitoring_tab = self.create_monitoring_tab()
        self.tab_widget.addTab(monitoring_tab, "📊 모니터링")
        
        # 탭 2: 차트 (plotly + yfinance 사용 가능 시)
        if CHART_AVAILABLE:
            # trading_engine를 전달
            self.chart_widget = AdvancedChartWidget(self.trading_engine)
            self.tab_widget.addTab(self.chart_widget, "📈 차트")
            # 초기 관심 종목 등록
            self.initialize_chart_stocks()
        
        # 탭 3: 통계 (선택적)
        if STATISTICS_AVAILABLE:
            self.statistics_widget = StatisticsWidget(self.trading_engine)
            self.tab_widget.addTab(self.statistics_widget, "📊 통계")
        
        main_layout.addWidget(self.tab_widget)
        
        # 메뉴바 생성
        self.create_menu_bar()
        
        # 스타일 적용
        self.apply_styles()
    
    def create_monitoring_tab(self) -> QWidget:
        """모니터링 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 상단: 계좌 정보
        account_group = self.create_account_group()
        layout.addWidget(account_group)
        
        # 컨트롤: 자동매매 시작/중지 버튼
        control_group = self.create_control_group()
        layout.addWidget(control_group)
        
        # 중단: 보유 종목 / 급등주 현황
        middle_layout = QHBoxLayout()
        
        holdings_group = self.create_holdings_group()
        middle_layout.addWidget(holdings_group)
        
        surge_group = self.create_surge_group()
        middle_layout.addWidget(surge_group)
        
        layout.addLayout(middle_layout)
        
        # 하단: 실시간 로그
        log_group = self.create_log_group()
        layout.addWidget(log_group)
        
        return tab
    
    def initialize_chart_stocks(self):
        """차트에 초기 관심 종목 등록"""
        if not self.chart_widget:
            return
        
        # 관심 종목 추가
        for stock_code in self.trading_engine.watch_list:
            # 종목명 조회 시도
            stock_name = stock_code  # 기본값
            try:
                # 🆕 키움 API에서 종목명 조회
                if hasattr(self.trading_engine, 'kiwoom'):
                    fetched_name = self.trading_engine.kiwoom.get_stock_name(stock_code)
                    if fetched_name and fetched_name != stock_code:
                        stock_name = fetched_name
            except Exception as e:
                print(f"종목명 조회 실패 ({stock_code}): {e}")
            
            self.chart_widget.add_stock(stock_code, stock_name)
        
        # 🆕 보유 종목도 차트에 추가
        for stock_code, position in self.trading_engine.risk_manager.positions.items():
            self.chart_widget.add_stock(stock_code, position.stock_name)
    
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일")
        
        exit_action = QAction("종료", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 거래 메뉴
        trade_menu = menubar.addMenu("거래")
        
        manual_trade_action = QAction("💰 수동 거래...", self)
        manual_trade_action.triggered.connect(self.open_manual_trading)
        trade_menu.addAction(manual_trade_action)
        
        # 🆕 차트 메뉴
        chart_menu = menubar.addMenu("차트")
        
        naver_chart_action = QAction("📊 네이버 금융", self)
        naver_chart_action.triggered.connect(lambda: self.open_external_chart("naver"))
        chart_menu.addAction(naver_chart_action)
        
        yahoo_chart_action = QAction("📈 야후 파이낸스", self)
        yahoo_chart_action.triggered.connect(lambda: self.open_external_chart("yahoo"))
        chart_menu.addAction(yahoo_chart_action)
        
        tradingview_action = QAction("📉 TradingView", self)
        tradingview_action.triggered.connect(lambda: self.open_external_chart("tradingview"))
        chart_menu.addAction(tradingview_action)
        
        # 설정 메뉴
        if SETTINGS_AVAILABLE:
            settings_menu = menubar.addMenu("설정")
            
            configure_action = QAction("⚙️ 매매 설정...", self)
            configure_action.triggered.connect(self.open_settings_dialog)
            settings_menu.addAction(configure_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")
        
        about_action = QAction("정보", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def open_settings_dialog(self):
        """설정 대화상자 열기"""
        try:
            from config import Config
            
            dialog = SettingsDialog(Config, self)
            
            if dialog.exec_():
                # 설정 저장됨
                QMessageBox.information(
                    self,
                    "설정 적용",
                    "설정이 저장되었습니다.\n"
                    "변경사항을 적용하려면 프로그램을 재시작하세요."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"설정 대화상자를 열 수 없습니다:\n{e}"
            )
    
    def open_manual_trading(self):
        """수동 거래 다이얼로그 열기"""
        try:
            from manual_trading_dialog import ManualTradingDialog
            
            dialog = ManualTradingDialog(self.trading_engine.kiwoom, parent=self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"수동 거래 창을 열 수 없습니다:\n{e}"
            )
    
    def open_external_chart(self, chart_type: str):
        """
        외부 차트 사이트 열기
        
        Args:
            chart_type: 'naver', 'yahoo', 'tradingview'
        """
        import webbrowser
        
        urls = {
            'naver': 'https://finance.naver.com/sise/',
            'yahoo': 'https://finance.yahoo.com/',
            'tradingview': 'https://www.tradingview.com/chart/'
        }
        
        url = urls.get(chart_type, 'https://finance.naver.com')
        
        # 보유 종목이 있으면 첫 번째 종목으로 직접 이동
        positions = self.trading_engine.risk_manager.positions
        if positions and chart_type == 'naver':
            first_stock_code = list(positions.keys())[0]
            url = f'https://finance.naver.com/item/main.naver?code={first_stock_code}'
        
        try:
            webbrowser.open(url)
            self.add_log(f"외부 차트 열기: {chart_type.upper()}", "blue")
        except Exception as e:
            QMessageBox.warning(
                self,
                "오류",
                f"브라우저를 열 수 없습니다:\n{e}"
            )
    
    def show_about(self):
        """정보 대화상자"""
        QMessageBox.about(
            self,
            "CleonAI 자동매매 프로그램",
            "<h2>CleonAI 자동매매 프로그램</h2>"
            "<p>버전: 1.0.0</p>"
            "<p>키움증권 Open API 기반 자동매매 시스템</p>"
            "<hr>"
            "<p><b>주요 기능:</b></p>"
            "<ul>"
            "<li>실시간 가격 모니터링</li>"
            "<li>다중 전략 매매 신호</li>"
            "<li>리스크 관리 (손절/익절)</li>"
            "<li>급등주 자동 감지</li>"
            "<li>뉴스 감성 분석 (선택적)</li>"
            "</ul>"
            "<hr>"
            "<p><small>⚠️ 투자 책임은 본인에게 있습니다.</small></p>"
        )
        
    def create_account_group(self) -> QGroupBox:
        """계좌 정보 그룹 생성"""
        group = QGroupBox("💰 계좌 정보")
        layout = QHBoxLayout()
        
        # 시장 상태
        self.market_state_label = QLabel("시장 상태: 확인중...")
        self.market_state_label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        layout.addWidget(self.market_state_label)
        
        layout.addStretch()
        
        # 잔고
        self.balance_label = QLabel("잔고: 조회중...")
        self.balance_label.setFont(QFont("맑은 고딕", 14, QFont.Bold))
        layout.addWidget(self.balance_label)
        
        layout.addStretch()
        
        # 총 자산
        self.total_asset_label = QLabel("총 자산: 조회중...")
        self.total_asset_label.setFont(QFont("맑은 고딕", 14, QFont.Bold))
        layout.addWidget(self.total_asset_label)
        
        layout.addStretch()
        
        # 수익률
        self.profit_rate_label = QLabel("수익률: 0.00%")
        self.profit_rate_label.setFont(QFont("맑은 고딕", 14, QFont.Bold))
        layout.addWidget(self.profit_rate_label)
        
        group.setLayout(layout)
        return group
    
    def create_control_group(self) -> QGroupBox:
        """자동매매 컨트롤 그룹 생성"""
        group = QGroupBox("🎮 자동매매 제어")
        layout = QHBoxLayout()
        
        # 상태 표시 레이블
        self.trading_status_label = QLabel("⏸ 자동매매 중지됨")
        self.trading_status_label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        self.trading_status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.trading_status_label)
        
        layout.addStretch()
        
        # 시작 버튼
        self.start_button = QPushButton("▶ 자동매매 시작")
        self.start_button.setFont(QFont("맑은 고딕", 11, QFont.Bold))
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.start_button.clicked.connect(self.on_start_trading)
        layout.addWidget(self.start_button)
        
        # 중지 버튼
        self.stop_button = QPushButton("⏹ 자동매매 중지")
        self.stop_button.setFont(QFont("맑은 고딕", 11, QFont.Bold))
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.stop_button.clicked.connect(self.on_stop_trading)
        self.stop_button.setEnabled(False)  # 초기에는 비활성화
        layout.addWidget(self.stop_button)
        
        group.setLayout(layout)
        return group
    
    def create_holdings_group(self) -> QGroupBox:
        """보유 종목 그룹 생성"""
        group = QGroupBox("📊 보유 종목")
        layout = QVBoxLayout()
        
        # 테이블 생성
        self.holdings_table = QTableWidget()
        self.holdings_table.setColumnCount(10)
        self.holdings_table.setHorizontalHeaderLabels([
            "매도금지", "종목코드", "종목명", "수량", "평균가", "현재가", "수익률", "비중", "추가매수", "뉴스"
        ])
        self.holdings_table.horizontalHeader().setStretchLastSection(True)
        self.holdings_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.holdings_table)
        group.setLayout(layout)
        return group
    
    def create_surge_group(self) -> QGroupBox:
        """급등주 현황 그룹 생성"""
        group = QGroupBox("🚀 급등주 감지 현황")
        layout = QVBoxLayout()
        
        # 상태 레이블
        self.surge_status_label = QLabel("모니터링 중...")
        self.surge_status_label.setFont(QFont("맑은 고딕", 10))
        layout.addWidget(self.surge_status_label)
        
        # 테이블 생성
        self.surge_table = QTableWidget()
        self.surge_table.setColumnCount(4)
        self.surge_table.setHorizontalHeaderLabels([
            "종목명", "현재가", "상승률", "거래량비율"
        ])
        self.surge_table.horizontalHeader().setStretchLastSection(True)
        self.surge_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.surge_table)
        group.setLayout(layout)
        return group
    
    def create_log_group(self) -> QGroupBox:
        """로그 그룹 생성"""
        group = QGroupBox("📝 실시간 로그 (최근 20개)")
        layout = QVBoxLayout()
        
        # 텍스트 에디터
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Consolas", 9))
        
        layout.addWidget(self.log_text)
        group.setLayout(layout)
        return group
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                font-size: 10pt;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
    
    def setup_timer(self):
        """업데이트 타이머 설정"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # 1초마다 업데이트
        
    def update_display(self):
        """화면 업데이트"""
        try:
            # 시장 상태 업데이트
            self.update_market_state()
            
            # 계좌 정보 업데이트
            self.update_account_info()
            
            # 보유 종목 업데이트
            self.update_holdings()
            
            # 급등주 현황 업데이트
            self.update_surge_status()
            
        except Exception as e:
            self.add_log(f"❌ 화면 업데이트 오류: {e}", "red")
    
    def update_market_state(self):
        """시장 상태 업데이트"""
        try:
            market_state = self.market_scheduler.get_current_market_state()
            
            # 상태별 색상 및 텍스트
            state_colors = {
                MarketState.OPEN: ("🟢 정규장", "green"),
                MarketState.PRE_OPEN: ("🟡 장시작전", "orange"),
                MarketState.AFTER_HOURS: ("⚡ 시간외거래", "darkorange"),
                MarketState.CLOSED: ("🔴 장마감", "red"),
                MarketState.WEEKEND: ("🔵 주말", "blue"),
                MarketState.HOLIDAY: ("🟣 공휴일", "purple"),
            }
            
            state_text, color = state_colors.get(market_state, (market_state.value, "gray"))
            
            # 시간 정보 추가
            if market_state in [MarketState.CLOSED, MarketState.WEEKEND, MarketState.HOLIDAY]:
                minutes_until_open = self.market_scheduler.get_time_until_market_open()
                hours = minutes_until_open // 60
                mins = minutes_until_open % 60
                state_text += f" ({hours}시간 {mins}분 후 개장)"
            elif market_state == MarketState.OPEN:
                minutes_until_close = self.market_scheduler.get_time_until_market_close()
                hours = minutes_until_close // 60
                mins = minutes_until_close % 60
                state_text += f" ({hours}시간 {mins}분 후 마감)"
            elif market_state == MarketState.PRE_OPEN:
                minutes_until_open = self.market_scheduler.get_time_until_market_open()
                state_text += f" ({minutes_until_open}분 후 개장)"
            elif market_state == MarketState.AFTER_HOURS:
                # 🆕 시간외 거래 시간 표시
                from datetime import datetime
                current_time = datetime.now().time()
                after_hours_end = datetime.strptime(Config.MARKET_AFTER_HOURS_END, "%H:%M").time()
                time_diff = datetime.combine(datetime.today(), after_hours_end) - datetime.combine(datetime.today(), current_time)
                minutes_until_close = int(time_diff.total_seconds() / 60)
                hours = minutes_until_close // 60
                mins = minutes_until_close % 60
                state_text += f" ({hours}시간 {mins}분 후 종료)"
            
            self.market_state_label.setText(f"시장: {state_text}")
            self.market_state_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
        except Exception as e:
            self.market_state_label.setText("시장 상태: 오류")
    
    def update_account_info(self):
        """계좌 정보 업데이트"""
        try:
            stats = self.trading_engine.risk_manager.get_statistics()
            
            # 잔고
            balance = stats.get('current_balance', 0)
            self.balance_label.setText(f"잔고: {balance:,}원")
            
            # 총 자산 (잔고 + 보유 종목 평가액)
            positions_value = sum(
                p.quantity * p.current_price
                for p in self.trading_engine.risk_manager.positions.values()
            )
            total_asset = balance + positions_value
            
            # 수수료 정보 포함
            total_fees = stats.get('total_fees_paid', 0)
            if total_fees > 0:
                self.total_asset_label.setText(
                    f"총 자산: {total_asset:,}원 (수수료: {total_fees:,}원)"
                )
            else:
                self.total_asset_label.setText(f"총 자산: {total_asset:,}원")
            
            # 수익률
            total_profit_loss = stats.get('total_profit_loss', 0)
            initial_balance = stats.get('initial_balance', 10000000)
            profit_rate = (total_profit_loss / initial_balance) * 100 if initial_balance > 0 else 0
            
            self.profit_rate_label.setText(f"수익률: {profit_rate:+.2f}%")
            
            # 색상 변경
            if profit_rate >= 0:
                self.profit_rate_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.profit_rate_label.setStyleSheet("color: blue; font-weight: bold;")
                
        except Exception as e:
            self.add_log(f"계좌 정보 업데이트 오류: {e}", "red")
    
    def update_holdings(self):
        """보유 종목 업데이트"""
        try:
            positions = self.trading_engine.risk_manager.positions
            
            self.holdings_table.setRowCount(len(positions))
            
            # 총 자산 계산 (잔고 + 보유 종목 평가액)
            balance = self.trading_engine.risk_manager.current_balance
            positions_value = sum(
                p.quantity * p.current_price
                for p in positions.values()
            )
            total_asset = balance + positions_value
            
            for row, (stock_code, position) in enumerate(positions.items()):
                # 현재가는 position.current_price 사용 (실시간 업데이트됨)
                current_price = position.current_price
                
                # 차트에 데이터 업데이트
                if self.chart_widget:
                    self.chart_widget.update_price_data(stock_code, current_price)
                
                # 수익률 계산 (평균가 기준)
                profit_rate = ((current_price - position.avg_price) / position.avg_price) * 100
                
                # 종목 평가액
                position_value = position.quantity * current_price
                
                # 총 자산 대비 비중 계산
                weight_pct = (position_value / total_asset * 100) if total_asset > 0 else 0
                
                # 🆕 매도 금지 체크박스
                checkbox = QCheckBox()
                checkbox.setChecked(position.sell_blocked)
                checkbox.stateChanged.connect(lambda state, code=stock_code: self.on_sell_block_changed(code, state))
                # 체크박스를 중앙 정렬하기 위한 위젯
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.holdings_table.setCellWidget(row, 0, checkbox_widget)
                
                # 테이블 업데이트 (인덱스 +1)
                self.holdings_table.setItem(row, 1, QTableWidgetItem(stock_code))
                self.holdings_table.setItem(row, 2, QTableWidgetItem(position.stock_name))
                self.holdings_table.setItem(row, 3, QTableWidgetItem(str(position.quantity)))
                self.holdings_table.setItem(row, 4, QTableWidgetItem(f"{position.avg_price:,}"))
                self.holdings_table.setItem(row, 5, QTableWidgetItem(f"{current_price:,}"))
                
                # 수익률 아이템 (색상 적용)
                profit_item = QTableWidgetItem(f"{profit_rate:+.2f}%")
                if profit_rate >= 0:
                    profit_item.setForeground(QColor(255, 0, 0))  # 빨간색
                else:
                    profit_item.setForeground(QColor(0, 0, 255))  # 파란색
                self.holdings_table.setItem(row, 6, profit_item)
                
                # 비중 표시
                weight_item = QTableWidgetItem(f"{weight_pct:.1f}%")
                self.holdings_table.setItem(row, 7, weight_item)
                
                # 추가 매수 횟수
                avg_down_text = f"{position.average_down_count}회" if position.average_down_count > 0 else "-"
                self.holdings_table.setItem(row, 8, QTableWidgetItem(avg_down_text))
                
                # 🆕 뉴스 요약
                news_summary = self.get_news_summary(stock_code)
                self.holdings_table.setItem(row, 9, QTableWidgetItem(news_summary))
            
            # 전체 수익률 차트 업데이트
            if self.chart_widget and positions:
                stats = self.trading_engine.risk_manager.get_statistics()
                total_profit_loss = stats.get('total_profit_loss', 0)
                initial_balance = stats.get('initial_balance', 10000000)
                profit_rate = (total_profit_loss / initial_balance) * 100 if initial_balance > 0 else 0
                
                # 누적 수익률 업데이트
                self.chart_widget.update_profit_data(profit_rate, profit_rate)
                
        except Exception as e:
            self.add_log(f"보유 종목 업데이트 오류: {e}", "red")
    
    def on_sell_block_changed(self, stock_code: str, state: int):
        """매도 금지 체크박스 상태 변경 처리"""
        try:
            position = self.trading_engine.risk_manager.positions.get(stock_code)
            if position:
                position.sell_blocked = (state == Qt.Checked)
                status = "활성화" if position.sell_blocked else "해제"
                self.add_log(f"매도 금지 {status}: {position.stock_name}({stock_code})", "orange")
        except Exception as e:
            self.add_log(f"매도 금지 설정 오류: {e}", "red")
    
    def get_news_summary(self, stock_code: str) -> str:
        """종목의 최신 뉴스 요약 가져오기"""
        try:
            # 뉴스 크롤러가 없거나 뉴스 분석이 비활성화된 경우
            if not hasattr(self, 'news_crawler') or not self.news_crawler:
                return "-"
            
            # 캐시된 뉴스 먼저 확인
            news_list = self.news_crawler.get_cached_news(stock_code)
            
            # 캐시에 없으면 최신 뉴스 1개만 조회 (과부하 방지)
            if not news_list:
                news_list = self.news_crawler.get_latest_news(stock_code, max_count=1)
            
            # 뉴스가 있으면 제목 표시
            if news_list:
                latest = news_list[0]
                title = latest.title[:30] + "..." if len(latest.title) > 30 else latest.title
                return title
            else:
                return "-"
                
        except Exception as e:
            # 에러 발생 시 조용히 처리 (GUI 업데이트 실패 방지)
            return "-"
    
    def update_surge_status(self):
        """급등주 현황 업데이트"""
        try:
            if not self.trading_engine.surge_detector:
                self.surge_status_label.setText("급등주 감지 비활성화")
                return
            
            stats = self.trading_engine.surge_detector.get_statistics()
            
            # 상태 레이블 업데이트
            status_text = (
                f"후보군: {stats.get('candidate_count', 0)}개 | "
                f"감지: {stats.get('detected_count', 0)}개 | "
                f"추가: {len(self.trading_engine.surge_detected_stocks)}개"
            )
            self.surge_status_label.setText(status_text)
            
            # 테이블은 필요 시 구현 (현재는 간단히 표시)
            
        except Exception as e:
            self.add_log(f"급등주 현황 업데이트 오류: {e}", "red")
    
    def add_log(self, message: str, color: str = "black"):
        """로그 추가"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # HTML 형식으로 색상 적용
            html_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
            
            # 텍스트 추가
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.End)
            self.log_text.setTextCursor(cursor)
            self.log_text.insertHtml(html_message + "<br>")
            
            # 스크롤을 최하단으로
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
            # 최대 줄 수 제한 (메모리 관리)
            lines = self.log_text.toPlainText().split('\n')
            if len(lines) > 100:
                # 처음 50줄만 남기고 삭제
                self.log_text.setPlainText('\n'.join(lines[-50:]))
                
        except Exception as e:
            print(f"로그 추가 오류: {e}")
    
    def on_start_trading(self):
        """자동매매 시작 버튼 클릭"""
        try:
            if not self.trading_engine.is_running:
                self.add_log("🚀 자동매매를 시작합니다...", "green")
                self.trading_engine.start_trading()
                self.update_control_buttons()
                self.add_log("✅ 자동매매가 시작되었습니다!", "green")
            else:
                self.add_log("⚠️ 이미 자동매매가 실행 중입니다.", "orange")
        except Exception as e:
            self.add_log(f"❌ 자동매매 시작 오류: {e}", "red")
            QMessageBox.critical(self, "오류", f"자동매매 시작 중 오류가 발생했습니다:\n{e}")
    
    def on_stop_trading(self):
        """자동매매 중지 버튼 클릭"""
        try:
            if self.trading_engine.is_running:
                reply = QMessageBox.question(
                    self,
                    "자동매매 중지",
                    "자동매매를 중지하시겠습니까?\n\n"
                    "진행 중인 주문은 취소되지 않으며,\n"
                    "새로운 매매 신호 생성만 중지됩니다.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.add_log("⏸ 자동매매를 중지합니다...", "orange")
                    self.trading_engine.stop_trading()
                    self.update_control_buttons()
                    self.add_log("✅ 자동매매가 중지되었습니다.", "gray")
            else:
                self.add_log("⚠️ 자동매매가 실행 중이 아닙니다.", "orange")
        except Exception as e:
            self.add_log(f"❌ 자동매매 중지 오류: {e}", "red")
            QMessageBox.critical(self, "오류", f"자동매매 중지 중 오류가 발생했습니다:\n{e}")
    
    def update_control_buttons(self):
        """컨트롤 버튼 상태 업데이트"""
        try:
            is_running = self.trading_engine.is_running
            
            # 버튼 활성화/비활성화
            self.start_button.setEnabled(not is_running)
            self.stop_button.setEnabled(is_running)
            
            # 상태 레이블 업데이트
            if is_running:
                self.trading_status_label.setText("▶ 자동매매 실행 중")
                self.trading_status_label.setStyleSheet("color: green;")
            else:
                self.trading_status_label.setText("⏸ 자동매매 중지됨")
                self.trading_status_label.setStyleSheet("color: gray;")
        except Exception as e:
            print(f"컨트롤 버튼 업데이트 오류: {e}")
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        self.update_timer.stop()
        event.accept()


# 테스트 코드
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 더미 엔진 (테스트용)
    class DummyEngine:
        class DummyRiskManager:
            def get_statistics(self):
                return {
                    'current_balance': 9500000,
                    'initial_balance': 10000000,
                    'total_profit': -500000
                }
            positions = {}
        
        risk_manager = DummyRiskManager()
        price_history = {}
        surge_detected_stocks = set()
        surge_detector = None
    
    window = MonitorWindow(DummyEngine())
    window.show()
    
    sys.exit(app.exec_())

