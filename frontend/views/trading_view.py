"""
매매 화면

[파일 역할]
주문 실행, 체결 내역, 관심 종목 관리
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox,
    QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class OrderForm(QFrame):
    """주문 폼 위젯"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.current_account_id = 1  # TODO: 실제 계좌 ID
        self.setup_ui()
    
    def setup_ui(self):
        """UI 초기화"""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QGridLayout(self)
        
        # 제목
        title = QLabel("주문 실행")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title, 0, 0, 1, 2)
        
        # 종목코드
        layout.addWidget(QLabel("종목코드:"), 1, 0)
        self.stock_code_input = QLineEdit()
        self.stock_code_input.setPlaceholderText("예: 005930")
        layout.addWidget(self.stock_code_input, 1, 1)
        
        # 종목명 (조회 버튼)
        self.stock_name_label = QLabel("")
        self.stock_name_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.stock_name_label, 2, 1)
        
        self.search_btn = QPushButton("🔍 조회")
        self.search_btn.clicked.connect(self.search_stock)
        layout.addWidget(self.search_btn, 2, 0)
        
        # 주문 유형
        layout.addWidget(QLabel("주문 유형:"), 3, 0)
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["매수", "매도"])
        layout.addWidget(self.order_type_combo, 3, 1)
        
        # 가격 유형
        layout.addWidget(QLabel("가격 유형:"), 4, 0)
        self.price_type_combo = QComboBox()
        self.price_type_combo.addItems(["시장가", "지정가"])
        self.price_type_combo.currentTextChanged.connect(self.on_price_type_changed)
        layout.addWidget(self.price_type_combo, 4, 1)
        
        # 수량
        layout.addWidget(QLabel("수량:"), 5, 0)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(1000000)
        self.quantity_input.setValue(10)
        layout.addWidget(self.quantity_input, 5, 1)
        
        # 가격 (지정가 시)
        layout.addWidget(QLabel("가격:"), 6, 0)
        self.price_input = QSpinBox()
        self.price_input.setMinimum(0)
        self.price_input.setMaximum(10000000)
        self.price_input.setSingleStep(100)
        self.price_input.setEnabled(False)
        layout.addWidget(self.price_input, 6, 1)
        
        # 주문 버튼
        button_layout = QHBoxLayout()
        
        self.buy_btn = QPushButton("매수")
        self.buy_btn.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        self.buy_btn.clicked.connect(lambda: self.execute_order("buy"))
        
        self.sell_btn = QPushButton("매도")
        self.sell_btn.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.sell_btn.clicked.connect(lambda: self.execute_order("sell"))
        
        button_layout.addWidget(self.buy_btn)
        button_layout.addWidget(self.sell_btn)
        
        layout.addLayout(button_layout, 7, 0, 1, 2)
    
    def on_price_type_changed(self, price_type: str):
        """가격 유형 변경 시"""
        self.price_input.setEnabled(price_type == "지정가")
    
    def search_stock(self):
        """종목 조회"""
        stock_code = self.stock_code_input.text().strip()
        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력하세요.")
            return
        
        try:
            stock_info = self.api_client.get_stock_info(stock_code)
            self.stock_name_label.setText(f"{stock_info.get('name', '(조회 실패)')}")
            self.price_input.setValue(stock_info.get('price', 0))
        except Exception as e:
            self.stock_name_label.setText("(조회 실패)")
            QMessageBox.warning(self, "오류", f"종목 조회 실패: {str(e)}")
    
    def execute_order(self, order_type: str):
        """주문 실행"""
        stock_code = self.stock_code_input.text().strip()
        stock_name = self.stock_name_label.text()
        
        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력하세요.")
            return
        
        quantity = self.quantity_input.value()
        price_type = "market" if self.price_type_combo.currentText() == "시장가" else "limit"
        price = None if price_type == "market" else self.price_input.value()
        
        # 확인 메시지
        order_text = f"매수" if order_type == "buy" else "매도"
        price_text = "시장가" if price_type == "market" else f"{price:,}원"
        
        reply = QMessageBox.question(
            self,
            "주문 확인",
            f"{stock_code} ({stock_name})\n"
            f"{order_text} {quantity:,}주 @ {price_text}\n\n"
            f"주문을 실행하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                result = self.api_client.create_order(
                    account_id=self.current_account_id,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    order_type=order_type,
                    price_type=price_type,
                    quantity=quantity,
                    price=price
                )
                
                QMessageBox.information(self, "주문 완료", "주문이 전송되었습니다.")
                self.clear_form()
                
            except Exception as e:
                QMessageBox.critical(self, "주문 실패", f"주문 실행 중 오류: {str(e)}")
    
    def clear_form(self):
        """폼 초기화"""
        self.stock_code_input.clear()
        self.stock_name_label.clear()
        self.quantity_input.setValue(10)
        self.price_input.setValue(0)


