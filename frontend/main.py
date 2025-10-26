"""
CleonAI Trading Platform - 메인 애플리케이션
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QStatusBar, QTextEdit, QGroupBox, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

# API 클라이언트
from services.api_client import APIClient


class SimpleDashboard(QWidget):
    """간단한 대시보드"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
        
        # 자동 새로고침
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)  # 5초마다
        
        # 초기 로드
        QTimer.singleShot(100, self.refresh)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 제목
        title = QLabel("💰 계좌 정보")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 계좌 정보 표시
        self.info_label = QLabel("로딩 중...")
        self.info_label.setStyleSheet("font-size: 14px; padding: 10px; background: white; border-radius: 5px;")
        layout.addWidget(self.info_label)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(refresh_btn)
        
        # 결과 표시
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas, monospace;
            }
        """)
        layout.addWidget(self.result_text)
    
    def refresh(self):
        """데이터 새로고침"""
        try:
            # 계좌 정보 조회
            accounts = self.api_client.get_accounts()
            
            if accounts:
                account = accounts[0]
                
                # 계좌 타입 표시 (simulation/real)
                account_type = account.get('account_type', 'unknown')
                account_type_text = "🎮 모의투자" if account_type == "simulation" else "💼 실계좌"
                
                # account_number 호환성 유지 (account_no 우선)
                account_no = account.get('account_no') or account.get('account_number', 'N/A')
                
                info_text = f"""
