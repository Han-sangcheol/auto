"""
차트 위젯 모듈

[파일 역할]
실시간 가격 및 수익률 차트를 표시하는 PyQt5 위젯입니다.

[주요 기능]
- 실시간 가격 차트 (종목별)
- 수익률 차트 (시간별)
- 매매 시점 마커 표시
- 자동 업데이트

[사용 방법]
from chart_widget import ChartWidget
chart = ChartWidget()
chart.update_price_data(stock_code, price, timestamp)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer
from collections import deque, defaultdict
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

# pyqtgraph (선택적 로드)
try:
    import pyqtgraph as pg
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    print("⚠️  pyqtgraph 미설치. pip install pyqtgraph로 설치하세요.")


class ChartWidget(QWidget):
    """
    실시간 차트 위젯
    """
    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        
        # 데이터베이스 참조 (히스토리 로드용)
        self.database = database
        
        # 데이터 저장 (최대 1000개 포인트)
        self.max_points = 1000
        self.price_data: Dict[str, Dict] = defaultdict(lambda: {
            'timestamps': deque(maxlen=self.max_points),
            'prices': deque(maxlen=self.max_points),
            'buy_points': [],  # (timestamp, price)
            'sell_points': []  # (timestamp, price)
        })
        
        self.profit_data = {
            'timestamps': deque(maxlen=self.max_points),
            'profit_rates': deque(maxlen=self.max_points),
            'cumulative_profit': deque(maxlen=self.max_points)
        }
        
        # 현재 선택된 종목
        self.current_stock = None
        
        # 히스토리 로드 캐시 (중복 로드 방지)
        self.loaded_stocks = set()
        
        # UI 초기화
        self.init_ui()
        
        # 자동 업데이트 타이머 (1초마다)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_charts)
        self.update_timer.start(1000)
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 상단 컨트롤
        control_layout = QHBoxLayout()
        
        # 종목 선택
        self.stock_label = QLabel("종목:")
        self.stock_combo = QComboBox()
        self.stock_combo.addItem("전체 수익률")
        self.stock_combo.currentTextChanged.connect(self.on_stock_changed)
        
        # 새로고침 버튼
        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.clicked.connect(self.refresh_charts)
        
        # 초기화 버튼
        self.clear_button = QPushButton("초기화")
        self.clear_button.clicked.connect(self.clear_data)
        
        control_layout.addWidget(self.stock_label)
        control_layout.addWidget(self.stock_combo)
        control_layout.addStretch()
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.clear_button)
        
        layout.addLayout(control_layout)
        
        # 차트 영역
        if PYQTGRAPH_AVAILABLE:
            self.setup_pyqtgraph_charts(layout)
        else:
            self.setup_fallback_ui(layout)
        
        self.setLayout(layout)
    
    def setup_pyqtgraph_charts(self, layout):
        """pyqtgraph 차트 설정"""
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 1. 가격 차트
        self.price_plot_widget = pg.PlotWidget()
        self.price_plot_widget.setLabel('left', '가격 (원)')
        self.price_plot_widget.setLabel('bottom', '시간')
        self.price_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.price_plot_widget.addLegend()
        
        # 가격 라인
        self.price_line = self.price_plot_widget.plot(
            pen=pg.mkPen(color=(0, 0, 255), width=2),
            name='가격'
        )
        
        # 매수/매도 포인트
        self.buy_scatter = pg.ScatterPlotItem(
            size=10,
            brush=pg.mkBrush(255, 0, 0, 200),
            pen=pg.mkPen(None),
            symbol='t'  # 삼각형 (위)
        )
        self.sell_scatter = pg.ScatterPlotItem(
            size=10,
            brush=pg.mkBrush(0, 255, 0, 200),
            pen=pg.mkPen(None),
            symbol='t1'  # 삼각형 (아래)
        )
        
        self.price_plot_widget.addItem(self.buy_scatter)
        self.price_plot_widget.addItem(self.sell_scatter)
        
        self.tab_widget.addTab(self.price_plot_widget, "가격 차트")
        
        # 2. 수익률 차트
        self.profit_plot_widget = pg.PlotWidget()
        self.profit_plot_widget.setLabel('left', '수익률 (%)')
        self.profit_plot_widget.setLabel('bottom', '시간')
        self.profit_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.profit_plot_widget.addLegend()
        
        # 수익률 라인
        self.profit_line = self.profit_plot_widget.plot(
            pen=pg.mkPen(color=(255, 0, 0), width=2),
            name='개별 수익률'
        )
        
        # 누적 수익률 라인
        self.cumulative_profit_line = self.profit_plot_widget.plot(
            pen=pg.mkPen(color=(0, 128, 0), width=2),
            name='누적 수익률'
        )
        
        # 0% 기준선
        self.profit_plot_widget.addLine(y=0, pen=pg.mkPen('k', style=Qt.DashLine))
        
        self.tab_widget.addTab(self.profit_plot_widget, "수익률 차트")
        
        layout.addWidget(self.tab_widget)
    
    def setup_fallback_ui(self, layout):
        """pyqtgraph 미설치 시 대체 UI"""
        fallback_label = QLabel()
        fallback_label.setText(
            "<h2>📊 차트 기능 비활성화</h2>"
            "<p><b>실시간 차트를 사용하려면 pyqtgraph를 설치하세요:</b></p>"
            "<pre style='background: #333; color: #0f0; padding: 10px;'>"
            "pip install pyqtgraph"
            "</pre>"
            "<hr>"
            "<p><b>🌐 외부 차트 보기:</b></p>"
            "<p>• <a href='https://finance.naver.com'>네이버 금융</a> - 한국 주식 차트</p>"
            "<p>• <a href='https://finance.yahoo.com'>야후 파이낸스</a> - 글로벌 차트</p>"
            "<p>• <a href='https://www.tradingview.com'>TradingView</a> - 고급 차트</p>"
        )
        fallback_label.setAlignment(Qt.AlignCenter)
        fallback_label.setStyleSheet("background-color: #f8f9fa; padding: 30px; font-size: 14px;")
        fallback_label.setOpenExternalLinks(True)  # 링크 클릭 가능
        layout.addWidget(fallback_label)
    
    def on_stock_changed(self, stock_code: str):
        """종목 선택 변경"""
        if stock_code == "전체 수익률":
            self.current_stock = None
        else:
            # 종목 코드 추출 (괄호 안의 코드)
            if '(' in stock_code and ')' in stock_code:
                self.current_stock = stock_code.split('(')[-1].split(')')[0]
            else:
                self.current_stock = stock_code
            
            # 아직 로드하지 않은 종목이면 히스토리 로드
            if self.current_stock not in self.loaded_stocks:
                self.load_history(self.current_stock, days=7)
        
        self.refresh_charts()
    
    def add_stock(self, stock_code: str, stock_name: str):
        """
        관심 종목 추가
        
        Args:
            stock_code: 종목 코드
            stock_name: 종목 이름
        """
        display_text = f"{stock_name} ({stock_code})"
        
        # 이미 있는지 확인
        for i in range(self.stock_combo.count()):
            if self.stock_combo.itemText(i) == display_text:
                return
        
        self.stock_combo.addItem(display_text)
    
    def load_history(self, stock_code: str, days: int = 7):
        """
        과거 차트 데이터를 데이터베이스에서 로드
        
        Args:
            stock_code: 종목 코드
            days: 로드할 기간 (일)
        """
        if not PYQTGRAPH_AVAILABLE or not self.database or not self.database.enabled:
            return
        
        try:
            from datetime import timedelta
            
            # 이미 로드했으면 스킵
            if stock_code in self.loaded_stocks:
                return
            
            # 기간 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # DB에서 1분봉 데이터 조회
            candles = self.database.get_candles(stock_code, start_date, end_date)
            
            if candles:
                # 차트에 추가
                for candle in candles:
                    self.update_price_data(
                        stock_code,
                        candle['close'],
                        candle['timestamp']
                    )
                
                print(f"✅ {stock_code} 히스토리 로드: {len(candles)}개 1분봉 (최근 {days}일)")
                self.loaded_stocks.add(stock_code)
            else:
                print(f"ℹ️  {stock_code} 히스토리 없음 (DB에 저장된 데이터가 없습니다)")
                
        except Exception as e:
            print(f"❌ 히스토리 로드 오류 ({stock_code}): {e}")
    
    def update_price_data(self, stock_code: str, price: float, timestamp: Optional[datetime] = None):
        """
        가격 데이터 업데이트
        
        Args:
            stock_code: 종목 코드
            price: 현재가
            timestamp: 타임스탬프 (None이면 현재 시간)
        """
        if not PYQTGRAPH_AVAILABLE:
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        data = self.price_data[stock_code]
        data['timestamps'].append(timestamp)
        data['prices'].append(price)
    
    def add_trade_marker(
        self,
        stock_code: str,
        trade_type: str,
        price: float,
        timestamp: Optional[datetime] = None
    ):
        """
        매매 마커 추가
        
        Args:
            stock_code: 종목 코드
            trade_type: 'buy' 또는 'sell'
            price: 체결가
            timestamp: 타임스탬프
        """
        if not PYQTGRAPH_AVAILABLE:
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        data = self.price_data[stock_code]
        
        if trade_type.lower() == 'buy':
            data['buy_points'].append((timestamp, price))
        elif trade_type.lower() == 'sell':
            data['sell_points'].append((timestamp, price))
    
    def update_profit_data(
        self,
        profit_rate: float,
        cumulative_profit: float,
        timestamp: Optional[datetime] = None
    ):
        """
        수익률 데이터 업데이트
        
        Args:
            profit_rate: 개별 수익률 (%)
            cumulative_profit: 누적 수익률 (%)
            timestamp: 타임스탬프
        """
        if not PYQTGRAPH_AVAILABLE:
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        self.profit_data['timestamps'].append(timestamp)
        self.profit_data['profit_rates'].append(profit_rate)
        self.profit_data['cumulative_profit'].append(cumulative_profit)
    
    def refresh_charts(self):
        """차트 새로고침"""
        if not PYQTGRAPH_AVAILABLE:
            return
        
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:
            # 가격 차트
            self.refresh_price_chart()
        elif current_tab == 1:
            # 수익률 차트
            self.refresh_profit_chart()
    
    def refresh_price_chart(self):
        """가격 차트 새로고침"""
        if not PYQTGRAPH_AVAILABLE:
            return
        
        if self.current_stock is None:
            # 전체 수익률 탭 선택 시 가격 차트 비움
            self.price_line.setData([], [])
            self.buy_scatter.setData([], [])
            self.sell_scatter.setData([], [])
            return
        
        data = self.price_data.get(self.current_stock)
        if not data or len(data['timestamps']) == 0:
            self.price_line.setData([], [])
            self.buy_scatter.setData([], [])
            self.sell_scatter.setData([], [])
            return
        
        # 타임스탬프를 숫자로 변환 (초 단위)
        base_time = data['timestamps'][0]
        x_data = [(t - base_time).total_seconds() for t in data['timestamps']]
        y_data = list(data['prices'])
        
        # 가격 라인 업데이트
        self.price_line.setData(x_data, y_data)
        
        # 매수 포인트
        if data['buy_points']:
            buy_x = [(t - base_time).total_seconds() for t, p in data['buy_points']]
            buy_y = [p for t, p in data['buy_points']]
            self.buy_scatter.setData(buy_x, buy_y)
        else:
            self.buy_scatter.setData([], [])
        
        # 매도 포인트
        if data['sell_points']:
            sell_x = [(t - base_time).total_seconds() for t, p in data['sell_points']]
            sell_y = [p for t, p in data['sell_points']]
            self.sell_scatter.setData(sell_x, sell_y)
        else:
            self.sell_scatter.setData([], [])
        
        # X축 레이블 업데이트 (시간 포맷)
        axis = self.price_plot_widget.getAxis('bottom')
        axis.setLabel('시간 (초)')
    
    def refresh_profit_chart(self):
        """수익률 차트 새로고침"""
        if not PYQTGRAPH_AVAILABLE:
            return
        
        data = self.profit_data
        if len(data['timestamps']) == 0:
            self.profit_line.setData([], [])
            self.cumulative_profit_line.setData([], [])
            return
        
        # 타임스탬프를 숫자로 변환
        base_time = data['timestamps'][0]
        x_data = [(t - base_time).total_seconds() for t in data['timestamps']]
        
        # 수익률 라인 업데이트
        self.profit_line.setData(x_data, list(data['profit_rates']))
        self.cumulative_profit_line.setData(x_data, list(data['cumulative_profit']))
        
        # X축 레이블
        axis = self.profit_plot_widget.getAxis('bottom')
        axis.setLabel('시간 (초)')
    
    def clear_data(self):
        """데이터 초기화"""
        # 확인 대화상자는 생략 (향후 추가 가능)
        self.price_data.clear()
        self.profit_data = {
            'timestamps': deque(maxlen=self.max_points),
            'profit_rates': deque(maxlen=self.max_points),
            'cumulative_profit': deque(maxlen=self.max_points)
        }
        
        self.refresh_charts()
        print("차트 데이터가 초기화되었습니다.")
    
    def get_chart_data_summary(self) -> Dict:
        """
        차트 데이터 요약 반환
        
        Returns:
            요약 정보 딕셔너리
        """
        return {
            'stock_count': len(self.price_data),
            'profit_points': len(self.profit_data['timestamps']),
            'max_points': self.max_points
        }


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    import random
    
    app = QApplication(sys.argv)
    
    # 테스트 윈도우
    window = ChartWidget()
    window.setWindowTitle("차트 위젯 테스트")
    window.resize(800, 600)
    window.show()
    
    # 테스트 데이터 추가
    window.add_stock("005930", "삼성전자")
    window.add_stock("000660", "SK하이닉스")
    
    # 시뮬레이션 데이터
    base_price_samsung = 75000
    base_price_sk = 140000
    
    for i in range(100):
        # 랜덤 가격 변동
        samsung_price = base_price_samsung + random.randint(-1000, 1000)
        sk_price = base_price_sk + random.randint(-2000, 2000)
        
        window.update_price_data("005930", samsung_price)
        window.update_price_data("000660", sk_price)
        
        # 랜덤 매매 마커
        if i % 20 == 0:
            window.add_trade_marker("005930", "buy", samsung_price)
        if i % 30 == 0:
            window.add_trade_marker("000660", "sell", sk_price)
        
        # 수익률 데이터
        profit_rate = random.uniform(-5, 5)
        cumulative = profit_rate + random.uniform(-2, 2)
        window.update_profit_data(profit_rate, cumulative)
    
    # 초기 차트 표시
    window.stock_combo.setCurrentIndex(1)  # 삼성전자 선택
    
    sys.exit(app.exec_())

