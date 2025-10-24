"""
로그 뷰어 화면

[파일 역할]
시스템 로그 및 트레이딩 로그 표시
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from datetime import datetime


class LogsView(QWidget):
    """로그 뷰어 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.logs = []
        self.filtered_logs = []
        self.setup_ui()
        
        # 자동 새로고침 타이머 (5초마다)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)
        self.refresh_timer.start(5000)
        
        # 초기 로드
        self.refresh_logs()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 상단: 제목 및 컨트롤
        header_layout = QHBoxLayout()
        
        title = QLabel("📝 시스템 로그")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 로그 레벨 필터
        header_layout.addWidget(QLabel("레벨:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["전체", "DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.currentTextChanged.connect(self.apply_filters)
        header_layout.addWidget(self.level_combo)
        
        # 검색
        header_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("메시지 검색...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.apply_filters)
        header_layout.addWidget(self.search_input)
        
        # 자동 스크롤
        self.auto_scroll_check = QCheckBox("자동 스크롤")
        self.auto_scroll_check.setChecked(True)
        header_layout.addWidget(self.auto_scroll_check)
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        header_layout.addWidget(self.refresh_btn)
        
        # 지우기 버튼
        self.clear_btn = QPushButton("🗑️ 지우기")
        self.clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.clear_btn)
        
        # 내보내기 버튼
        self.export_btn = QPushButton("💾 내보내기")
        self.export_btn.clicked.connect(self.export_logs)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # 중단: 로그 테이블
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(4)
        self.logs_table.setHorizontalHeaderLabels(["시간", "레벨", "모듈", "메시지"])
        
        # 열 너비 설정
        self.logs_table.setColumnWidth(0, 150)  # 시간
        self.logs_table.setColumnWidth(1, 80)   # 레벨
        self.logs_table.setColumnWidth(2, 120)  # 모듈
        
        header = self.logs_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.logs_table.setAlternatingRowColors(True)
        
        # 헤더 스타일
        self.logs_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #607D8B;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.logs_table)
        
        # 하단: 통계
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("총 로그: 0개")
        self.total_label.setStyleSheet("font-size: 12px; color: #666;")
        stats_layout.addWidget(self.total_label)
        
        stats_layout.addSpacing(20)
        
        self.error_label = QLabel("ERROR: 0개")
        self.error_label.setStyleSheet("font-size: 12px; color: #F44336; font-weight: bold;")
        stats_layout.addWidget(self.error_label)
        
        self.warning_label = QLabel("WARNING: 0개")
        self.warning_label.setStyleSheet("font-size: 12px; color: #FF9800;")
        stats_layout.addWidget(self.warning_label)
        
        stats_layout.addStretch()
        
        self.last_update_label = QLabel("마지막 업데이트: -")
        self.last_update_label.setStyleSheet("font-size: 12px; color: #999;")
        stats_layout.addWidget(self.last_update_label)
        
        layout.addLayout(stats_layout)
    
    def refresh_logs(self):
        """로그 새로고침"""
        try:
            # API를 통해 로그 조회
            self.logs = self.api_client.get_logs(limit=1000)
            
            # 필터 적용
            self.apply_filters()
            
            # 통계 업데이트
            self.update_statistics()
            
            # 마지막 업데이트 시간
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.setText(f"마지막 업데이트: {current_time}")
        
        except Exception as e:
            print(f"로그 새로고침 오류: {e}")
            # 샘플 로그 생성 (테스트용)
            self.generate_sample_logs()
    
    def generate_sample_logs(self):
        """샘플 로그 생성 (테스트용)"""
        sample_logs = [
            {
                'timestamp': (datetime.now()).isoformat(),
                'level': 'INFO',
                'module': 'trading_engine',
                'message': '자동매매 시스템이 시작되었습니다.'
            },
            {
                'timestamp': (datetime.now()).isoformat(),
                'level': 'INFO',
                'module': 'kiwoom_api',
                'message': '키움 API 로그인 성공'
            },
            {
                'timestamp': (datetime.now()).isoformat(),
                'level': 'DEBUG',
                'module': 'indicators',
                'message': 'RSI 계산 완료: 45.3'
            },
            {
                'timestamp': (datetime.now()).isoformat(),
                'level': 'WARNING',
                'module': 'risk_manager',
                'message': '포지션 한도 근접: 2/3 종목'
            },
            {
                'timestamp': (datetime.now()).isoformat(),
                'level': 'INFO',
                'module': 'strategies',
                'message': '매수 신호 감지: 005930'
            },
            {
                'timestamp': (datetime.now()).isoformat(),
                'level': 'ERROR',
                'module': 'kiwoom_api',
                'message': 'API 호출 실패: 조회 한도 초과'
            },
            {
                'timestamp': (datetime.now()).isoformat(),
                'level': 'INFO',
                'module': 'trading_engine',
                'message': '주문 체결: 005930 10주 @ 70,000원'
            },
        ]
        
        self.logs = sample_logs
        self.apply_filters()
        self.update_statistics()
    
    def apply_filters(self):
        """필터 적용"""
        # 레벨 필터
        selected_level = self.level_combo.currentText()
        search_text = self.search_input.text().lower()
        
        self.filtered_logs = []
        for log in self.logs:
            # 레벨 필터링
            if selected_level != "전체" and log['level'] != selected_level:
                continue
            
            # 검색 필터링
            if search_text and search_text not in log['message'].lower():
                continue
            
            self.filtered_logs.append(log)
        
        # 테이블 업데이트
        self.update_table()
    
    def update_table(self):
        """테이블 업데이트"""
        self.logs_table.setRowCount(len(self.filtered_logs))
        
        for row, log in enumerate(self.filtered_logs):
            # 시간
            timestamp = log['timestamp']
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[1].split('.')[0]
            time_item = QTableWidgetItem(timestamp)
            self.logs_table.setItem(row, 0, time_item)
            
            # 레벨
            level = log['level']
            level_item = QTableWidgetItem(level)
            
            # 레벨별 색상
            if level == 'ERROR':
                level_item.setForeground(QColor("#F44336"))
                level_item.setBackground(QColor("#FFEBEE"))
            elif level == 'WARNING':
                level_item.setForeground(QColor("#FF9800"))
                level_item.setBackground(QColor("#FFF3E0"))
            elif level == 'INFO':
                level_item.setForeground(QColor("#2196F3"))
            elif level == 'DEBUG':
                level_item.setForeground(QColor("#9E9E9E"))
            
            self.logs_table.setItem(row, 1, level_item)
            
            # 모듈
            module_item = QTableWidgetItem(log['module'])
            self.logs_table.setItem(row, 2, module_item)
            
            # 메시지
            message_item = QTableWidgetItem(log['message'])
            self.logs_table.setItem(row, 3, message_item)
        
        # 자동 스크롤
        if self.auto_scroll_check.isChecked() and self.filtered_logs:
            self.logs_table.scrollToBottom()
    
    def update_statistics(self):
        """통계 업데이트"""
        total = len(self.logs)
        error_count = sum(1 for log in self.logs if log['level'] == 'ERROR')
        warning_count = sum(1 for log in self.logs if log['level'] == 'WARNING')
        
        self.total_label.setText(f"총 로그: {total}개")
        self.error_label.setText(f"ERROR: {error_count}개")
        self.warning_label.setText(f"WARNING: {warning_count}개")
    
    def clear_logs(self):
        """로그 지우기"""
        reply = QMessageBox.question(
            self,
            "로그 지우기",
            "모든 로그를 지우시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logs = []
            self.filtered_logs = []
            self.update_table()
            self.update_statistics()
    
    def export_logs(self):
        """로그 내보내기"""
        try:
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                for log in self.logs:
                    f.write(f"[{log['timestamp']}] [{log['level']}] [{log['module']}] {log['message']}\n")
            
            QMessageBox.information(self, "내보내기 완료", f"로그가 {filename}에 저장되었습니다.")
        
        except Exception as e:
            QMessageBox.critical(self, "내보내기 실패", f"로그 내보내기 중 오류: {str(e)}")
    
    def closeEvent(self, event):
        """종료 시 타이머 정리"""
        self.refresh_timer.stop()
        event.accept()

