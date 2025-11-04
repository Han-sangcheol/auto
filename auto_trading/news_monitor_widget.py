"""
뉴스 검색 모니터링 위젯

뉴스 크롤링 상황을 실시간으로 모니터링하는 GUI 컴포넌트
"""

from datetime import datetime
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class NewsMonitorWidget(QGroupBox):
    """뉴스 검색 모니터링 위젯"""
    
    def __init__(self, parent=None):
        super().__init__("📰 뉴스 검색 모니터링", parent)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        
        # 상태 표시 레이블
        status_layout = QHBoxLayout()
        self.status_label = QLabel("⏸️ 대기 중...")
        self.status_label.setStyleSheet("font-weight: bold; color: #666;")
        status_layout.addWidget(self.status_label)
        
        # 소스별 통계
        self.naver_status = QLabel("네이버: 0/0 (0%)")
        self.naver_status.setStyleSheet("color: green;")
        self.daum_status = QLabel("다음: 0/0 (0%)")
        self.daum_status.setStyleSheet("color: blue;")
        
        status_layout.addStretch()
        status_layout.addWidget(self.naver_status)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.daum_status)
        
        layout.addLayout(status_layout)
        
        # 뉴스 로그 테이블
        self.news_table = QTableWidget()
        self.news_table.setColumnCount(5)
        self.news_table.setHorizontalHeaderLabels([
            "시간", "소스", "종목", "내용", "상태"
        ])
        
        # 컬럼 너비 설정
        header = self.news_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 시간
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 소스
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 종목
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # 내용
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 상태
        
        # 행 높이 자동 조정
        self.news_table.verticalHeader().setDefaultSectionSize(30)
        self.news_table.setAlternatingRowColors(True)
        
        # 최대 로그 개수 제한 (성능)
        self.max_log_rows = 100
        
        layout.addWidget(self.news_table)
        
        self.setLayout(layout)
    
    def add_news_log(
        self, 
        message: str, 
        level: str = "info", 
        stock_code: str = "", 
        source: str = ""
    ):
        """
        뉴스 로그 추가
        
        Args:
            message: 로그 메시지
            level: 로그 레벨 (info, success, warning, error)
            stock_code: 종목 코드
            source: 뉴스 소스 (naver, daum)
        """
        # 최대 로그 개수 초과 시 오래된 로그 삭제
        if self.news_table.rowCount() >= self.max_log_rows:
            self.news_table.removeRow(self.news_table.rowCount() - 1)
        
        # 새 행 추가 (최신 로그가 위에 오도록)
        self.news_table.insertRow(0)
        
        # 시간
        timestamp = datetime.now().strftime("%H:%M:%S")
        time_item = QTableWidgetItem(timestamp)
        time_item.setTextAlignment(Qt.AlignCenter)
        self.news_table.setItem(0, 0, time_item)
        
        # 소스
        source_name = self._get_source_display_name(source)
        source_item = QTableWidgetItem(source_name)
        source_item.setTextAlignment(Qt.AlignCenter)
        
        if source == "naver":
            source_item.setForeground(QColor("green"))
        elif source == "daum":
            source_item.setForeground(QColor("blue"))
        
        self.news_table.setItem(0, 1, source_item)
        
        # 종목
        stock_item = QTableWidgetItem(stock_code if stock_code else "-")
        stock_item.setTextAlignment(Qt.AlignCenter)
        self.news_table.setItem(0, 2, stock_item)
        
        # 내용
        content_item = QTableWidgetItem(message)
        self.news_table.setItem(0, 3, content_item)
        
        # 상태
        status_text = self._get_status_text(level)
        status_item = QTableWidgetItem(status_text)
        status_item.setTextAlignment(Qt.AlignCenter)
        
        # 상태별 색상
        if level == "success":
            status_item.setForeground(QColor("#00AA00"))
            status_item.setBackground(QColor("#E8F5E9"))
        elif level == "warning":
            status_item.setForeground(QColor("#FF8800"))
            status_item.setBackground(QColor("#FFF3E0"))
        elif level == "error":
            status_item.setForeground(QColor("#CC0000"))
            status_item.setBackground(QColor("#FFEBEE"))
        else:  # info
            status_item.setForeground(QColor("#0066CC"))
        
        self.news_table.setItem(0, 4, status_item)
        
        # 최신 로그로 스크롤
        self.news_table.scrollToTop()
        
        # 상태 레이블 업데이트
        self.status_label.setText("▶️ 실행 중...")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
    
    def update_source_stats(self, source: str, success: int, total: int):
        """
        소스별 통계 업데이트
        
        Args:
            source: 소스 이름 (naver, daum)
            success: 성공 횟수
            total: 전체 시도 횟수
        """
        success_rate = (success / total * 100) if total > 0 else 0
        
        if source == "naver":
            self.naver_status.setText(f"네이버: {success}/{total} ({success_rate:.0f}%)")
            
            # 성공률에 따라 색상 변경
            if success_rate >= 80:
                self.naver_status.setStyleSheet("color: green; font-weight: bold;")
            elif success_rate >= 50:
                self.naver_status.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.naver_status.setStyleSheet("color: red; font-weight: bold;")
        
        elif source == "daum":
            self.daum_status.setText(f"다음: {success}/{total} ({success_rate:.0f}%)")
            
            if success_rate >= 80:
                self.daum_status.setStyleSheet("color: green; font-weight: bold;")
            elif success_rate >= 50:
                self.daum_status.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.daum_status.setStyleSheet("color: red; font-weight: bold;")
    
    def clear_logs(self):
        """로그 전체 삭제"""
        self.news_table.setRowCount(0)
        self.status_label.setText("⏸️ 대기 중...")
        self.status_label.setStyleSheet("font-weight: bold; color: #666;")
    
    def _get_source_display_name(self, source: str) -> str:
        """소스 표시 이름 반환"""
        source_map = {
            "naver": "네이버",
            "daum": "다음",
        }
        return source_map.get(source, source)
    
    def _get_status_text(self, level: str) -> str:
        """레벨별 상태 텍스트 반환"""
        status_map = {
            "info": "ℹ️ 정보",
            "success": "✅ 성공",
            "warning": "⚠️ 경고",
            "error": "❌ 오류",
        }
        return status_map.get(level, "ℹ️ 정보")


