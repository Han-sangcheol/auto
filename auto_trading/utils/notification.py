"""
알림 시스템 모듈

[파일 역할]
자동매매 프로그램의 주요 이벤트 발생 시 사용자에게 알림을 전송합니다.

[주요 기능]
- Windows 토스트 알림 표시
- 소리 알림 (선택적)
- 매매 체결 알림
- 급등주 감지 알림
- 손절/익절 알림
- 시스템 이벤트 알림

[사용 방법]
from notification import Notifier
notifier = Notifier()
notifier.notify_trade("매수", "삼성전자", 10, 75000)
"""

from typing import Optional
from utils.logger import log
import platform

# Windows 토스트 알림 (선택적)
try:
    if platform.system() == 'Windows':
        from win10toast import ToastNotifier
        TOAST_AVAILABLE = True
    else:
        TOAST_AVAILABLE = False
        log.debug("Windows 환경이 아니므로 토스트 알림을 사용할 수 없습니다.")
except ImportError:
    TOAST_AVAILABLE = False
    log.debug("win10toast 패키지가 설치되지 않았습니다. 알림 기능을 사용하려면 'pip install win10toast'를 실행하세요.")

# 소리 알림 (선택적)
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    log.debug("winsound 모듈을 로드할 수 없습니다. 소리 알림이 비활성화됩니다.")


