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


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self, api_client):
        super().__init__()
        
        self.api_client = api_client
        self.current_account_id = 1  # TODO: 로그인 후 설정
        
        self.setup_ui()
        self.load_initial_data()
    
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
        dashboard_tab = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_tab)
        dashboard_layout.addWidget(QLabel("대시보드 (개발 중)", alignment=Qt.AlignCenter))
        self.tabs.addTab(dashboard_tab, "대시보드")
        
        # 매매 탭
        trading_tab = QWidget()
        trading_layout = QVBoxLayout(trading_tab)
        trading_layout.addWidget(QLabel("매매 화면 (개발 중)", alignment=Qt.AlignCenter))
        self.tabs.addTab(trading_tab, "매매")
        
        # 차트 탭
        chart_tab = QWidget()
        chart_layout = QVBoxLayout(chart_tab)
        chart_layout.addWidget(QLabel("차트 (개발 중)", alignment=Qt.AlignCenter))
        self.tabs.addTab(chart_tab, "차트")
        
        # 급등주 탭
        surge_tab = QWidget()
        surge_layout = QVBoxLayout(surge_tab)
        surge_layout.addWidget(QLabel("급등주 모니터 (개발 중)", alignment=Qt.AlignCenter))
        self.tabs.addTab(surge_tab, "급등주")
        
        # 설정 탭
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.addWidget(QLabel("설정 (개발 중)", alignment=Qt.AlignCenter))
        self.tabs.addTab(settings_tab, "설정")
    
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