📊 브로커: {account.get('broker', 'N/A')}
💳 계좌번호: {account_no}
{account_type_text}
💰 잔고: {account.get('balance', 0):,}원
                """
                self.info_label.setText(info_text)
                
                # 결과창에 상세 정보
                from PySide6.QtCore import QTime
                current_time = QTime.currentTime().toString("hh:mm:ss")
                self.result_text.append(f"\n=== {current_time} 업데이트 ===")
                self.result_text.append(f"✅ 계좌 조회 성공")
                self.result_text.append(f"   브로커: {account.get('broker')}")
                self.result_text.append(f"   계좌번호: {account_no}")
                self.result_text.append(f"   계좌타입: {account_type_text}")
                self.result_text.append(f"   잔고: {account.get('balance'):,}원")
            else:
                self.info_label.setText("⚠️ 계좌 정보 없음")
                self.result_text.append("⚠️ 계좌 정보를 불러올 수 없습니다")
                
        except Exception as e:
            self.info_label.setText(f"❌ 오류: {str(e)}")
            self.result_text.append(f"❌ 오류: {str(e)}")


class SimpleTrading(QWidget):
    """간단한 매매 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 제목
        title = QLabel("💰 주문 테스트")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 주문 폼
        form_group = QGroupBox("주문 정보")
        form_layout = QVBoxLayout()
        
        # 종목코드
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("종목코드:"))
        self.code_input = QLineEdit("005930")
        code_layout.addWidget(self.code_input)
        form_layout.addLayout(code_layout)
        
        # 수량
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("수량:"))
        self.qty_input = QLineEdit("10")
        qty_layout.addWidget(self.qty_input)
        form_layout.addLayout(qty_layout)
        
        # 가격
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("가격:"))
        self.price_input = QLineEdit("70000")
        price_layout.addWidget(self.price_input)
        form_layout.addLayout(price_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 버튼
        btn_layout = QHBoxLayout()
        
        buy_btn = QPushButton("💰 매수")
        buy_btn.clicked.connect(lambda: self.place_order("buy"))
        buy_btn.setStyleSheet("background: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        btn_layout.addWidget(buy_btn)
        
        sell_btn = QPushButton("💸 매도")
        sell_btn.clicked.connect(lambda: self.place_order("sell"))
        sell_btn.setStyleSheet("background: #f44336; color: white; padding: 10px; border-radius: 5px;")
        btn_layout.addWidget(sell_btn)
        
        layout.addLayout(btn_layout)
        
        # 결과
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("background: white; border: 1px solid #ddd; padding: 10px;")
        layout.addWidget(self.result_text)
    
    def place_order(self, order_type):
        """주문 실행"""
        try:
            code = self.code_input.text()
            qty = int(self.qty_input.text())
            price = int(self.price_input.text())
            
            self.result_text.append(f"\n=== 주문 시도 ===")
            self.result_text.append(f"종목: {code}")
            self.result_text.append(f"유형: {order_type}")
            self.result_text.append(f"수량: {qty}주")
            self.result_text.append(f"가격: {price:,}원")
            self.result_text.append(f"총액: {qty * price:,}원")
            self.result_text.append(f"✅ 주문 정보 확인 완료 (실제 주문은 Backend 연동 필요)")
            
        except Exception as e:
            self.result_text.append(f"❌ 오류: {str(e)}")


class SimpleTest(QWidget):
    """간단한 테스트 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 제목
        title = QLabel("🔍 Backend API 테스트")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 버튼들
        btn_layout = QVBoxLayout()
        
        test_btn = QPushButton("✅ Health Check")
        test_btn.clicked.connect(self.test_health)
        test_btn.setStyleSheet("padding: 10px; margin: 5px;")
        btn_layout.addWidget(test_btn)
        
        account_btn = QPushButton("💰 계좌 조회")
        account_btn.clicked.connect(self.test_account)
        account_btn.setStyleSheet("padding: 10px; margin: 5px;")
        btn_layout.addWidget(account_btn)
        
        docs_btn = QPushButton("📚 API 문서 열기")
        docs_btn.clicked.connect(self.open_docs)
        docs_btn.setStyleSheet("padding: 10px; margin: 5px;")
        btn_layout.addWidget(docs_btn)
        
        layout.addLayout(btn_layout)
        
        # 결과
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("background: white; border: 1px solid #ddd; padding: 10px; font-family: Consolas;")
        layout.addWidget(self.result_text)
    
    def test_health(self):
        """Health check"""
        try:
            self.result_text.append("\n=== Health Check ===")
            health = self.api_client.check_health()
            if health:
                self.result_text.append(f"✅ 상태: {health.get('status')}")
                self.result_text.append(f"🌐 환경: {health.get('environment')}")
            else:
                self.result_text.append("❌ Backend 응답 없음")
        except Exception as e:
            self.result_text.append(f"❌ 오류: {str(e)}")
    
    def test_account(self):
        """계좌 조회"""
        try:
            self.result_text.append("\n=== 계좌 조회 ===")
            accounts = self.api_client.get_accounts()
            self.result_text.append(f"✅ 계좌 수: {len(accounts)}")
            for acc in accounts:
                self.result_text.append(f"  - {acc.get('broker')}: {acc.get('account_number')}")
                self.result_text.append(f"    잔고: {acc.get('balance'):,}원")
        except Exception as e:
            self.result_text.append(f"❌ 오류: {str(e)}")
    
    def open_docs(self):
        """API 문서"""
        import webbrowser
        webbrowser.open("http://localhost:8000/docs")
        self.result_text.append("\n📚 브라우저에서 API 문서를 열었습니다")


class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CleonAI Trading Platform")
        self.setGeometry(100, 100, 1200, 800)
        
        # API 클라이언트 초기화
        self.api_client = APIClient("http://localhost:8000")
        
        # UI 설정
        self.setup_ui()
        
        # 연결 확인 (논블로킹)
        QTimer.singleShot(1000, self.start_connection_check)
    
    def start_connection_check(self):
        """연결 확인 시작"""
        self.check_connection()
        # 10초마다 체크
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(10000)
    
    def setup_ui(self):
        """UI 구성"""
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 10px 20px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #2196F3;
            }
        """)
        layout.addWidget(self.tabs)
        
        # 탭 추가
        self.tabs.addTab(SimpleDashboard(self.api_client), "📊 대시보드")
        self.tabs.addTab(SimpleTrading(self.api_client), "💰 매매")
        self.tabs.addTab(SimpleTest(self.api_client), "🔍 테스트")
        
        # 상태바
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("준비 중...")
    
    def check_connection(self):
        """Backend 연결 확인"""
        from PySide6.QtCore import QThread, Signal
        
        class ConnectionChecker(QThread):
            result = Signal(bool, str)
            
            def __init__(self, api_client):
                super().__init__()
                self.api_client = api_client
            
            def run(self):
                try:
                    health = self.api_client.check_health()
                    if health and health.get('status') == 'healthy':
                        self.result.emit(True, "Backend 연결됨")
                    else:
                        self.result.emit(False, "Backend 응답 오류")
                except Exception as e:
                    self.result.emit(False, f"연결 안됨")
        
        if hasattr(self, '_checker') and self._checker and self._checker.isRunning():
            return
        
        self._checker = ConnectionChecker(self.api_client)
        self._checker.result.connect(self.on_connection_result)
        self._checker.start()
    
    def on_connection_result(self, success: bool, message: str):
        """연결 결과"""
        if success:
            self.statusBar.showMessage(f"✅ {message}")
            self.statusBar.setStyleSheet("background-color: #d4edda; color: #155724;")
        else:
            self.statusBar.showMessage(f"❌ {message}")
            self.statusBar.setStyleSheet("background-color: #f8d7da; color: #721c24;")


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