class Notifier:
    """
    알림 관리 클래스
    """
    def __init__(self, enable_sound: bool = True):
        """
        Args:
            enable_sound: 소리 알림 활성화 여부
        """
        self.enable_sound = enable_sound and SOUND_AVAILABLE
        self.toast_notifier = None
        
        if TOAST_AVAILABLE:
            try:
                self.toast_notifier = ToastNotifier()
                log.info("Windows 토스트 알림 초기화 완료")
            except Exception as e:
                log.warning(f"토스트 알림 초기화 실패: {e}")
                self.toast_notifier = None
        
        if self.enable_sound:
            log.info("소리 알림 활성화")
        else:
            log.info("소리 알림 비활성화")
    
    def _play_sound(self, frequency: int = 1000, duration: int = 200):
        """
        소리 재생 (Windows만 지원)
        
        Args:
            frequency: 주파수 (Hz)
            duration: 지속 시간 (ms)
        """
        if not self.enable_sound:
            return
        
        try:
            winsound.Beep(frequency, duration)
        except Exception as e:
            log.debug(f"소리 재생 실패: {e}")
    
    def _show_toast(self, title: str, message: str, duration: int = 5):
        """
        토스트 알림 표시
        
        Args:
            title: 알림 제목
            message: 알림 내용
            duration: 표시 시간 (초)
        """
        if not self.toast_notifier:
            return
        
        try:
            # threaded=True로 설정하여 프로그램 블로킹 방지
            self.toast_notifier.show_toast(
                title=title,
                msg=message,
                duration=duration,
                threaded=True
            )
        except Exception as e:
            log.debug(f"토스트 알림 표시 실패: {e}")
    
    def notify_trade(
        self,
        trade_type: str,
        stock_name: str,
        quantity: int,
        price: int,
        profit_loss: Optional[int] = None
    ):
        """
        매매 체결 알림
        
        Args:
            trade_type: 매매 유형 ("매수" 또는 "매도")
            stock_name: 종목명
            quantity: 수량
            price: 가격
            profit_loss: 손익 (매도 시)
        """
        title = f"[CleonAI] {trade_type} 체결"
        message = f"{stock_name} {quantity}주 @ {price:,}원"
        
        if profit_loss is not None:
            profit_emoji = "📈" if profit_loss >= 0 else "📉"
            message += f"\n손익: {profit_emoji} {profit_loss:+,}원"
        
        log.info(f"📢 알림: {title} - {message}")
        self._show_toast(title, message)
        
        # 매수/매도 구분 소리
        if trade_type == "매수":
            self._play_sound(800, 150)
        else:
            self._play_sound(600, 150)
    
    def notify_surge(
        self,
        stock_name: str,
        stock_code: str,
        change_rate: float,
        volume_ratio: float
    ):
        """
        급등주 감지 알림
        
        Args:
            stock_name: 종목명
            stock_code: 종목코드
            change_rate: 변동률 (%)
            volume_ratio: 거래량 비율
        """
        title = "[CleonAI] 🚀 급등주 감지!"
        message = f"{stock_name} ({stock_code})\n" \
                  f"상승률: {change_rate:+.2f}% | 거래량: {volume_ratio:.1f}배"
        
        log.info(f"📢 알림: {title} - {message}")
        self._show_toast(title, message, duration=7)
        
        # 급등주 감지 특별 소리 (상승음)
        self._play_sound(1200, 100)
        self._play_sound(1400, 100)
        self._play_sound(1600, 100)
    
    def notify_stop_loss(
        self,
        stock_name: str,
        quantity: int,
        buy_price: int,
        sell_price: int,
        loss_amount: int
    ):
        """
        손절매 알림
        
        Args:
            stock_name: 종목명
            quantity: 수량
            buy_price: 매수가
            sell_price: 매도가
            loss_amount: 손실 금액
        """
        title = "[CleonAI] ⛔ 손절매 체결"
        message = f"{stock_name} {quantity}주\n" \
                  f"{buy_price:,}원 → {sell_price:,}원\n" \
                  f"손실: -{loss_amount:,}원"
        
        log.warning(f"📢 알림: {title} - {message}")
        self._show_toast(title, message, duration=7)
        
        # 손절매 경고음 (하강음)
        self._play_sound(800, 200)
        self._play_sound(600, 200)
    
    def notify_take_profit(
        self,
        stock_name: str,
        quantity: int,
        buy_price: int,
        sell_price: int,
        profit_amount: int
    ):
        """
        익절매 알림
        
        Args:
            stock_name: 종목명
            quantity: 수량
            buy_price: 매수가
            sell_price: 매도가
            profit_amount: 수익 금액
        """
        title = "[CleonAI] ✅ 익절매 체결"
        message = f"{stock_name} {quantity}주\n" \
                  f"{buy_price:,}원 → {sell_price:,}원\n" \
                  f"수익: +{profit_amount:,}원"
        
        log.info(f"📢 알림: {title} - {message}")
        self._show_toast(title, message, duration=7)
        
        # 익절매 성공음 (상승음)
        self._play_sound(1000, 150)
        self._play_sound(1200, 150)
        self._play_sound(1400, 150)
    
    def notify_daily_loss_limit(self, loss_amount: int, limit_percent: float):
        """
        일일 손실 한도 도달 알림
        
        Args:
            loss_amount: 손실 금액
            limit_percent: 한도 비율 (%)
        """
        title = "[CleonAI] 🛑 일일 손실 한도 도달"
        message = f"손실: -{loss_amount:,}원 (한도: {limit_percent}%)\n" \
                  f"자동매매를 중지합니다."
        
        log.error(f"📢 알림: {title} - {message}")
        self._show_toast(title, message, duration=10)
        
        # 긴급 경고음 (반복)
        for _ in range(3):
            self._play_sound(1500, 200)
    
    def notify_system_start(self):
        """시스템 시작 알림"""
        title = "[CleonAI] 🚀 자동매매 시작"
        message = "자동매매 프로그램이 시작되었습니다."
        
        log.info(f"📢 알림: {title}")
        self._show_toast(title, message)
        self._play_sound(1000, 200)
    
    def notify_system_stop(self):
        """시스템 종료 알림"""
        title = "[CleonAI] 🛑 자동매매 종료"
        message = "자동매매 프로그램이 종료되었습니다."
        
        log.info(f"📢 알림: {title}")
        self._show_toast(title, message)
        self._play_sound(600, 200)
    
    def notify_error(self, error_message: str):
        """에러 알림"""
        title = "[CleonAI] ⚠️ 에러 발생"
        message = f"에러: {error_message}"
        
        log.error(f"📢 알림: {title} - {message}")
        self._show_toast(title, message, duration=10)
        
        # 에러 경고음
        self._play_sound(1500, 300)


if __name__ == "__main__":
    # 테스트
    import time
    
    print("알림 시스템 테스트를 시작합니다...")
    notifier = Notifier(enable_sound=True)
    
    print("\n1. 시스템 시작 알림")
    notifier.notify_system_start()
    time.sleep(2)
    
    print("\n2. 매수 체결 알림")
    notifier.notify_trade("매수", "삼성전자", 10, 75000)
    time.sleep(2)
    
    print("\n3. 급등주 감지 알림")
    notifier.notify_surge("카카오", "035720", 8.5, 3.2)
    time.sleep(2)
    
    print("\n4. 익절매 체결 알림")
    notifier.notify_take_profit("SK하이닉스", 5, 140000, 154000, 70000)
    time.sleep(2)
    
    print("\n5. 매도 체결 알림 (손실)")
    notifier.notify_trade("매도", "LG화학", 3, 720000, -15000)
    time.sleep(2)
    
    print("\n6. 일일 손실 한도 알림")
    notifier.notify_daily_loss_limit(150000, 3.0)
    time.sleep(2)
    
    print("\n7. 시스템 종료 알림")
    notifier.notify_system_stop()
    
    print("\n테스트 완료!")
