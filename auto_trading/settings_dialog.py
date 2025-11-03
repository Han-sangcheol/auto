"""
설정 대화상자 모듈

[파일 역할]
매매 전략, 리스크 관리, 급등주 감지 등의 설정을 GUI에서 변경할 수 있는 대화상자입니다.

[주요 기능]
- 전략 파라미터 실시간 조정
- 리스크 관리 설정 변경
- 급등주 감지 기준 설정
- 설정 저장 (.env 파일 업데이트)

[사용 방법]
from settings_dialog import SettingsDialog
dialog = SettingsDialog(config)
if dialog.exec_() == QDialog.Accepted:
    new_settings = dialog.get_settings()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox,
    QTabWidget, QWidget, QMessageBox, QFormLayout, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Dict
import os


class SettingsDialog(QDialog):
    """
    설정 대화상자
    """
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.settings = {}
        
        self.setWindowTitle("설정")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 탭 1: 매매 전략
        strategy_tab = self.create_strategy_tab()
        self.tab_widget.addTab(strategy_tab, "📈 매매 전략")
        
        # 탭 2: 리스크 관리
        risk_tab = self.create_risk_tab()
        self.tab_widget.addTab(risk_tab, "🛡️ 리스크 관리")
        
        # 탭 3: 급등주 감지
        surge_tab = self.create_surge_tab()
        self.tab_widget.addTab(surge_tab, "🚀 급등주 감지")
        
        main_layout.addWidget(self.tab_widget)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton("기본값 복원")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def create_strategy_tab(self) -> QWidget:
        """매매 전략 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 이동평균선 그룹
        ma_group = QGroupBox("이동평균선 (MA)")
        ma_layout = QFormLayout()
        
        self.ma_short_spin = QSpinBox()
        self.ma_short_spin.setRange(1, 50)
        self.ma_short_spin.setSuffix("일")
        ma_layout.addRow("단기 이동평균:", self.ma_short_spin)
        
        self.ma_long_spin = QSpinBox()
        self.ma_long_spin.setRange(5, 200)
        self.ma_long_spin.setSuffix("일")
        ma_layout.addRow("장기 이동평균:", self.ma_long_spin)
        
        ma_group.setLayout(ma_layout)
        layout.addWidget(ma_group)
        
        # RSI 그룹
        rsi_group = QGroupBox("RSI")
        rsi_layout = QFormLayout()
        
        self.rsi_period_spin = QSpinBox()
        self.rsi_period_spin.setRange(5, 30)
        self.rsi_period_spin.setSuffix("일")
        rsi_layout.addRow("RSI 기간:", self.rsi_period_spin)
        
        self.rsi_oversold_spin = QDoubleSpinBox()
        self.rsi_oversold_spin.setRange(10, 40)
        self.rsi_oversold_spin.setDecimals(0)
        rsi_layout.addRow("과매도 기준:", self.rsi_oversold_spin)
        
        self.rsi_overbought_spin = QDoubleSpinBox()
        self.rsi_overbought_spin.setRange(60, 90)
        self.rsi_overbought_spin.setDecimals(0)
        rsi_layout.addRow("과매수 기준:", self.rsi_overbought_spin)
        
        rsi_group.setLayout(rsi_layout)
        layout.addWidget(rsi_group)
        
        # MACD 그룹
        macd_group = QGroupBox("MACD")
        macd_layout = QFormLayout()
        
        self.macd_fast_spin = QSpinBox()
        self.macd_fast_spin.setRange(5, 20)
        macd_layout.addRow("빠른선 (Fast):", self.macd_fast_spin)
        
        self.macd_slow_spin = QSpinBox()
        self.macd_slow_spin.setRange(20, 40)
        macd_layout.addRow("느린선 (Slow):", self.macd_slow_spin)
        
        self.macd_signal_spin = QSpinBox()
        self.macd_signal_spin.setRange(5, 15)
        macd_layout.addRow("시그널선:", self.macd_signal_spin)
        
        macd_group.setLayout(macd_layout)
        layout.addWidget(macd_group)
        
        # 통합 전략 그룹
        multi_group = QGroupBox("통합 전략")
        multi_layout = QFormLayout()
        
        self.min_signal_spin = QSpinBox()
        self.min_signal_spin.setRange(1, 3)
        self.min_signal_spin.setSuffix(" / 3")
        multi_layout.addRow("최소 신호 강도:", self.min_signal_spin)
        
        label = QLabel("※ 1=공격적, 2=균형, 3=보수적")
        label.setStyleSheet("color: gray; font-size: 9pt;")
        multi_layout.addRow("", label)
        
        multi_group.setLayout(multi_layout)
        layout.addWidget(multi_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_risk_tab(self) -> QWidget:
        """리스크 관리 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 기본 설정 그룹
        basic_group = QGroupBox("기본 설정")
        basic_layout = QFormLayout()
        
        self.max_stocks_spin = QSpinBox()
        self.max_stocks_spin.setRange(1, 10)
        self.max_stocks_spin.setSuffix("개")
        basic_layout.addRow("최대 보유 종목:", self.max_stocks_spin)
        
        self.auto_trading_ratio_spin = QDoubleSpinBox()
        self.auto_trading_ratio_spin.setRange(10.0, 100.0)
        self.auto_trading_ratio_spin.setSingleStep(5.0)
        self.auto_trading_ratio_spin.setSuffix("%")
        self.auto_trading_ratio_spin.setToolTip("전체 잔고 중 자동매매에 사용할 비율 (나머지는 수동매매/예비금)")
        basic_layout.addRow("자동매매 투자 비율:", self.auto_trading_ratio_spin)
        
        self.position_size_spin = QDoubleSpinBox()
        self.position_size_spin.setRange(1.0, 50.0)
        self.position_size_spin.setSingleStep(1.0)
        self.position_size_spin.setSuffix("%")
        self.position_size_spin.setToolTip("자동매매 잔고 중 한 종목에 투자할 비율")
        basic_layout.addRow("종목당 투자 비율:", self.position_size_spin)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # 손익 관리 그룹
        profit_loss_group = QGroupBox("손익 관리")
        profit_loss_layout = QFormLayout()
        
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(1.0, 20.0)
        self.stop_loss_spin.setSingleStep(0.5)
        self.stop_loss_spin.setSuffix("%")
        profit_loss_layout.addRow("손절매 비율:", self.stop_loss_spin)
        
        self.take_profit_spin = QDoubleSpinBox()
        self.take_profit_spin.setRange(5.0, 50.0)
        self.take_profit_spin.setSingleStep(1.0)
        self.take_profit_spin.setSuffix("%")
        profit_loss_layout.addRow("익절매 비율:", self.take_profit_spin)
        
        self.daily_loss_limit_spin = QDoubleSpinBox()
        self.daily_loss_limit_spin.setRange(1.0, 10.0)
        self.daily_loss_limit_spin.setSingleStep(0.5)
        self.daily_loss_limit_spin.setSuffix("%")
        profit_loss_layout.addRow("일일 손실 한도:", self.daily_loss_limit_spin)
        
        profit_loss_group.setLayout(profit_loss_layout)
        layout.addWidget(profit_loss_group)
        
        # 추가 매수 설정 그룹 (물타기)
        average_down_group = QGroupBox("추가 매수 (물타기 전략)")
        average_down_layout = QFormLayout()
        
        self.enable_average_down_check = QCheckBox()
        self.enable_average_down_check.setToolTip(
            "손실 발생 시 추가 매수로 평균 매수가를 낮추는 전략\n"
            "주의: 위험도가 높으므로 충분한 테스트 후 사용하세요."
        )
        average_down_layout.addRow("추가 매수 활성화:", self.enable_average_down_check)
        
        self.average_down_trigger_spin = QDoubleSpinBox()
        self.average_down_trigger_spin.setRange(0.5, 10.0)
        self.average_down_trigger_spin.setSingleStep(0.5)
        self.average_down_trigger_spin.setSuffix("%")
        self.average_down_trigger_spin.setToolTip(
            "평균가 대비 이 비율만큼 하락 시 추가 매수 실행\n"
            "예: 2.5% = 평균가 대비 -2.5% 하락 시 추가 매수"
        )
        average_down_layout.addRow("추가 매수 트리거:", self.average_down_trigger_spin)
        
        self.max_average_down_spin = QSpinBox()
        self.max_average_down_spin.setRange(1, 5)
        self.max_average_down_spin.setToolTip("무한 물타기 방지를 위한 최대 추가 매수 횟수")
        average_down_layout.addRow("최대 추가 매수 횟수:", self.max_average_down_spin)
        
        self.average_down_size_ratio_spin = QDoubleSpinBox()
        self.average_down_size_ratio_spin.setRange(0.5, 3.0)
        self.average_down_size_ratio_spin.setSingleStep(0.5)
        self.average_down_size_ratio_spin.setValue(1.0)
        self.average_down_size_ratio_spin.setToolTip(
            "첫 매수 대비 추가 매수할 수량의 비율\n"
            "1.0 = 첫 매수와 같은 수량\n"
            "2.0 = 첫 매수의 2배 수량"
        )
        average_down_layout.addRow("추가 매수 수량 비율:", self.average_down_size_ratio_spin)
        
        average_down_group.setLayout(average_down_layout)
        layout.addWidget(average_down_group)
        
        # 경고 메시지
        warning_label = QLabel(
            "⚠️ 주의: 리스크 관리 설정은 신중하게 변경하세요.\n"
            "손절매 비율이 너무 크면 손실이 확대될 수 있습니다.\n"
            "추가 매수(물타기)는 위험도가 높으니 신중하게 사용하세요."
        )
        warning_label.setStyleSheet(
            "background-color: #fff3cd; "
            "border: 1px solid #ffc107; "
            "padding: 10px; "
            "border-radius: 5px; "
            "color: #856404;"
        )
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_surge_tab(self) -> QWidget:
        """급등주 감지 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 감지 기준 그룹
        criteria_group = QGroupBox("감지 기준")
        criteria_layout = QFormLayout()
        
        self.surge_min_change_spin = QDoubleSpinBox()
        self.surge_min_change_spin.setRange(1.0, 20.0)
        self.surge_min_change_spin.setSingleStep(0.5)
        self.surge_min_change_spin.setSuffix("%")
        criteria_layout.addRow("최소 상승률:", self.surge_min_change_spin)
        
        self.surge_min_volume_spin = QDoubleSpinBox()
        self.surge_min_volume_spin.setRange(1.0, 10.0)
        self.surge_min_volume_spin.setSingleStep(0.1)
        self.surge_min_volume_spin.setSuffix("배")
        criteria_layout.addRow("최소 거래량 비율:", self.surge_min_volume_spin)
        
        self.surge_candidate_spin = QSpinBox()
        self.surge_candidate_spin.setRange(50, 300)
        self.surge_candidate_spin.setSingleStep(10)
        self.surge_candidate_spin.setSuffix("개")
        criteria_layout.addRow("후보 종목 수:", self.surge_candidate_spin)
        
        criteria_group.setLayout(criteria_layout)
        layout.addWidget(criteria_group)
        
        # 재감지 관리 그룹
        cooldown_group = QGroupBox("재감지 관리")
        cooldown_layout = QFormLayout()
        
        self.surge_cooldown_spin = QSpinBox()
        self.surge_cooldown_spin.setRange(10, 120)
        self.surge_cooldown_spin.setSingleStep(5)
        self.surge_cooldown_spin.setSuffix("분")
        cooldown_layout.addRow("재감지 대기시간:", self.surge_cooldown_spin)
        
        cooldown_group.setLayout(cooldown_layout)
        layout.addWidget(cooldown_group)
        
        # 설명 레이블
        info_label = QLabel(
            "💡 급등주 감지 설정은 실시간으로 적용됩니다.\n"
            "상승률과 거래량 비율이 높을수록 더 강한 급등주만 감지됩니다."
        )
        info_label.setStyleSheet(
            "background-color: #d1ecf1; "
            "border: 1px solid #bee5eb; "
            "padding: 10px; "
            "border-radius: 5px; "
            "color: #0c5460;"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def load_current_settings(self):
        """현재 설정 불러오기"""
        try:
            # 매매 전략
            self.ma_short_spin.setValue(self.config.MA_SHORT_PERIOD)
            self.ma_long_spin.setValue(self.config.MA_LONG_PERIOD)
            
            self.rsi_period_spin.setValue(self.config.RSI_PERIOD)
            self.rsi_oversold_spin.setValue(self.config.RSI_OVERSOLD)
            self.rsi_overbought_spin.setValue(self.config.RSI_OVERBOUGHT)
            
            self.macd_fast_spin.setValue(self.config.MACD_FAST)
            self.macd_slow_spin.setValue(self.config.MACD_SLOW)
            self.macd_signal_spin.setValue(self.config.MACD_SIGNAL)
            
            self.min_signal_spin.setValue(self.config.MIN_SIGNAL_STRENGTH)
            
            # 리스크 관리
            self.max_stocks_spin.setValue(self.config.MAX_STOCKS)
            self.auto_trading_ratio_spin.setValue(self.config.AUTO_TRADING_RATIO)
            self.position_size_spin.setValue(self.config.POSITION_SIZE_PERCENT)
            self.stop_loss_spin.setValue(self.config.STOP_LOSS_PERCENT)
            self.take_profit_spin.setValue(self.config.TAKE_PROFIT_PERCENT)
            self.daily_loss_limit_spin.setValue(self.config.DAILY_LOSS_LIMIT_PERCENT)
            
            # 추가 매수 (물타기)
            self.enable_average_down_check.setChecked(self.config.ENABLE_AVERAGE_DOWN)
            self.average_down_trigger_spin.setValue(self.config.AVERAGE_DOWN_TRIGGER_PERCENT)
            self.max_average_down_spin.setValue(self.config.MAX_AVERAGE_DOWN_COUNT)
            self.average_down_size_ratio_spin.setValue(self.config.AVERAGE_DOWN_SIZE_RATIO)
            
            # 급등주 감지
            self.surge_min_change_spin.setValue(self.config.SURGE_MIN_CHANGE_RATE)
            self.surge_min_volume_spin.setValue(self.config.SURGE_MIN_VOLUME_RATIO)
            self.surge_candidate_spin.setValue(self.config.SURGE_CANDIDATE_COUNT)
            self.surge_cooldown_spin.setValue(self.config.SURGE_COOLDOWN_MINUTES)
            
        except Exception as e:
            print(f"설정 불러오기 오류: {e}")
    
    def get_settings(self) -> Dict:
        """변경된 설정 반환"""
        return {
            # 매매 전략
            'MA_SHORT_PERIOD': self.ma_short_spin.value(),
            'MA_LONG_PERIOD': self.ma_long_spin.value(),
            'RSI_PERIOD': self.rsi_period_spin.value(),
            'RSI_OVERSOLD': self.rsi_oversold_spin.value(),
            'RSI_OVERBOUGHT': self.rsi_overbought_spin.value(),
            'MACD_FAST': self.macd_fast_spin.value(),
            'MACD_SLOW': self.macd_slow_spin.value(),
            'MACD_SIGNAL': self.macd_signal_spin.value(),
            'MIN_SIGNAL_STRENGTH': self.min_signal_spin.value(),
            
            # 리스크 관리
            'MAX_STOCKS': self.max_stocks_spin.value(),
            'AUTO_TRADING_RATIO': self.auto_trading_ratio_spin.value(),
            'POSITION_SIZE_PERCENT': self.position_size_spin.value(),
            'STOP_LOSS_PERCENT': self.stop_loss_spin.value(),
            'TAKE_PROFIT_PERCENT': self.take_profit_spin.value(),
            'DAILY_LOSS_LIMIT_PERCENT': self.daily_loss_limit_spin.value(),
            
            # 추가 매수 (물타기)
            'ENABLE_AVERAGE_DOWN': self.enable_average_down_check.isChecked(),
            'AVERAGE_DOWN_TRIGGER_PERCENT': self.average_down_trigger_spin.value(),
            'MAX_AVERAGE_DOWN_COUNT': self.max_average_down_spin.value(),
            'AVERAGE_DOWN_SIZE_RATIO': self.average_down_size_ratio_spin.value(),
            
            # 급등주 감지
            'SURGE_MIN_CHANGE_RATE': self.surge_min_change_spin.value(),
            'SURGE_MIN_VOLUME_RATIO': self.surge_min_volume_spin.value(),
            'SURGE_CANDIDATE_COUNT': self.surge_candidate_spin.value(),
            'SURGE_COOLDOWN_MINUTES': self.surge_cooldown_spin.value(),
        }
    
    def save_settings(self):
        """설정 저장 (.env 파일 업데이트)"""
        try:
            # 설정 가져오기
            new_settings = self.get_settings()
            
            # .env 파일 경로
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            
            if not os.path.exists(env_path):
                QMessageBox.warning(
                    self,
                    "경고",
                    ".env 파일을 찾을 수 없습니다.\n"
                    "설정이 저장되지 않았습니다."
                )
                return
            
            # .env 파일 읽기
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 설정 업데이트
            updated_lines = []
            updated_keys = set()
            
            for line in lines:
                updated = False
                for key, value in new_settings.items():
                    if line.startswith(f"{key}="):
                        updated_lines.append(f"{key}={value}\n")
                        updated_keys.add(key)
                        updated = True
                        break
                
                if not updated:
                    updated_lines.append(line)
            
            # 누락된 설정 추가
            for key, value in new_settings.items():
                if key not in updated_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # .env 파일 쓰기
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            # 성공 메시지
            QMessageBox.information(
                self,
                "저장 완료",
                "설정이 .env 파일에 저장되었습니다.\n\n"
                "⚠️ 주의: 설정을 적용하려면 프로그램을 재시작해야 합니다."
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"설정 저장 중 오류가 발생했습니다:\n{e}"
            )
    
    def reset_to_defaults(self):
        """기본값으로 복원"""
        reply = QMessageBox.question(
            self,
            "기본값 복원",
            "모든 설정을 기본값으로 복원하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 기본값 설정
            defaults = {
                # 매매 전략
                'MA_SHORT_PERIOD': 5,
                'MA_LONG_PERIOD': 20,
                'RSI_PERIOD': 14,
                'RSI_OVERSOLD': 30,
                'RSI_OVERBOUGHT': 70,
                'MACD_FAST': 12,
                'MACD_SLOW': 26,
                'MACD_SIGNAL': 9,
                'MIN_SIGNAL_STRENGTH': 2,
                
                # 리스크 관리
                'MAX_STOCKS': 3,
                'AUTO_TRADING_RATIO': 80.0,
                'POSITION_SIZE_PERCENT': 10.0,
                'STOP_LOSS_PERCENT': 5.0,
                'TAKE_PROFIT_PERCENT': 10.0,
                'DAILY_LOSS_LIMIT_PERCENT': 3.0,
                
                # 추가 매수 (물타기)
                'ENABLE_AVERAGE_DOWN': False,
                'AVERAGE_DOWN_TRIGGER_PERCENT': 2.5,
                'MAX_AVERAGE_DOWN_COUNT': 2,
                'AVERAGE_DOWN_SIZE_RATIO': 1.0,
                
                # 급등주 감지
                'SURGE_MIN_CHANGE_RATE': 5.0,
                'SURGE_MIN_VOLUME_RATIO': 2.0,
                'SURGE_CANDIDATE_COUNT': 100,
                'SURGE_COOLDOWN_MINUTES': 30,
            }
            
            # UI에 기본값 적용
            self.ma_short_spin.setValue(defaults['MA_SHORT_PERIOD'])
            self.ma_long_spin.setValue(defaults['MA_LONG_PERIOD'])
            self.rsi_period_spin.setValue(defaults['RSI_PERIOD'])
            self.rsi_oversold_spin.setValue(defaults['RSI_OVERSOLD'])
            self.rsi_overbought_spin.setValue(defaults['RSI_OVERBOUGHT'])
            self.macd_fast_spin.setValue(defaults['MACD_FAST'])
            self.macd_slow_spin.setValue(defaults['MACD_SLOW'])
            self.macd_signal_spin.setValue(defaults['MACD_SIGNAL'])
            self.min_signal_spin.setValue(defaults['MIN_SIGNAL_STRENGTH'])
            
            self.max_stocks_spin.setValue(defaults['MAX_STOCKS'])
            self.auto_trading_ratio_spin.setValue(defaults['AUTO_TRADING_RATIO'])
            self.position_size_spin.setValue(defaults['POSITION_SIZE_PERCENT'])
            self.stop_loss_spin.setValue(defaults['STOP_LOSS_PERCENT'])
            self.take_profit_spin.setValue(defaults['TAKE_PROFIT_PERCENT'])
            self.daily_loss_limit_spin.setValue(defaults['DAILY_LOSS_LIMIT_PERCENT'])
            
            self.enable_average_down_check.setChecked(defaults['ENABLE_AVERAGE_DOWN'])
            self.average_down_trigger_spin.setValue(defaults['AVERAGE_DOWN_TRIGGER_PERCENT'])
            self.max_average_down_spin.setValue(defaults['MAX_AVERAGE_DOWN_COUNT'])
            self.average_down_size_ratio_spin.setValue(defaults['AVERAGE_DOWN_SIZE_RATIO'])
            
            self.surge_min_change_spin.setValue(defaults['SURGE_MIN_CHANGE_RATE'])
            self.surge_min_volume_spin.setValue(defaults['SURGE_MIN_VOLUME_RATIO'])
            self.surge_candidate_spin.setValue(defaults['SURGE_CANDIDATE_COUNT'])
            self.surge_cooldown_spin.setValue(defaults['SURGE_COOLDOWN_MINUTES'])
            
            QMessageBox.information(
                self,
                "복원 완료",
                "모든 설정이 기본값으로 복원되었습니다.\n"
                "'저장' 버튼을 눌러 적용하세요."
            )


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from config import Config
    
    app = QApplication(sys.argv)
    
    dialog = SettingsDialog(Config)
    
    if dialog.exec_() == QDialog.Accepted:
        print("설정이 저장되었습니다:")
        print(dialog.get_settings())
    else:
        print("취소됨")
    
    sys.exit()

