"""
차트 화면

[파일 역할]
실시간 캔들스틱 차트 및 기술적 지표 표시
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg
from datetime import datetime, timedelta
import numpy as np


class CandlestickItem(pg.GraphicsObject):
    """캔들스틱 차트 아이템"""
    
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data
        self.generatePicture()
    
    def generatePicture(self):
        """차트 그리기"""
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        
        w = 0.4  # 캔들 너비
        
        for i, (t, open_, high, low, close) in enumerate(self.data):
            # 상승/하락 색상
            if close > open_:
                p.setPen(pg.mkPen('#F44336', width=1))
                p.setBrush(pg.mkBrush('#F44336'))
            else:
                p.setPen(pg.mkPen('#2196F3', width=1))
                p.setBrush(pg.mkBrush('#2196F3'))
            
            # 고가-저가 선
            p.drawLine(pg.QtCore.QPointF(i, low), pg.QtCore.QPointF(i, high))
            
            # 시가-종가 박스
            p.drawRect(pg.QtCore.QRectF(i - w, open_, w * 2, close - open_))
        
        p.end()
    
    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


class ChartView(QWidget):
    """차트 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.current_stock_code = None
        self.chart_data = []
        self.setup_ui()
        
        # 자동 업데이트 타이머
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(5000)  # 5초마다 업데이트
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 상단: 종목 검색 및 설정
        control_layout = QHBoxLayout()
        
        # 종목 입력
        control_layout.addWidget(QLabel("종목코드:"))
        self.stock_code_input = QLineEdit()
        self.stock_code_input.setPlaceholderText("예: 005930")
        self.stock_code_input.setMaximumWidth(150)
        control_layout.addWidget(self.stock_code_input)
        
        self.search_btn = QPushButton("🔍 조회")
        self.search_btn.clicked.connect(self.on_search_stock)
        control_layout.addWidget(self.search_btn)
        
        control_layout.addSpacing(20)
        
        # 시간대 선택
        control_layout.addWidget(QLabel("시간대:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1분", "5분", "30분", "1시간", "일봉", "주봉"])
        self.timeframe_combo.setCurrentText("일봉")
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        control_layout.addWidget(self.timeframe_combo)
        
        control_layout.addSpacing(20)
        
        # 기간 선택
        control_layout.addWidget(QLabel("기간:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["1일", "1주", "1개월", "3개월", "6개월", "1년"])
        self.period_combo.setCurrentText("1개월")
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        control_layout.addWidget(self.period_combo)
        
        control_layout.addStretch()
        
        # 종목명 표시
        self.stock_name_label = QLabel("")
        self.stock_name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        control_layout.addWidget(self.stock_name_label)
        
        layout.addLayout(control_layout)
        
        # 중단: 차트 영역
        chart_layout = QHBoxLayout()
        
        # 왼쪽: 차트
        chart_container = QVBoxLayout()
        
        # pyqtgraph 위젯
        self.chart_widget = pg.GraphicsLayoutWidget()
        self.chart_widget.setBackground('w')
        
        # 메인 차트 (가격)
        self.price_plot = self.chart_widget.addPlot(row=0, col=0)
        self.price_plot.setLabel('left', '가격', units='원')
        self.price_plot.setLabel('bottom', '시간')
        self.price_plot.showGrid(x=True, y=True, alpha=0.3)
        
        # 거래량 차트
        self.volume_plot = self.chart_widget.addPlot(row=1, col=0)
        self.volume_plot.setLabel('left', '거래량')
        self.volume_plot.showGrid(x=True, y=True, alpha=0.3)
        self.volume_plot.setMaximumHeight(150)
        
        chart_container.addWidget(self.chart_widget)
        chart_layout.addLayout(chart_container, 3)
        
        # 오른쪽: 지표 설정 및 정보
        right_panel = QVBoxLayout()
        
        # 기술적 지표 설정
        indicator_group = QGroupBox("기술적 지표")
        indicator_layout = QVBoxLayout(indicator_group)
        
        self.ma5_check = QCheckBox("MA5 (5일 이동평균)")
        self.ma5_check.setChecked(True)
        self.ma5_check.stateChanged.connect(self.update_chart)
        indicator_layout.addWidget(self.ma5_check)
        
        self.ma20_check = QCheckBox("MA20 (20일 이동평균)")
        self.ma20_check.setChecked(True)
        self.ma20_check.stateChanged.connect(self.update_chart)
        indicator_layout.addWidget(self.ma20_check)
        
        self.ma60_check = QCheckBox("MA60 (60일 이동평균)")
        self.ma60_check.setChecked(False)
        self.ma60_check.stateChanged.connect(self.update_chart)
        indicator_layout.addWidget(self.ma60_check)
        
        indicator_layout.addSpacing(10)
        
        self.bollinger_check = QCheckBox("볼린저 밴드")
        self.bollinger_check.setChecked(False)
        self.bollinger_check.stateChanged.connect(self.update_chart)
        indicator_layout.addWidget(self.bollinger_check)
        
        right_panel.addWidget(indicator_group)
        
        # 현재가 정보
        info_group = QGroupBox("현재가 정보")
        info_layout = QFormLayout(info_group)
        
        self.current_price_label = QLabel("-")
        info_layout.addRow("현재가:", self.current_price_label)
        
        self.change_label = QLabel("-")
        info_layout.addRow("등락:", self.change_label)
        
        self.volume_label = QLabel("-")
        info_layout.addRow("거래량:", self.volume_label)
        
        self.high_label = QLabel("-")
        info_layout.addRow("고가:", self.high_label)
        
        self.low_label = QLabel("-")
        info_layout.addRow("저가:", self.low_label)
        
        right_panel.addWidget(info_group)
        right_panel.addStretch()
        
        chart_layout.addLayout(right_panel, 1)
        
        layout.addLayout(chart_layout)
    
    def on_search_stock(self):
        """종목 조회"""
        stock_code = self.stock_code_input.text().strip()
        if not stock_code:
            return
        
        self.current_stock_code = stock_code
        self.load_chart_data()
    
    def on_timeframe_changed(self, timeframe: str):
        """시간대 변경"""
        if self.current_stock_code:
            self.load_chart_data()
    
    def on_period_changed(self, period: str):
        """기간 변경"""
        if self.current_stock_code:
            self.load_chart_data()
    
    def load_chart_data(self):
        """차트 데이터 로드"""
        if not self.current_stock_code:
            return
        
        try:
            # 기간 계산
            period_map = {
                "1일": 1,
                "1주": 7,
                "1개월": 30,
                "3개월": 90,
                "6개월": 180,
                "1년": 365
            }
            days = period_map.get(self.period_combo.currentText(), 30)
            
            # API 호출
            data = self.api_client.get_chart_data(self.current_stock_code, days=days)
            
            # 종목명 표시
            stock_info = self.api_client.get_stock_info(self.current_stock_code)
            self.stock_name_label.setText(f"{stock_info.get('name', '')} ({self.current_stock_code})")
            
            # 차트 데이터 저장
            self.chart_data = data.get('candles', [])
            
            # 차트 업데이트
            self.update_chart()
            
            # 현재가 정보 업데이트
            self.update_price_info(stock_info)
        
        except Exception as e:
            print(f"차트 데이터 로드 오류: {e}")
            # 샘플 데이터 생성 (테스트용)
            self.generate_sample_data()
    
    def generate_sample_data(self):
        """샘플 데이터 생성 (API 연동 전 테스트용)"""
        base_price = 50000
        self.chart_data = []
        
        for i in range(30):
            date = datetime.now() - timedelta(days=30-i)
            open_ = base_price + np.random.randint(-1000, 1000)
            close = open_ + np.random.randint(-1000, 1000)
            high = max(open_, close) + np.random.randint(0, 500)
            low = min(open_, close) - np.random.randint(0, 500)
            volume = np.random.randint(100000, 1000000)
            
            self.chart_data.append({
                'timestamp': date.isoformat(),
                'open': open_,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        self.stock_name_label.setText(f"샘플 종목 ({self.current_stock_code})")
        self.update_chart()
    
    def update_chart(self):
        """차트 업데이트"""
        if not self.chart_data:
            return
        
        # 차트 초기화
        self.price_plot.clear()
        self.volume_plot.clear()
        
        # 데이터 준비
        candle_data = []
        volumes = []
        closes = []
        
        for i, candle in enumerate(self.chart_data):
            candle_data.append((
                i,
                candle['open'],
                candle['high'],
                candle['low'],
                candle['close']
            ))
            volumes.append(candle['volume'])
            closes.append(candle['close'])
        
        # 캔들스틱 그리기
        candlestick = CandlestickItem(candle_data)
        self.price_plot.addItem(candlestick)
        
        # 이동평균선
        if self.ma5_check.isChecked() and len(closes) >= 5:
            ma5 = self.calculate_ma(closes, 5)
            self.price_plot.plot(ma5, pen=pg.mkPen('#FF9800', width=2), name='MA5')
        
        if self.ma20_check.isChecked() and len(closes) >= 20:
            ma20 = self.calculate_ma(closes, 20)
            self.price_plot.plot(ma20, pen=pg.mkPen('#2196F3', width=2), name='MA20')
        
        if self.ma60_check.isChecked() and len(closes) >= 60:
            ma60 = self.calculate_ma(closes, 60)
            self.price_plot.plot(ma60, pen=pg.mkPen('#9C27B0', width=2), name='MA60')
        
        # 볼린저 밴드
        if self.bollinger_check.isChecked() and len(closes) >= 20:
            upper, middle, lower = self.calculate_bollinger(closes, 20)
            self.price_plot.plot(upper, pen=pg.mkPen('#FF5722', width=1, style=pg.QtCore.Qt.DashLine))
            self.price_plot.plot(middle, pen=pg.mkPen('#4CAF50', width=1))
            self.price_plot.plot(lower, pen=pg.mkPen('#FF5722', width=1, style=pg.QtCore.Qt.DashLine))
        
        # 거래량
        x = list(range(len(volumes)))
        colors = ['r' if self.chart_data[i]['close'] >= self.chart_data[i]['open'] else 'b' 
                  for i in range(len(volumes))]
        
        bg = pg.BarGraphItem(x=x, height=volumes, width=0.8, brushes=colors)
        self.volume_plot.addItem(bg)
    
    def calculate_ma(self, data, period):
        """이동평균 계산"""
        ma = []
        for i in range(len(data)):
            if i < period - 1:
                ma.append(np.nan)
            else:
                ma.append(np.mean(data[i-period+1:i+1]))
        return ma
    
    def calculate_bollinger(self, data, period):
        """볼린저 밴드 계산"""
        ma = self.calculate_ma(data, period)
        upper = []
        lower = []
        
        for i in range(len(data)):
            if i < period - 1:
                upper.append(np.nan)
                lower.append(np.nan)
            else:
                std = np.std(data[i-period+1:i+1])
                upper.append(ma[i] + 2 * std)
                lower.append(ma[i] - 2 * std)
        
        return upper, ma, lower
    
    def update_price_info(self, stock_info: dict):
        """현재가 정보 업데이트"""
        price = stock_info.get('price', 0)
        change = stock_info.get('change', 0)
        change_pct = stock_info.get('change_percent', 0.0)
        volume = stock_info.get('volume', 0)
        high = stock_info.get('high', 0)
        low = stock_info.get('low', 0)
        
        self.current_price_label.setText(f"{price:,}원")
        
        change_text = f"{change:+,}원 ({change_pct:+.2f}%)"
        change_color = "#F44336" if change < 0 else "#4CAF50" if change > 0 else "#666"
        self.change_label.setText(change_text)
        self.change_label.setStyleSheet(f"color: {change_color}; font-weight: bold;")
        
        self.volume_label.setText(f"{volume:,}")
        self.high_label.setText(f"{high:,}원")
        self.low_label.setText(f"{low:,}원")
    
    def closeEvent(self, event):
        """종료 시 타이머 정리"""
        self.update_timer.stop()
        event.accept()

