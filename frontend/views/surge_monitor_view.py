"""
급등주 모니터 화면

[파일 역할]
실시간 급등주 목록 표시 및 상세 정보
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor


class SurgeMonitorView(QWidget):
    """급등주 모니터 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
        
        # 자동 새로고침 타이머 (10초마다)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(10000)
        
        self.refresh_data()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 상단: 제목 및 설정
        header_layout = QHBoxLayout()
        
        title = QLabel("🚀 급등주 모니터")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 설정 버튼
        self.settings_btn = QPushButton("⚙️ 설정")
        self.settings_btn.clicked.connect(self.toggle_settings)
        header_layout.addWidget(self.settings_btn)
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 설정 패널 (접을 수 있음)
        self.settings_panel = QGroupBox("급등주 감지 설정")
        self.settings_panel.setVisible(False)
        settings_layout = QFormLayout(self.settings_panel)
        
        # 최소 상승률
        self.min_change_rate_input = QDoubleSpinBox()
        self.min_change_rate_input.setMinimum(0.0)
        self.min_change_rate_input.setMaximum(50.0)
        self.min_change_rate_input.setValue(5.0)
        self.min_change_rate_input.setSuffix("%")
        settings_layout.addRow("최소 상승률:", self.min_change_rate_input)
        
        # 최소 거래량 비율
        self.min_volume_ratio_input = QDoubleSpinBox()
        self.min_volume_ratio_input.setMinimum(1.0)
        self.min_volume_ratio_input.setMaximum(10.0)
        self.min_volume_ratio_input.setValue(2.0)
        self.min_volume_ratio_input.setSuffix("배")
        settings_layout.addRow("최소 거래량 비율:", self.min_volume_ratio_input)
        
        # 표시 개수
        self.display_count_input = QSpinBox()
        self.display_count_input.setMinimum(10)
        self.display_count_input.setMaximum(100)
        self.display_count_input.setValue(20)
        settings_layout.addRow("표시 개수:", self.display_count_input)
        
        layout.addWidget(self.settings_panel)
        
        # 중단: 급등주 테이블
        self.surge_table = QTableWidget()
        self.surge_table.setColumnCount(6)
        self.surge_table.setHorizontalHeaderLabels([
            "종목코드", "종목명", "현재가", "상승률", "거래량 비율", "감지시간"
        ])
        self.surge_table.horizontalHeader().setStretchLastSection(True)
        self.surge_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.surge_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.surge_table.setAlternatingRowColors(True)
        
        # 헤더 스타일
        self.surge_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #FF9800;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # 테이블 스타일
        self.surge_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #FFF3E0;
            }
        """)
        
        layout.addWidget(self.surge_table)
        
        # 하단: 통계 정보
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("총 감지: 0개")
        self.total_label.setStyleSheet("font-size: 14px; color: #666;")
        stats_layout.addWidget(self.total_label)
        
        stats_layout.addStretch()
        
        self.last_update_label = QLabel("마지막 업데이트: -")
        self.last_update_label.setStyleSheet("font-size: 12px; color: #999;")
        stats_layout.addWidget(self.last_update_label)
        
        layout.addLayout(stats_layout)
    
    def toggle_settings(self):
        """설정 패널 토글"""
        self.settings_panel.setVisible(not self.settings_panel.isVisible())
    
    def refresh_data(self):
        """데이터 새로고침"""
        try:
            # 급등주 목록 조회
            limit = self.display_count_input.value()
            surge_data = self.api_client.get_surge_stocks(limit=limit)
            
            surge_stocks = surge_data.get('surge_stocks', [])
            self.update_surge_table(surge_stocks)
            
            # 통계 업데이트
            self.total_label.setText(f"총 감지: {len(surge_stocks)}개")
            
            # 마지막 업데이트 시간
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.setText(f"마지막 업데이트: {current_time}")
        
        except Exception as e:
            print(f"급등주 데이터 새로고침 오류: {e}")
    
    def update_surge_table(self, surge_stocks: list):
        """급등주 테이블 업데이트"""
        self.surge_table.setRowCount(len(surge_stocks))
        
        for row, stock in enumerate(surge_stocks):
            # 종목코드
            self.surge_table.setItem(row, 0, QTableWidgetItem(stock.get('stock_code', '')))
            
            # 종목명
            name_item = QTableWidgetItem(stock.get('stock_name', ''))
            name_item.setFont(self.surge_table.font())
            self.surge_table.setItem(row, 1, name_item)
            
            # 현재가
            price = stock.get('price', 0)
            price_item = QTableWidgetItem(f"{price:,}원")
            self.surge_table.setItem(row, 2, price_item)
            
            # 상승률
            change_rate = stock.get('change_rate', 0.0)
            rate_item = QTableWidgetItem(f"+{change_rate:.2f}%")
            rate_item.setForeground(QColor("#F44336"))
            rate_item.setFont(self.surge_table.font())
            self.surge_table.setItem(row, 3, rate_item)
            
            # 거래량 비율
            volume_ratio = stock.get('volume_ratio', 0.0)
            volume_item = QTableWidgetItem(f"{volume_ratio:.2f}배")
            volume_item.setForeground(QColor("#FF9800"))
            self.surge_table.setItem(row, 4, volume_item)
            
            # 감지시간
            detect_time = stock.get('detected_at', '')
            self.surge_table.setItem(row, 5, QTableWidgetItem(detect_time))
        
        # 열 너비 자동 조정
        self.surge_table.resizeColumnsToContents()
    
    def closeEvent(self, event):
        """종료 시 타이머 정리"""
        self.refresh_timer.stop()
        event.accept()

