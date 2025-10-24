"""
메인 윈도우

애플리케이션의 메인 윈도우입니다.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from ..services.websocket_manager import WebSocketManager


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self, api_client):
        super().__init__()
        
        self.api_client = api_client
        self.current_account_id = 1  # TODO: 로그인 후 설정
        
        # WebSocket Manager 초기화
        self.ws_manager = WebSocketManager()
        self.setup_websocket_handlers()
        
        self.setup_ui()
        self.load_initial_data()
        
        # WebSocket 연결 시작
        self.ws_manager.start()
    
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("CleonAI Trading Platform")
        self.setGeometry(100, 100, 1400, 900)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 상단 툴바
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 탭 추가 (임시 플레이스홀더)
        self.create_tabs()
        
        # 상태바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # 스타일 적용
        self.apply_stylesheet()
    
    def create_toolbar(self) -> QWidget:
        """툴바 생성"""
        toolbar = QWidget()
        toolbar.setMaximumHeight(60)
        layout = QHBoxLayout(toolbar)
        
        # 제목
        title = QLabel("CleonAI Trading Platform")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 계좌 정보 (임시)
        account_label = QLabel("계좌: 모의투자")
        layout.addWidget(account_label)
        
        # 잔고 (임시)
        balance_label = QLabel("잔고: 10,000,000원")
        layout.addWidget(balance_label)
        
        return toolbar
    
    def create_tabs(self):
        """탭 생성"""
        # 대시보드 탭
        from .dashboard_view import DashboardView
        dashboard_view = DashboardView(self.api_client)
        self.tabs.addTab(dashboard_view, "📊 대시보드")
        
        # 매매 탭
        from .trading_view import TradingView
        trading_view = TradingView(self.api_client)
        self.tabs.addTab(trading_view, "💰 매매")
        
        # 차트 탭
        from .chart_view import ChartView
        chart_view = ChartView(self.api_client)
        self.tabs.addTab(chart_view, "📈 차트")
        
        # 급등주 탭
        from .surge_monitor_view import SurgeMonitorView
        surge_view = SurgeMonitorView(self.api_client)
        self.tabs.addTab(surge_view, "🚀 급등주")
        
        # 설정 탭
        from .settings_view import SettingsView
        settings_view = SettingsView(self.api_client)
        self.tabs.addTab(settings_view, "⚙️ 설정")
        
        # 로그 탭
        from .logs_view import LogsView
        logs_view = LogsView(self.api_client)
        self.tabs.addTab(logs_view, "📝 로그")
    
    def apply_stylesheet(self):
        """스타일시트 적용"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QLabel {
                padding: 5px;
            }
        """)
    
    def load_initial_data(self):
        """초기 데이터 로드"""
        try:
            # 계좌 정보 로드
            accounts = self.api_client.get_accounts()
            if accounts:
                self.current_account_id = accounts[0]['id']
            
            # 잔고 조회
            balance = self.api_client.get_account_balance(self.current_account_id)
            
            self.status_bar.showMessage(f"데이터 로드 완료 | 잔고: {balance.get('current_balance', 0):,}원")
        
        except Exception as e:
            self.status_bar.showMessage(f"데이터 로드 실패: {str(e)}")
    
    def setup_websocket_handlers(self):
        """WebSocket 핸들러 설정"""
        # 실시간 시세 데이터
        self.ws_manager.market_data_received.connect(self.on_market_data)
        
        # 주문 업데이트
        self.ws_manager.order_update_received.connect(self.on_order_update)
        
        # 포지션 업데이트
        self.ws_manager.position_update_received.connect(self.on_position_update)
        
        # 급등주 알림
        self.ws_manager.surge_alert_received.connect(self.on_surge_alert)
    
    def on_market_data(self, data: dict):
        """실시간 시세 데이터 처리"""
        stock_code = data.get('stock_code')
        price = data.get('price')
        self.status_bar.showMessage(f"📈 {stock_code}: {price:,}원", 3000)
    
    def on_order_update(self, data: dict):
        """주문 업데이트 처리"""
        order_id = data.get('order_id')
        status = data.get('status')
        self.status_bar.showMessage(f"📋 주문 #{order_id}: {status}", 5000)
    
    def on_position_update(self, data: dict):
        """포지션 업데이트 처리"""
        stock_code = data.get('stock_code')
        quantity = data.get('quantity')
        self.status_bar.showMessage(f"💼 포지션 업데이트: {stock_code} {quantity}주", 5000)
    
    def on_surge_alert(self, data: dict):
        """급등주 알림 처리"""
        stock_code = data.get('stock_code')
        change_rate = data.get('change_rate', 0)
        self.status_bar.showMessage(f"🚀 급등주 감지: {stock_code} (+{change_rate:.2f}%)", 10000)
    
    def closeEvent(self, event):
        """종료 시 WebSocket 정리"""
        self.ws_manager.stop()
        event.accept()

