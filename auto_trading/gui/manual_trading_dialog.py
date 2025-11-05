"""
수동 거래 다이얼로그 모듈

[파일 역할]
HTS 없이 프로그램 내에서 수동으로 매매할 수 있는 다이얼로그입니다.

[주요 기능]
- 종목 검색 및 조회
- 실시간 시세 표시 (현재가, 등락률, 거래량)
- 호가 정보 표시 (매도/매수 호가 5단계)
- 보유 종목 표시
- 매수/매도 주문 전송

[사용 방법]
from manual_trading_dialog import ManualTradingDialog
dialog = ManualTradingDialog(kiwoom_api, parent=window)
dialog.exec_()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QRadioButton, QButtonGroup,
    QSpinBox, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from typing import Dict, Optional
from utils.logger import log


class ManualTradingDialog(QDialog):
    """수동 거래 다이얼로그"""
    
    def __init__(self, kiwoom_api, parent=None):
        super().__init__(parent)
        self.kiwoom = kiwoom_api
        self.current_stock_code = None
        self.current_stock_name = None
        self.current_price = 0
        
        self.setWindowTitle("수동 거래")
        self.setMinimumWidth(700)
        self.setMinimumHeight(800)
        
        self.init_ui()
        self.setup_realtime_callback()
        self.load_holdings()
        
        # 실시간 업데이트 타이머 (1초마다)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        
        # 종목 검색 영역
        search_group = self.create_search_group()
        main_layout.addWidget(search_group)
        
        # 현재 시세 정보 영역
        quote_group = self.create_quote_group()
        main_layout.addWidget(quote_group)
        
        # 호가 정보 영역
        orderbook_group = self.create_orderbook_group()
        main_layout.addWidget(orderbook_group)
        
        # 보유 종목 영역
        holdings_group = self.create_holdings_group()
        main_layout.addWidget(holdings_group)
        
        # 주문 영역
        order_group = self.create_order_group()
        main_layout.addWidget(order_group)
        
        # 닫기 버튼
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)
        
        self.setLayout(main_layout)
    
    def create_search_group(self) -> QGroupBox:
        """종목 검색 그룹"""
        group = QGroupBox("종목 검색")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("종목코드:"))
        
        self.stock_code_input = QLineEdit()
        self.stock_code_input.setPlaceholderText("예: 005930")
        self.stock_code_input.returnPressed.connect(self.search_stock)
        layout.addWidget(self.stock_code_input)
        
        search_button = QPushButton("조회")
        search_button.clicked.connect(self.search_stock)
        layout.addWidget(search_button)
        
        group.setLayout(layout)
        return group
    
    def create_quote_group(self) -> QGroupBox:
        """현재 시세 그룹"""
        group = QGroupBox("현재 시세")
        layout = QFormLayout()
        
        self.stock_name_label = QLabel("-")
        self.stock_name_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addRow("종목명:", self.stock_name_label)
        
        self.current_price_label = QLabel("-")
        self.current_price_label.setStyleSheet("font-size: 14pt;")
        layout.addRow("현재가:", self.current_price_label)
        
        self.change_rate_label = QLabel("-")
        layout.addRow("등락률:", self.change_rate_label)
        
        self.volume_label = QLabel("-")
        layout.addRow("거래량:", self.volume_label)
        
        group.setLayout(layout)
        return group
    
    def create_orderbook_group(self) -> QGroupBox:
        """호가 정보 그룹"""
        group = QGroupBox("호가 정보")
        layout = QVBoxLayout()
        
        # 호가 테이블
        self.orderbook_table = QTableWidget()
        self.orderbook_table.setColumnCount(3)
        self.orderbook_table.setHorizontalHeaderLabels(["구분", "가격", "수량"])
        self.orderbook_table.setRowCount(10)  # 매도5 + 매수5
        self.orderbook_table.setMaximumHeight(300)
        
        # 초기 데이터
        for i in range(5):
            self.orderbook_table.setItem(i, 0, QTableWidgetItem(f"매도{5-i}"))
            self.orderbook_table.setItem(i, 1, QTableWidgetItem("-"))
            self.orderbook_table.setItem(i, 2, QTableWidgetItem("-"))
        
        for i in range(5, 10):
            self.orderbook_table.setItem(i, 0, QTableWidgetItem(f"매수{i-4}"))
            self.orderbook_table.setItem(i, 1, QTableWidgetItem("-"))
            self.orderbook_table.setItem(i, 2, QTableWidgetItem("-"))
        
        layout.addWidget(self.orderbook_table)
        
        # 체결 강도
        self.execution_strength_label = QLabel("체결 강도: -")
        layout.addWidget(self.execution_strength_label)
        
        group.setLayout(layout)
        return group
    
    def create_holdings_group(self) -> QGroupBox:
        """보유 종목 그룹"""
        group = QGroupBox("보유 종목")
        layout = QVBoxLayout()
        
        self.holdings_table = QTableWidget()
        self.holdings_table.setColumnCount(4)
        self.holdings_table.setHorizontalHeaderLabels(["종목코드", "종목명", "수량", "평균가"])
        self.holdings_table.setMaximumHeight(150)
        
        layout.addWidget(self.holdings_table)
        
        group.setLayout(layout)
        return group
    
    def create_order_group(self) -> QGroupBox:
        """주문 그룹"""
        group = QGroupBox("주문")
        layout = QFormLayout()
        
        # 매수/매도 선택
        trade_type_layout = QHBoxLayout()
        self.buy_radio = QRadioButton("매수")
        self.sell_radio = QRadioButton("매도")
        self.buy_radio.setChecked(True)
        
        self.trade_type_group = QButtonGroup()
        self.trade_type_group.addButton(self.buy_radio, 1)
        self.trade_type_group.addButton(self.sell_radio, 2)
        
        trade_type_layout.addWidget(self.buy_radio)
        trade_type_layout.addWidget(self.sell_radio)
        trade_type_layout.addStretch()
        
        layout.addRow("구분:", trade_type_layout)
        
        # 가격 유형 (시장가/지정가)
        price_type_layout = QHBoxLayout()
        self.market_price_radio = QRadioButton("시장가")
        self.limit_price_radio = QRadioButton("지정가")
        self.market_price_radio.setChecked(True)
        self.market_price_radio.toggled.connect(self.on_price_type_changed)
        
        self.price_type_group = QButtonGroup()
        self.price_type_group.addButton(self.market_price_radio, 1)
        self.price_type_group.addButton(self.limit_price_radio, 2)
        
        price_type_layout.addWidget(self.market_price_radio)
        price_type_layout.addWidget(self.limit_price_radio)
        
        self.price_input = QSpinBox()
        self.price_input.setRange(0, 10000000)
        self.price_input.setSingleStep(100)
        self.price_input.setSuffix("원")
        self.price_input.setEnabled(False)
        self.price_input.valueChanged.connect(self.update_order_amount)
        
        price_type_layout.addWidget(self.price_input)
        price_type_layout.addStretch()
        
        layout.addRow("가격:", price_type_layout)
        
        # 수량
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100000)
        self.quantity_spin.setSingleStep(1)
        self.quantity_spin.setSuffix("주")
        self.quantity_spin.valueChanged.connect(self.update_order_amount)
        layout.addRow("수량:", self.quantity_spin)
        
        # 예상 금액
        self.order_amount_label = QLabel("0원")
        self.order_amount_label.setStyleSheet("font-weight: bold; color: blue;")
        layout.addRow("예상 금액:", self.order_amount_label)
        
        # 주문 버튼
        button_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("매수 주문")
        self.buy_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
        self.buy_button.clicked.connect(self.execute_buy_order)
        button_layout.addWidget(self.buy_button)
        
        self.sell_button = QPushButton("매도 주문")
        self.sell_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        self.sell_button.clicked.connect(self.execute_sell_order)
        button_layout.addWidget(self.sell_button)
        
        layout.addRow("", button_layout)
        
        group.setLayout(layout)
        return group
    
    def search_stock(self):
        """종목 조회"""
        stock_code = self.stock_code_input.text().strip()
        
        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력하세요.")
            return
        
        if len(stock_code) != 6 or not stock_code.isdigit():
            QMessageBox.warning(self, "입력 오류", "올바른 종목코드를 입력하세요. (6자리 숫자)")
            return
        
        try:
            # 종목 정보 조회
            stock_info = self.kiwoom.get_stock_info(stock_code)
            
            if stock_info:
                self.current_stock_code = stock_code
                self.current_stock_name = stock_info.get('name', stock_code)
                self.current_price = stock_info.get('current_price', 0)
                
                # UI 업데이트
                self.update_quote_display(stock_info)
                
                # 실시간 시세 등록
                self.register_realtime_data(stock_code)
                
                log.info(f"종목 조회 성공: {self.current_stock_name} ({stock_code})")
            else:
                QMessageBox.warning(self, "조회 실패", "종목 정보를 가져올 수 없습니다.")
                
        except Exception as e:
            log.error(f"종목 조회 오류: {e}")
            QMessageBox.critical(self, "오류", f"종목 조회 중 오류가 발생했습니다:\n{e}")
    
    def register_realtime_data(self, stock_code: str):
        """실시간 시세 등록"""
        try:
            # 실시간 시세 등록 (주식체결, 주식호가잔량)
            fid_list = "9001;10;11;12;13;14;15;16;17;18;19;20"  # 종목코드, 현재가, 전일대비 등
            self.kiwoom.ocx.dynamicCall(
                "SetRealReg(QString, QString, QString, QString)",
                "9999",  # 화면번호
                stock_code,
                fid_list,
                "1"  # 1=신규등록, 0=추가등록
            )
            log.info(f"실시간 시세 등록: {stock_code}")
        except Exception as e:
            log.error(f"실시간 시세 등록 오류: {e}")
    
    def setup_realtime_callback(self):
        """실시간 데이터 콜백 설정"""
        # kiwoom_api의 실시간 콜백에 이 다이얼로그를 연결
        # 실제로는 kiwoom_api의 _on_receive_real_data에서 처리
        pass
    
    def update_quote_display(self, stock_info: Dict):
        """시세 정보 표시 업데이트"""
        self.stock_name_label.setText(stock_info.get('name', '-'))
        
        current_price = stock_info.get('current_price', 0)
        self.current_price = current_price
        self.current_price_label.setText(f"{current_price:,}원")
        
        change_rate = stock_info.get('change_rate', 0)
        self.change_rate_label.setText(f"{change_rate:+.2f}%")
        if change_rate > 0:
            self.change_rate_label.setStyleSheet("color: red; font-weight: bold;")
        elif change_rate < 0:
            self.change_rate_label.setStyleSheet("color: blue; font-weight: bold;")
        else:
            self.change_rate_label.setStyleSheet("color: black;")
        
        volume = stock_info.get('volume', 0)
        self.volume_label.setText(f"{volume:,}주")
        
        # 시장가 주문 시 현재가로 자동 설정
        if self.market_price_radio.isChecked() and current_price > 0:
            self.update_order_amount()
    
    def load_holdings(self):
        """보유 종목 로드"""
        try:
            holdings = self.kiwoom.get_holdings()
            
            self.holdings_table.setRowCount(len(holdings))
            
            for row, holding in enumerate(holdings):
                self.holdings_table.setItem(row, 0, QTableWidgetItem(holding.get('code', '-')))
                self.holdings_table.setItem(row, 1, QTableWidgetItem(holding.get('name', '-')))
                self.holdings_table.setItem(row, 2, QTableWidgetItem(str(holding.get('quantity', 0))))
                self.holdings_table.setItem(row, 3, QTableWidgetItem(f"{holding.get('avg_price', 0):,}"))
            
        except Exception as e:
            log.error(f"보유 종목 로드 오류: {e}")
    
    def update_display(self):
        """주기적 디스플레이 업데이트"""
        # 보유 종목 갱신
        self.load_holdings()
    
    def on_price_type_changed(self):
        """가격 유형 변경 이벤트"""
        is_limit = self.limit_price_radio.isChecked()
        self.price_input.setEnabled(is_limit)
        
        if not is_limit:
            # 시장가일 때는 현재가 사용
            self.update_order_amount()
    
    def update_order_amount(self):
        """예상 주문 금액 업데이트"""
        quantity = self.quantity_spin.value()
        
        if self.market_price_radio.isChecked():
            # 시장가: 현재가 사용
            price = self.current_price
        else:
            # 지정가: 입력한 가격 사용
            price = self.price_input.value()
        
        amount = price * quantity
        self.order_amount_label.setText(f"{amount:,}원")
    
    def execute_buy_order(self):
        """매수 주문 실행"""
        if not self.current_stock_code:
            QMessageBox.warning(self, "주문 오류", "종목을 먼저 조회하세요.")
            return
        
        quantity = self.quantity_spin.value()
        
        if self.market_price_radio.isChecked():
            price = 0  # 시장가
            price_str = "시장가"
        else:
            price = self.price_input.value()
            price_str = f"{price:,}원"
        
        # 확인 메시지
        reply = QMessageBox.question(
            self,
            "매수 주문 확인",
            f"종목: {self.current_stock_name} ({self.current_stock_code})\n"
            f"수량: {quantity}주\n"
            f"가격: {price_str}\n\n"
            f"매수 주문하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                result = self.kiwoom.buy_order(self.current_stock_code, quantity, price)
                
                if result:
                    QMessageBox.information(self, "주문 성공", "매수 주문이 전송되었습니다.")
                    log.success(f"매수 주문 성공: {self.current_stock_code} {quantity}주 @ {price_str}")
                else:
                    QMessageBox.warning(self, "주문 실패", "매수 주문 전송에 실패했습니다.")
                    
            except Exception as e:
                log.error(f"매수 주문 오류: {e}")
                QMessageBox.critical(self, "오류", f"매수 주문 중 오류가 발생했습니다:\n{e}")
    
    def execute_sell_order(self):
        """매도 주문 실행"""
        if not self.current_stock_code:
            QMessageBox.warning(self, "주문 오류", "종목을 먼저 조회하세요.")
            return
        
        quantity = self.quantity_spin.value()
        
        if self.market_price_radio.isChecked():
            price = 0  # 시장가
            price_str = "시장가"
        else:
            price = self.price_input.value()
            price_str = f"{price:,}원"
        
        # 확인 메시지
        reply = QMessageBox.question(
            self,
            "매도 주문 확인",
            f"종목: {self.current_stock_name} ({self.current_stock_code})\n"
            f"수량: {quantity}주\n"
            f"가격: {price_str}\n\n"
            f"매도 주문하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                result = self.kiwoom.sell_order(self.current_stock_code, quantity, price)
                
                if result:
                    QMessageBox.information(self, "주문 성공", "매도 주문이 전송되었습니다.")
                    log.success(f"매도 주문 성공: {self.current_stock_code} {quantity}주 @ {price_str}")
                else:
                    QMessageBox.warning(self, "주문 실패", "매도 주문 전송에 실패했습니다.")
                    
            except Exception as e:
                log.error(f"매도 주문 오류: {e}")
                QMessageBox.critical(self, "오류", f"매도 주문 중 오류가 발생했습니다:\n{e}")
    
    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트"""
        self.update_timer.stop()
        
        # 실시간 시세 해제
        if self.current_stock_code:
            try:
                self.kiwoom.ocx.dynamicCall(
                    "SetRealRemove(QString, QString)",
                    "9999",  # 화면번호
                    self.current_stock_code
                )
            except:
                pass
        
        event.accept()


# 테스트 코드
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 더미 API (테스트용)
    class DummyKiwoom:
        def get_stock_info(self, stock_code):
            return {
                'name': '삼성전자',
                'current_price': 70000,
                'change_rate': 2.5,
                'volume': 1234567
            }
        
        def get_holdings(self):
            return [
                {'code': '005930', 'name': '삼성전자', 'quantity': 10, 'avg_price': 68000},
                {'code': '000660', 'name': 'SK하이닉스', 'quantity': 5, 'avg_price': 120000},
            ]
        
        def buy_order(self, code, quantity, price):
            return True
        
        def sell_order(self, code, quantity, price):
            return True
        
        class OCX:
            def dynamicCall(self, *args):
                pass
        
        ocx = OCX()
    
    dialog = ManualTradingDialog(DummyKiwoom())
    dialog.show()
    
    sys.exit(app.exec_())

