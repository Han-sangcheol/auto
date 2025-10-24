"""
설정 화면

[파일 역할]
애플리케이션 설정 관리 (전략, 리스크, 시스템)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QGroupBox, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt


class SettingsView(QWidget):
    """설정 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("⚙️ 시스템 설정")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 탭 위젯
        tabs = QTabWidget()
        
        # 1. 매매 전략 설정
        strategy_tab = self.create_strategy_tab()
        tabs.addTab(strategy_tab, "매매 전략")
        
        # 2. 리스크 관리 설정
        risk_tab = self.create_risk_tab()
        tabs.addTab(risk_tab, "리스크 관리")
        
        # 3. 급등주 설정
        surge_tab = self.create_surge_tab()
        tabs.addTab(surge_tab, "급등주 감지")
        
        # 4. 시스템 설정
        system_tab = self.create_system_tab()
        tabs.addTab(system_tab, "시스템")
        
        layout.addWidget(tabs)
        
        # 하단: 저장 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("💾 설정 저장")
        self.save_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 30px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def create_strategy_tab(self) -> QWidget:
        """매매 전략 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 활성 전략 선택
        strategy_group = QGroupBox("활성 전략")
        strategy_layout = QVBoxLayout(strategy_group)
        
        self.ma_strategy_check = QCheckBox("이동평균 전략 (MA Crossover)")
        self.ma_strategy_check.setChecked(True)
        strategy_layout.addWidget(self.ma_strategy_check)
        
        self.rsi_strategy_check = QCheckBox("RSI 전략")
        self.rsi_strategy_check.setChecked(True)
        strategy_layout.addWidget(self.rsi_strategy_check)
        
        self.macd_strategy_check = QCheckBox("MACD 전략")
        self.macd_strategy_check.setChecked(True)
        strategy_layout.addWidget(self.macd_strategy_check)
        
        layout.addWidget(strategy_group)
        
        # MA 전략 설정
        ma_group = QGroupBox("이동평균 전략 설정")
        ma_layout = QFormLayout(ma_group)
        
        self.ma_short_input = QSpinBox()
        self.ma_short_input.setRange(5, 50)
        self.ma_short_input.setValue(5)
        ma_layout.addRow("단기 이동평균:", self.ma_short_input)
        
        self.ma_long_input = QSpinBox()
        self.ma_long_input.setRange(10, 200)
        self.ma_long_input.setValue(20)
        ma_layout.addRow("장기 이동평균:", self.ma_long_input)
        
        layout.addWidget(ma_group)
        
        # RSI 전략 설정
        rsi_group = QGroupBox("RSI 전략 설정")
        rsi_layout = QFormLayout(rsi_group)
        
        self.rsi_period_input = QSpinBox()
        self.rsi_period_input.setRange(5, 30)
        self.rsi_period_input.setValue(14)
        rsi_layout.addRow("RSI 기간:", self.rsi_period_input)
        
        self.rsi_oversold_input = QSpinBox()
        self.rsi_oversold_input.setRange(10, 40)
        self.rsi_oversold_input.setValue(30)
        rsi_layout.addRow("과매도 기준:", self.rsi_oversold_input)
        
        self.rsi_overbought_input = QSpinBox()
        self.rsi_overbought_input.setRange(60, 90)
        self.rsi_overbought_input.setValue(70)
        rsi_layout.addRow("과매수 기준:", self.rsi_overbought_input)
        
        layout.addWidget(rsi_group)
        
        layout.addStretch()
        return tab
    
    def create_risk_tab(self) -> QWidget:
        """리스크 관리 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 포지션 관리
        position_group = QGroupBox("포지션 관리")
        position_layout = QFormLayout(position_group)
        
        self.max_stocks_input = QSpinBox()
        self.max_stocks_input.setRange(1, 10)
        self.max_stocks_input.setValue(3)
        position_layout.addRow("최대 보유 종목:", self.max_stocks_input)
        
        self.position_size_input = QDoubleSpinBox()
        self.position_size_input.setRange(1.0, 50.0)
        self.position_size_input.setValue(10.0)
        self.position_size_input.setSuffix("%")
        position_layout.addRow("포지션 크기 (계좌 대비):", self.position_size_input)
        
        layout.addWidget(position_group)
        
        # 손절/익절 설정
        stop_group = QGroupBox("손절/익절 설정")
        stop_layout = QFormLayout(stop_group)
        
        self.stop_loss_input = QDoubleSpinBox()
        self.stop_loss_input.setRange(1.0, 20.0)
        self.stop_loss_input.setValue(5.0)
        self.stop_loss_input.setSuffix("%")
        stop_layout.addRow("손절 기준:", self.stop_loss_input)
        
        self.take_profit_input = QDoubleSpinBox()
        self.take_profit_input.setRange(5.0, 50.0)
        self.take_profit_input.setValue(10.0)
        self.take_profit_input.setSuffix("%")
        stop_layout.addRow("익절 기준:", self.take_profit_input)
        
        layout.addWidget(stop_group)
        
        # 일일 한도
        daily_group = QGroupBox("일일 한도")
        daily_layout = QFormLayout(daily_group)
        
        self.daily_loss_limit_input = QDoubleSpinBox()
        self.daily_loss_limit_input.setRange(1.0, 10.0)
        self.daily_loss_limit_input.setValue(3.0)
        self.daily_loss_limit_input.setSuffix("%")
        daily_layout.addRow("일일 손실 한도:", self.daily_loss_limit_input)
        
        layout.addWidget(daily_group)
        
        layout.addStretch()
        return tab
    
    def create_surge_tab(self) -> QWidget:
        """급등주 감지 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 급등주 감지 활성화
        self.surge_enable_check = QCheckBox("급등주 자동 감지 활성화")
        self.surge_enable_check.setChecked(True)
        layout.addWidget(self.surge_enable_check)
        
        # 감지 조건
        detection_group = QGroupBox("감지 조건")
        detection_layout = QFormLayout(detection_group)
        
        self.surge_min_change_rate_input = QDoubleSpinBox()
        self.surge_min_change_rate_input.setRange(1.0, 30.0)
        self.surge_min_change_rate_input.setValue(5.0)
        self.surge_min_change_rate_input.setSuffix("%")
        detection_layout.addRow("최소 상승률:", self.surge_min_change_rate_input)
        
        self.surge_min_volume_ratio_input = QDoubleSpinBox()
        self.surge_min_volume_ratio_input.setRange(1.0, 10.0)
        self.surge_min_volume_ratio_input.setValue(2.0)
        self.surge_min_volume_ratio_input.setSuffix("배")
        detection_layout.addRow("최소 거래량 비율:", self.surge_min_volume_ratio_input)
        
        self.surge_cooldown_input = QSpinBox()
        self.surge_cooldown_input.setRange(5, 120)
        self.surge_cooldown_input.setValue(30)
        self.surge_cooldown_input.setSuffix("분")
        detection_layout.addRow("재감지 쿨다운:", self.surge_cooldown_input)
        
        layout.addWidget(detection_group)
        
        # 자동 매수
        auto_buy_group = QGroupBox("자동 매수")
        auto_buy_layout = QVBoxLayout(auto_buy_group)
        
        self.surge_auto_approve_check = QCheckBox("급등주 자동 매수 활성화 (사용자 승인 없이)")
        self.surge_auto_approve_check.setChecked(False)
        auto_buy_layout.addWidget(self.surge_auto_approve_check)
        
        layout.addWidget(auto_buy_group)
        
        layout.addStretch()
        return tab
    
    def create_system_tab(self) -> QWidget:
        """시스템 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API 연결
        api_group = QGroupBox("API 연결")
        api_layout = QFormLayout(api_group)
        
        self.api_url_input = QLineEdit()
        self.api_url_input.setText("http://localhost:8000")
        api_layout.addRow("Backend URL:", self.api_url_input)
        
        layout.addWidget(api_group)
        
        # 로그 설정
        log_group = QGroupBox("로그 설정")
        log_layout = QFormLayout(log_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        log_layout.addRow("로그 레벨:", self.log_level_combo)
        
        layout.addWidget(log_group)
        
        # 자동 매매
        auto_trading_group = QGroupBox("자동 매매")
        auto_trading_layout = QVBoxLayout(auto_trading_group)
        
        self.auto_trading_check = QCheckBox("자동 매매 활성화")
        self.auto_trading_check.setChecked(False)
        auto_trading_layout.addWidget(self.auto_trading_check)
        
        layout.addWidget(auto_trading_group)
        
        layout.addStretch()
        return tab
    
    def load_settings(self):
        """설정 불러오기"""
        # TODO: API를 통해 실제 설정 불러오기
        pass
    
    def save_settings(self):
        """설정 저장"""
        try:
            # TODO: API를 통해 실제 설정 저장
            QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"설정 저장 중 오류: {str(e)}")

