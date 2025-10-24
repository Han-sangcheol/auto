"""
대시보드 화면

[파일 역할]
포지션 현황, 수익률, 계좌 정보를 표시하는 메인 대시보드
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor


class StatCard(QFrame):
    """통계 카드 위젯"""
    
    def __init__(self, title: str, value: str, color: str = "#2196F3"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border: 2px solid {color};
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(title_label)
        
        # 값
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)
    
    def update_value(self, value: str):
        """값 업데이트"""
        self.value_label.setText(value)


class DashboardView(QWidget):
    """대시보드 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
        
        # 자동 새로고침 타이머 (5초마다)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)
        
        # 초기 데이터 로드
        self.refresh_data()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 상단: 통계 카드
        stats_layout = QHBoxLayout()
        
        self.balance_card = StatCard("현금 잔고", "0원", "#2196F3")
        self.total_value_card = StatCard("총 평가액", "0원", "#4CAF50")
        self.profit_card = StatCard("총 손익", "0원", "#FF9800")
        self.profit_rate_card = StatCard("수익률", "0.00%", "#9C27B0")
        
        stats_layout.addWidget(self.balance_card)
        stats_layout.addWidget(self.total_value_card)
        stats_layout.addWidget(self.profit_card)
        stats_layout.addWidget(self.profit_rate_card)
        
        layout.addLayout(stats_layout)
        
        # 중단: 보유 포지션 테이블
        positions_label = QLabel("보유 포지션")
        positions_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(positions_label)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(7)
        self.positions_table.setHorizontalHeaderLabels([
            "종목코드", "종목명", "수량", "평균단가", "현재가", "손익", "수익률"
        ])
        self.positions_table.horizontalHeader().setStretchLastSection(True)
        self.positions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.positions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.positions_table.setAlternatingRowColors(True)
        
        # 헤더 스타일
        self.positions_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.positions_table)
        
        # 하단: 컨트롤 버튼
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
    
    def refresh_data(self):
        """데이터 새로고침"""
        try:
            # 계좌 정보 조회
            accounts = self.api_client.get_accounts()
            if accounts:
                account_id = accounts[0]['id']
                
                # 잔고 조회
                balance = self.api_client.get_account_balance(account_id)
                self.update_balance_info(balance)
                
                # 포지션 조회
                positions = self.api_client.get_positions(account_id)
                self.update_positions_table(positions)
        
        except Exception as e:
            print(f"데이터 새로고침 오류: {e}")
    
    def update_balance_info(self, balance: dict):
        """잔고 정보 업데이트"""
        current_balance = balance.get('current_balance', 0)
        stock_value = balance.get('stock_value', 0)
        total_value = balance.get('total_value', 0)
        profit_loss = balance.get('profit_loss', 0)
        profit_loss_pct = balance.get('profit_loss_percent', 0.0)
        
        self.balance_card.update_value(f"{current_balance:,}원")
        self.total_value_card.update_value(f"{total_value:,}원")
        
        # 손익에 따라 색상 변경
        profit_color = "#F44336" if profit_loss < 0 else "#4CAF50"
        self.profit_card.value_label.setStyleSheet(
            f"color: {profit_color}; font-size: 24px; font-weight: bold;"
        )
        self.profit_card.update_value(f"{profit_loss:+,}원")
        
        self.profit_rate_card.value_label.setStyleSheet(
            f"color: {profit_color}; font-size: 24px; font-weight: bold;"
        )
        self.profit_rate_card.update_value(f"{profit_loss_pct:+.2f}%")
    
    def update_positions_table(self, positions: list):
        """포지션 테이블 업데이트"""
        self.positions_table.setRowCount(len(positions))
        
        for row, pos in enumerate(positions):
            # 종목코드
            self.positions_table.setItem(row, 0, QTableWidgetItem(pos.get('stock_code', '')))
            
            # 종목명
            self.positions_table.setItem(row, 1, QTableWidgetItem(pos.get('stock_name', '')))
            
            # 수량
            quantity = pos.get('quantity', 0)
            self.positions_table.setItem(row, 2, QTableWidgetItem(f"{quantity:,}"))
            
            # 평균단가
            avg_price = pos.get('avg_price', 0)
            self.positions_table.setItem(row, 3, QTableWidgetItem(f"{avg_price:,}"))
            
            # 현재가
            current_price = pos.get('current_price', 0)
            self.positions_table.setItem(row, 4, QTableWidgetItem(f"{current_price:,}"))
            
            # 손익
            profit_loss = pos.get('profit_loss', 0)
            profit_item = QTableWidgetItem(f"{profit_loss:+,}")
            profit_color = QColor("#F44336") if profit_loss < 0 else QColor("#4CAF50")
            profit_item.setForeground(profit_color)
            self.positions_table.setItem(row, 5, profit_item)
            
            # 수익률
            profit_rate = pos.get('profit_loss_percent', 0.0)
            rate_item = QTableWidgetItem(f"{profit_rate:+.2f}%")
            rate_item.setForeground(profit_color)
            self.positions_table.setItem(row, 6, rate_item)
        
        # 열 너비 자동 조정
        self.positions_table.resizeColumnsToContents()
    
    def closeEvent(self, event):
        """종료 시 타이머 정리"""
        self.refresh_timer.stop()
        event.accept()

