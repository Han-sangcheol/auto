"""
고급 차트 위젯 모듈

[파일 역할]
plotly 기반 인터랙티브 금융 차트를 표시하는 PyQt5 위젯입니다.

[주요 기능]
- yfinance를 통한 외부 데이터 조회
- 캔들스틱 차트
- 이동평균선 (5일, 20일, 60일)
- 평균 매수가 라인 표시
- 거래량 차트
- 기술적 지표 (RSI, MACD, 볼린저밴드)
- 인터랙티브 줌/팬 기능

[사용 방법]
from advanced_chart_widget import AdvancedChartWidget
chart = AdvancedChartWidget(trading_engine)
chart.load_and_display_stock(stock_code)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QCheckBox, QGroupBox,
    QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QTimer
from typing import Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance 미설치. pip install yfinance로 설치하세요.")

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    print("⚠️  pandas_ta 미설치. pip install pandas_ta로 설치하세요.")


class AdvancedChartWidget(QWidget):
    """
    plotly 기반 고급 차트 위젯
    """
    def __init__(self, trading_engine, parent=None):
        super().__init__(parent)
        
        self.trading_engine = trading_engine
        
        # 종목 목록 (code -> name 매핑)
        self.stocks: Dict[str, str] = {}
        
        # 현재 선택된 종목
        self.current_stock_code: Optional[str] = None
        
        # 데이터 캐시
        self.data_cache: Dict[str, pd.DataFrame] = {}
        
        # UI 초기화
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 상단 컨트롤 패널
        control_layout = QHBoxLayout()
        
        # 종목 선택
        control_layout.addWidget(QLabel("종목:"))
        self.stock_combo = QComboBox()
        self.stock_combo.setMinimumWidth(150)
        self.stock_combo.currentTextChanged.connect(self.on_stock_changed)
        control_layout.addWidget(self.stock_combo)
        
        # 기간 선택
        control_layout.addWidget(QLabel("기간:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "1주일 (1wk)",
            "1개월 (1mo)",
            "3개월 (3mo)",
            "6개월 (6mo)",
            "1년 (1y)"
        ])
        self.period_combo.setCurrentText("3개월 (3mo)")
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        control_layout.addWidget(self.period_combo)
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.clicked.connect(self.refresh_chart)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 지표 설정 패널
        indicators_group = QGroupBox("차트 지표")
        indicators_layout = QHBoxLayout()
        
        self.ma_checkbox = QCheckBox("이동평균선")
        self.ma_checkbox.setChecked(True)
        self.ma_checkbox.stateChanged.connect(self.refresh_chart)
        indicators_layout.addWidget(self.ma_checkbox)
        
        self.bb_checkbox = QCheckBox("볼린저밴드")
        self.bb_checkbox.setChecked(False)
        self.bb_checkbox.stateChanged.connect(self.refresh_chart)
        indicators_layout.addWidget(self.bb_checkbox)
        
        self.volume_checkbox = QCheckBox("거래량")
        self.volume_checkbox.setChecked(True)
        self.volume_checkbox.stateChanged.connect(self.refresh_chart)
        indicators_layout.addWidget(self.volume_checkbox)
        
        self.rsi_checkbox = QCheckBox("RSI")
        self.rsi_checkbox.setChecked(False)
        self.rsi_checkbox.stateChanged.connect(self.refresh_chart)
        indicators_layout.addWidget(self.rsi_checkbox)
        
        self.macd_checkbox = QCheckBox("MACD")
        self.macd_checkbox.setChecked(False)
        self.macd_checkbox.stateChanged.connect(self.refresh_chart)
        indicators_layout.addWidget(self.macd_checkbox)
        
        self.avg_buy_checkbox = QCheckBox("평균 매수가")
        self.avg_buy_checkbox.setChecked(True)
        self.avg_buy_checkbox.stateChanged.connect(self.refresh_chart)
        indicators_layout.addWidget(self.avg_buy_checkbox)
        
        indicators_layout.addStretch()
        
        indicators_group.setLayout(indicators_layout)
        layout.addWidget(indicators_group)
        
        # 차트 표시 영역 (QWebEngineView)
        if YFINANCE_AVAILABLE:
            self.web_view = QWebEngineView()
            layout.addWidget(self.web_view)
        else:
            fallback_label = QLabel(
                "<h2>📊 고급 차트 기능 비활성화</h2>"
                "<p><b>고급 차트를 사용하려면 다음 패키지를 설치하세요:</b></p>"
                "<pre style='background: #333; color: #0f0; padding: 10px;'>"
                "pip install yfinance plotly PyQtWebEngine pandas-ta"
                "</pre>"
            )
            fallback_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(fallback_label)
        
        self.setLayout(layout)
        
    def add_stock(self, stock_code: str, stock_name: str):
        """
        차트에 종목 추가
        
        Args:
            stock_code: 종목 코드 (예: "005930")
            stock_name: 종목명 (예: "삼성전자")
        """
        if stock_code not in self.stocks:
            self.stocks[stock_code] = stock_name
            self.stock_combo.addItem(f"{stock_name} ({stock_code})")
            print(f"✅ 차트 종목 추가: {stock_name} ({stock_code})")
    
    def on_stock_changed(self, text: str):
        """종목 변경 이벤트"""
        if not text or text == "":
            return
        
        # 텍스트에서 종목 코드 추출 "종목명 (코드)" 형식
        if "(" in text and ")" in text:
            stock_code = text.split("(")[-1].split(")")[0]
            self.current_stock_code = stock_code
            self.load_and_display_stock(stock_code)
    
    def on_period_changed(self, text: str):
        """기간 변경 이벤트"""
        if self.current_stock_code:
            self.load_and_display_stock(self.current_stock_code)
    
    def get_period_value(self) -> str:
        """선택된 기간 값 반환"""
        text = self.period_combo.currentText()
        # "1개월 (1mo)" -> "1mo"
        if "(" in text and ")" in text:
            return text.split("(")[-1].split(")")[0]
        return "3mo"  # 기본값
    
    def convert_to_yahoo_symbol(self, stock_code: str) -> str:
        """
        키움 종목코드 -> 야후 파이낸스 심볼 변환
        
        Args:
            stock_code: 키움 종목 코드 (예: "005930")
        
        Returns:
            야후 파이낸스 심볼 (예: "005930.KS")
        
        Note:
            한국 거래소 구분:
            - .KS: 코스피 (대부분의 대형주)
            - .KQ: 코스닥 (중소형주, 기술주)
            
            정확한 거래소 구분은 키움 API의 GetMasterStockState()를 사용해야 하지만,
            간단하게 종목 코드 범위로 추정:
            - 코스닥: 일반적으로 039XXX, 0XXXXX 범위
            - 기본적으로 .KS로 시도하고, 실패하면 .KQ로 재시도
        """
        # 코스닥 범위 추정 (정확하지 않을 수 있음)
        kosdaq_ranges = [
            (39000, 39999),  # 039XXX
            (50000, 69999),  # 05XXXX ~ 06XXXX
        ]
        
        try:
            code_num = int(stock_code)
            for start, end in kosdaq_ranges:
                if start <= code_num <= end:
                    return f"{stock_code}.KQ"
        except:
            pass
        
        return f"{stock_code}.KS"  # 기본: 코스피
    
    def load_stock_data(self, stock_code: str, period: str = "3mo") -> Optional[pd.DataFrame]:
        """
        yfinance로 주식 데이터 조회
        
        Args:
            stock_code: 종목 코드
            period: 조회 기간 (1wk, 1mo, 3mo, 6mo, 1y 등)
        
        Returns:
            DataFrame (OHLCV 데이터) 또는 None (실패 시)
        """
        if not YFINANCE_AVAILABLE:
            return None
        
        try:
            # 야후 파이낸스 심볼 변환
            yahoo_symbol = self.convert_to_yahoo_symbol(stock_code)
            print(f"📊 데이터 조회 시작: {yahoo_symbol} (기간: {period})")
            
            # yfinance로 데이터 다운로드
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(period=period)
            
            if df.empty:
                # .KS로 실패하면 .KQ로 재시도
                if yahoo_symbol.endswith(".KS"):
                    yahoo_symbol = stock_code + ".KQ"
                    print(f"   재시도: {yahoo_symbol}")
                    ticker = yf.Ticker(yahoo_symbol)
                    df = ticker.history(period=period)
                
                if df.empty:
                    print(f"⚠️  데이터 조회 실패: {stock_code}")
                    return None
            
            print(f"✅ 데이터 조회 완료: {len(df)}개 데이터")
            
            # 캐시에 저장
            self.data_cache[stock_code] = df
            
            return df
            
        except Exception as e:
            print(f"❌ 데이터 조회 오류 ({stock_code}): {e}")
            return None
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표 계산
        
        Args:
            df: OHLCV 데이터프레임
        
        Returns:
            지표가 추가된 데이터프레임
        """
        if not PANDAS_TA_AVAILABLE:
            return df
        
        try:
            # 이동평균선
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['MA60'] = ta.sma(df['Close'], length=60)
            
            # 볼린저 밴드
            bbands = ta.bbands(df['Close'], length=20, std=2)
            if bbands is not None and not bbands.empty:
                df['BB_upper'] = bbands.iloc[:, 0]  # BBU_20_2.0
                df['BB_middle'] = bbands.iloc[:, 1]  # BBM_20_2.0
                df['BB_lower'] = bbands.iloc[:, 2]  # BBL_20_2.0
            
            # RSI
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # MACD
            macd = ta.macd(df['Close'])
            if macd is not None and not macd.empty:
                df['MACD'] = macd.iloc[:, 0]  # MACD_12_26_9
                df['MACD_signal'] = macd.iloc[:, 1]  # MACDs_12_26_9
                df['MACD_hist'] = macd.iloc[:, 2]  # MACDh_12_26_9
            
            print(f"✅ 기술적 지표 계산 완료")
            
        except Exception as e:
            print(f"⚠️  기술적 지표 계산 오류: {e}")
        
        return df
    
    def create_chart(self, df: pd.DataFrame, stock_code: str) -> str:
        """
        plotly 차트 생성
        
        Args:
            df: OHLCV + 지표 데이터
            stock_code: 종목 코드
        
        Returns:
            HTML 문자열
        """
        stock_name = self.stocks.get(stock_code, stock_code)
        
        # 서브플롯 개수 계산
        subplot_count = 1  # 기본: 캔들스틱
        subplot_titles = [f"{stock_name} ({stock_code})"]
        row_heights = []
        
        if self.volume_checkbox.isChecked():
            subplot_count += 1
            subplot_titles.append("거래량")
        
        if self.rsi_checkbox.isChecked():
            subplot_count += 1
            subplot_titles.append("RSI")
        
        if self.macd_checkbox.isChecked():
            subplot_count += 1
            subplot_titles.append("MACD")
        
        # 높이 비율 설정
        if subplot_count == 1:
            row_heights = [1.0]
        elif subplot_count == 2:
            row_heights = [0.7, 0.3]
        elif subplot_count == 3:
            row_heights = [0.6, 0.2, 0.2]
        elif subplot_count == 4:
            row_heights = [0.5, 0.2, 0.15, 0.15]
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=subplot_count,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=subplot_titles,
            row_heights=row_heights,
            specs=[[{"secondary_y": False}] for _ in range(subplot_count)]
        )
        
        # 1. 캔들스틱 차트
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='가격',
                increasing_line_color='red',
                decreasing_line_color='blue'
            ),
            row=1, col=1
        )
        
        # 이동평균선
        if self.ma_checkbox.isChecked():
            if 'MA5' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['MA5'],
                        name='MA5',
                        line=dict(color='orange', width=1)
                    ),
                    row=1, col=1
                )
            if 'MA20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['MA20'],
                        name='MA20',
                        line=dict(color='green', width=1)
                    ),
                    row=1, col=1
                )
            if 'MA60' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['MA60'],
                        name='MA60',
                        line=dict(color='purple', width=1)
                    ),
                    row=1, col=1
                )
        
        # 볼린저 밴드
        if self.bb_checkbox.isChecked() and 'BB_upper' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BB_upper'],
                    name='BB 상단',
                    line=dict(color='gray', width=1, dash='dash')
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BB_middle'],
                    name='BB 중간',
                    line=dict(color='gray', width=1)
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BB_lower'],
                    name='BB 하단',
                    line=dict(color='gray', width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(128,128,128,0.1)'
                ),
                row=1, col=1
            )
        
        # 평균 매수가 라인
        if self.avg_buy_checkbox.isChecked():
            positions = self.trading_engine.risk_manager.positions
            if stock_code in positions:
                avg_price = positions[stock_code].avg_price
                fig.add_hline(
                    y=avg_price,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"평균 매수가: {avg_price:,}원",
                    annotation_position="right",
                    row=1, col=1
                )
        
        # 서브플롯 카운터
        current_row = 2
        
        # 2. 거래량 차트
        if self.volume_checkbox.isChecked():
            colors = ['red' if row['Close'] >= row['Open'] else 'blue' for idx, row in df.iterrows()]
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='거래량',
                    marker_color=colors,
                    showlegend=False
                ),
                row=current_row, col=1
            )
            current_row += 1
        
        # 3. RSI 차트
        if self.rsi_checkbox.isChecked() and 'RSI' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['RSI'],
                    name='RSI',
                    line=dict(color='purple', width=1),
                    showlegend=False
                ),
                row=current_row, col=1
            )
            # RSI 기준선 (30, 70)
            fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=1, row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="blue", line_width=1, row=current_row, col=1)
            fig.update_yaxes(range=[0, 100], row=current_row, col=1)
            current_row += 1
        
        # 4. MACD 차트
        if self.macd_checkbox.isChecked() and 'MACD' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MACD'],
                    name='MACD',
                    line=dict(color='blue', width=1),
                    showlegend=False
                ),
                row=current_row, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MACD_signal'],
                    name='Signal',
                    line=dict(color='red', width=1),
                    showlegend=False
                ),
                row=current_row, col=1
            )
            if 'MACD_hist' in df.columns:
                colors = ['green' if val >= 0 else 'red' for val in df['MACD_hist']]
                fig.add_trace(
                    go.Bar(
                        x=df.index,
                        y=df['MACD_hist'],
                        name='Histogram',
                        marker_color=colors,
                        showlegend=False
                    ),
                    row=current_row, col=1
                )
            current_row += 1
        
        # 레이아웃 설정
        fig.update_layout(
            height=800,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            template='plotly_white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # x축 날짜 형식
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # 주말 숨기기
            ]
        )
        
        # HTML로 변환
        html_str = fig.to_html(include_plotlyjs='cdn', config={
            'displayModeBar': True,
            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
            'displaylogo': False
        })
        
        return html_str
    
    def load_and_display_stock(self, stock_code: str):
        """
        종목 데이터 조회 및 차트 표시
        
        Args:
            stock_code: 종목 코드
        """
        if not YFINANCE_AVAILABLE:
            return
        
        # 데이터 조회
        period = self.get_period_value()
        df = self.load_stock_data(stock_code, period)
        
        if df is None or df.empty:
            # 오류 메시지 표시
            error_html = f"""
            <html>
            <body style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial;">
                <div style="text-align: center;">
                    <h2>📊 데이터 조회 실패</h2>
                    <p>종목 코드: <b>{stock_code}</b></p>
                    <p>야후 파이낸스에서 데이터를 가져올 수 없습니다.</p>
                    <p>다음 사이트에서 확인하세요:</p>
                    <p><a href="https://finance.naver.com/item/main.naver?code={stock_code}" target="_blank">네이버 금융</a></p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(error_html)
            return
        
        # 지표 계산
        df = self.calculate_indicators(df)
        
        # 차트 생성
        html_str = self.create_chart(df, stock_code)
        
        # 차트 표시
        self.web_view.setHtml(html_str)
        
        print(f"✅ 차트 표시 완료: {stock_code}")
    
    def refresh_chart(self):
        """차트 새로고침"""
        if self.current_stock_code:
            # 캐시 삭제
            if self.current_stock_code in self.data_cache:
                del self.data_cache[self.current_stock_code]
            
            # 재조회 및 표시
            self.load_and_display_stock(self.current_stock_code)
    
    def update_price_data(self, stock_code: str, price: int, timestamp: Optional[datetime] = None):
        """
        실시간 가격 업데이트 (호환성 유지용 - 실제로는 yfinance 데이터 사용)
        
        Args:
            stock_code: 종목 코드
            price: 현재가
            timestamp: 시간 (사용 안 함)
        """
        # 실시간 업데이트는 하지 않음 (yfinance는 실시간 데이터 미제공)
        # 사용자가 새로고침 버튼을 클릭하면 최신 데이터 조회
        pass
    
    def update_profit_data(self, profit_rate: float, timestamp: Optional[datetime] = None):
        """
        수익률 업데이트 (호환성 유지용 - 사용 안 함)
        
        Args:
            profit_rate: 수익률 (%)
            timestamp: 시간 (사용 안 함)
        """
        # 사용 안 함 (개별 종목 차트에 집중)
        pass
    
    def add_trade_marker(self, stock_code: str, trade_type: str, price: int):
        """
        매매 마커 추가 (호환성 유지용 - 차트에 실시간 반영 안 됨)
        
        Args:
            stock_code: 종목 코드
            trade_type: 'buy' or 'sell'
            price: 거래 가격
        """
        # plotly 차트는 정적이므로 실시간 마커 추가 불가
        # 새로고침 시 평균 매수가 라인으로 표시됨
        pass