class TradingView(QWidget):
    """매매 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.current_account_id = 1  # TODO: 실제 계좌 ID
        self.setup_ui()
        
        # 자동 새로고침 타이머
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(3000)
        
        self.refresh_data()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        
        # 왼쪽: 주문 폼
        left_panel = QVBoxLayout()
        self.order_form = OrderForm(self.api_client)
        left_panel.addWidget(self.order_form)
        left_panel.addStretch()
        
        layout.addLayout(left_panel, 1)
        
        # 오른쪽: 주문 내역 및 체결 내역
        right_panel = QVBoxLayout()
        
        # 탭 위젯
        self.tabs = QTabWidget()
        
        # 주문 내역 탭
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(7)
        self.orders_table.setHorizontalHeaderLabels([
            "주문번호", "종목", "유형", "수량", "가격", "상태", "시간"
        ])
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.setAlternatingRowColors(True)
        self.tabs.addTab(self.orders_table, "주문 내역")
        
        # 체결 내역 탭
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels([
            "종목", "유형", "수량", "체결가", "손익", "시간"
        ])
        self.trades_table.horizontalHeader().setStretchLastSection(True)
        self.trades_table.setAlternatingRowColors(True)
        self.tabs.addTab(self.trades_table, "체결 내역")
        
        right_panel.addWidget(self.tabs)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_data)
        right_panel.addWidget(refresh_btn)
        
        layout.addLayout(right_panel, 2)
    
    def refresh_data(self):
        """데이터 새로고침"""
        try:
            # 주문 내역
            orders = self.api_client.get_orders(self.current_account_id)
            self.update_orders_table(orders)
            
            # 체결 내역
            trades = self.api_client.get_trades(self.current_account_id)
            self.update_trades_table(trades)
        
        except Exception as e:
            print(f"데이터 새로고침 오류: {e}")
    
    def update_orders_table(self, orders: list):
        """주문 내역 테이블 업데이트"""
        self.orders_table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.get('id', ''))))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.get('stock_code', '')))
            self.orders_table.setItem(row, 2, QTableWidgetItem(order.get('order_type', '')))
            self.orders_table.setItem(row, 3, QTableWidgetItem(f"{order.get('quantity', 0):,}"))
            self.orders_table.setItem(row, 4, QTableWidgetItem(f"{order.get('price', 0):,}"))
            self.orders_table.setItem(row, 5, QTableWidgetItem(order.get('status', '')))
            self.orders_table.setItem(row, 6, QTableWidgetItem(order.get('created_at', '')))
    
    def update_trades_table(self, trades: list):
        """체결 내역 테이블 업데이트"""
        self.trades_table.setRowCount(len(trades))
        
        for row, trade in enumerate(trades):
            self.trades_table.setItem(row, 0, QTableWidgetItem(trade.get('stock_code', '')))
            self.trades_table.setItem(row, 1, QTableWidgetItem(trade.get('trade_type', '')))
            self.trades_table.setItem(row, 2, QTableWidgetItem(f"{trade.get('quantity', 0):,}"))
            self.trades_table.setItem(row, 3, QTableWidgetItem(f"{trade.get('price', 0):,}"))
            self.trades_table.setItem(row, 4, QTableWidgetItem(f"{trade.get('profit_loss', 0):+,}"))
            self.trades_table.setItem(row, 5, QTableWidgetItem(trade.get('created_at', '')))
    
    def closeEvent(self, event):
        """종료 시 타이머 정리"""
        self.refresh_timer.stop()
        event.accept()

