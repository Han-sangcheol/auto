"""
자동매매 프로그램 메인 실행 파일

[파일 역할]
프로그램의 진입점으로, 전체 실행 흐름을 제어합니다.

[주요 기능]
- PyQt 애플리케이션 초기화
- 키움 API 로그인 처리
- 자동매매 엔진 시작
- 사용자 인터페이스 제공
- 예외 처리 및 안전한 종료

[실행 방법]
python main.py
또는
start.bat (더블클릭)
"""

import sys
import os
import signal
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from kiwoom_api import KiwoomAPI
from trading_engine import TradingEngine
from monitor_gui import MonitorWindow
from market_scheduler import MarketScheduler, MarketState
from logger import log
from config import Config


def print_banner():
    """프로그램 시작 배너 출력"""
    from datetime import datetime
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║          🤖 CleonAI 자동매매 프로그램 v1.3              ║
    ║                                                          ║
    ║          키움증권 Open API 기반 자동매매 시스템          ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 작업 디렉토리: {os.getcwd()}")
    print()


def confirm_real_account(parent):
    """
    실계좌 모드 확인 다이얼로그
    
    Args:
        parent: 부모 위젯
    
    Returns:
        사용자가 "예"를 선택하면 True, 아니면 False
    """
    reply = QMessageBox.warning(
        parent,
        "⚠️ 실계좌 모드 경고",
        "<h3>실계좌 모드로 실행됩니다!</h3>"
        "<p><b>실제 자금이 투자되며, 급등주가 자동으로 매수됩니다.</b></p>"
        "<hr>"
        "<p>다음 사항을 확인하세요:</p>"
        "<ul>"
        "<li>자동매매 전략이 충분히 검증되었습니까?</li>"
        "<li>리스크 관리 설정이 적절합니까?</li>"
        "<li>투자 가능한 자금이 준비되어 있습니까?</li>"
        "</ul>"
        "<hr>"
        "<p><b>정말 진행하시겠습니까?</b></p>",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return reply == QMessageBox.Yes


def create_surge_approval_callback(engine):
    """
    급등주 자동 승인 콜백 함수 생성 (자동 승인만 지원)
    
    Args:
        engine: TradingEngine 인스턴스
    """
    
    def surge_approval_callback(stock_code: str, candidate) -> bool:
        """
        급등주 자동 매수 승인 및 실행
        
        Args:
            stock_code: 종목 코드
            candidate: SurgeCandidate 객체
        
        Returns:
            승인 여부 (항상 True)
        """
        try:
            # 급등 정보 로그
            log.success(f"✅ 급등주 자동 승인: {candidate.name}")
            log.info(f"   종목코드: {stock_code}")
            log.info(f"   현재가: {candidate.current_price:,}원")
            log.info(f"   상승률: {candidate.current_change_rate:+.2f}%")
            log.info(f"   거래량 비율: {candidate.get_volume_ratio():.2f}배")
            
            # 매수 실행
            engine.add_surge_stock(stock_code, candidate)
            return True
                
        except Exception as e:
            log.error(f"승인 콜백 오류: {e}")
            return False
    
    return surge_approval_callback


def main():
    """메인 실행 함수"""
    
    # 배너 출력
    print_banner()
    
    # 로그 시스템 확인
    today = datetime.now().strftime("%Y-%m-%d")
    log.info("=" * 80)
    log.info(f"🚀 프로그램 시작 - {today}")
    log.info("=" * 80)
    log.info(f"📁 작업 디렉토리: {os.getcwd()}")
    log.info(f"📝 로그 파일: logs/trading_{today}.log")
    log.info(f"🐍 Python 버전: {sys.version}")
    log.info("설정 확인 중...")
    
    # 설정 유효성 검사
    validation_errors = Config.validate()
    if validation_errors:
        log.error("⚠️  설정 오류 발견:")
        for error in validation_errors:
            log.error(f"  - {error}")
        log.error("\n.env 파일을 확인하고 올바르게 설정해주세요.")
        log.error("예시: .env.example 파일을 참고하세요.")
        return 1
    
    # 설정 출력
    Config.print_config()
    
    # 모의투자/실계좌 모드 로그
    if Config.USE_SIMULATION:
        log.warning("⚠️  모의투자 모드로 실행합니다.")
        log.warning("실제 자금이 투자되지 않습니다.")
    else:
        log.critical("⚠️⚠️⚠️  실계좌 모드로 실행합니다! ⚠️⚠️⚠️")
        log.critical("실제 자금이 투자됩니다. 신중하게 사용하세요!")
        
        # 급등주 자동 승인 추가 경고
        if Config.ENABLE_SURGE_DETECTION:
            log.critical("🔥 급등주 자동 승인이 활성화되어 있습니다!")
            log.critical("감지된 모든 급등주를 자동으로 매수합니다!")
        
        # GUI 다이얼로그로 확인 (GUI 생성 후 처리)
    
    try:
        # PyQt 애플리케이션 생성
        log.info("PyQt 애플리케이션 초기화 중...")
        print("[INFO] Creating PyQt Application...")
        app = QApplication(sys.argv)
        print("[OK] PyQt Application created successfully")
        
        # 키움 API 초기화
        log.info("키움 API 초기화 중...")
        print("[INFO] Initializing Kiwoom OpenAPI...")
        print("       - Loading ActiveX Control: KHOPENAPI.KHOpenAPICtrl.1")
        print("       - This may take 5-10 seconds...")
        
        try:
            kiwoom = KiwoomAPI()
            print("[OK] Kiwoom OpenAPI initialized successfully")
        except Exception as api_error:
            print("[ERROR] Failed to initialize Kiwoom OpenAPI!")
            print(f"        Error: {api_error}")
            print("")
            print("Possible causes:")
            print("  1. Kiwoom Open API+ is not installed")
            print("     → Download: https://www.kiwoom.com/h/customer/download/VOpenApiInfoView")
            print("  2. Using 64-bit Python (Kiwoom requires 32-bit)")
            print("     → Check: python --version and verify it says '32 bit'")
            print("  3. ActiveX not registered properly")
            print("     → Run as Administrator and reinstall Open API+")
            print("")
            log.error(f"키움 API 초기화 실패: {api_error}")
            raise
        
        # 로그인
        log.info("=" * 80)
        log.info("🔐 키움증권 Open API 로그인")
        log.info("=" * 80)
        log.info("📌 [1단계] 공동인증서 창이 자동으로 표시됩니다")
        log.info("   → 인증서를 선택하고 비밀번호를 입력하세요")
        log.info("")
        log.info("📌 [2단계] 로그인 성공 후 계좌 비밀번호 등록창이 표시됩니다")
        log.info("   → 계좌를 선택하고 비밀번호(4자리)를 입력하세요")
        log.info("   → 모의투자 계좌 비밀번호: 0000 권장")
        log.info("   → 등록 후 'AUTO' 체크박스를 선택하면 다음부터 자동 로그인됩니다")
        log.info("=" * 80)
        log.info("")
        
        if not kiwoom.login():
            log.error("❌ 로그인 실패")
            log.error("문제 해결:")
            log.error("  1. 키움 Open API+가 설치되어 있는지 확인")
            log.error("  2. 공동인증서가 올바르게 등록되어 있는지 확인")
            log.error("  3. 모의투자/실계좌 설정이 올바른지 확인")
            return 1
        
        log.success("✅ 로그인 성공!")
        
        # 자동매매 엔진 초기화
        log.info("자동매매 엔진 초기화 중...")
        engine = TradingEngine(kiwoom)
        
        if not engine.initialize():
            log.error("❌ 엔진 초기화 실패")
            return 1
        
        log.success("✅ 엔진 초기화 완료!")
        
        # 시장 상태 확인 및 안내
        market_scheduler = MarketScheduler()
        market_state = market_scheduler.get_current_market_state()
        
        log.info("=" * 80)
        log.info("📊 시장 상태 확인")
        log.info("=" * 80)
        log.info(f"현재 상태: {market_state.value}")
        
        if market_state == MarketState.OPEN:
            log.success("✅ 정규 거래 시간입니다. 자동매매를 시작할 수 있습니다.")
            minutes_until_close = market_scheduler.get_time_until_market_close()
            hours = minutes_until_close // 60
            mins = minutes_until_close % 60
            log.info(f"장 마감까지: {hours}시간 {mins}분")
        elif market_state == MarketState.PRE_OPEN:
            minutes_until_open = market_scheduler.get_time_until_market_open()
            log.info(f"⏰ 장 시작 전입니다. {minutes_until_open}분 후 개장")
            log.info("실시간 데이터 수신은 시작하지만, 매매는 개장 후 실행됩니다.")
        elif market_state == MarketState.AFTER_HOURS:
            log.info("⚡ 시간외 매매 시간입니다.")
            if Config.ENABLE_AFTER_HOURS_TRADING:
                log.info("시간외 매매가 활성화되어 있습니다.")
            else:
                log.warning("시간외 매매가 비활성화되어 있습니다.")
        elif market_state in [MarketState.WEEKEND, MarketState.HOLIDAY, MarketState.CLOSED]:
            minutes_until_open = market_scheduler.get_time_until_market_open()
            hours = minutes_until_open // 60
            mins = minutes_until_open % 60
            log.warning(f"⚠️  현재 장외 시간입니다 ({market_state.value})")
            log.warning(f"장 시작까지: {hours}시간 {mins}분")
            
            if Config.AUTO_START_ENABLED:
                log.info("✅ 자동 시작이 활성화되어 있습니다.")
                log.info("'자동매매 시작' 버튼을 누르면 장 시작 시 자동으로 시작됩니다.")
            else:
                log.info("장 시작 후 '자동매매 시작' 버튼을 눌러주세요.")
        
        log.info("=" * 80)
        
        # 급등주 승인 콜백 설정
        if Config.ENABLE_SURGE_DETECTION and engine.surge_detector:
            surge_callback = create_surge_approval_callback(engine)  # engine 전달
            engine.set_surge_approval_callback(surge_callback)
            log.info("급등주 승인 콜백 등록 완료")
        
        # 모니터링 GUI 창 생성 및 표시
        log.info("📊 실시간 모니터링 GUI 창 생성 중...")
        monitor_window = MonitorWindow(engine)
        monitor_window.show()
        monitor_window.add_log("✅ 자동매매 프로그램 준비 완료", "green")
        monitor_window.add_log(f"📋 관심 종목: {', '.join(Config.WATCH_LIST)}", "blue")
        if Config.ENABLE_SURGE_DETECTION:
            monitor_window.add_log("🚀 급등주 감지 활성화 (자동 승인)", "orange")
        monitor_window.add_log("⏸ '자동매매 시작' 버튼을 눌러 시작하세요", "blue")
        
        # 엔진에 모니터 창 설정 (이벤트를 GUI에 전달)
        engine.set_monitor_window(monitor_window)
        
        log.success("✅ 모니터링 GUI 창 표시 완료!")
        
        # 실계좌 모드일 경우 확인 다이얼로그 표시
        if not Config.USE_SIMULATION:
            log.info("실계좌 모드 확인 다이얼로그 표시 중...")
            if not confirm_real_account(monitor_window):
                log.info("사용자가 실계좌 모드를 취소했습니다.")
                monitor_window.add_log("❌ 사용자가 실행을 취소했습니다.", "red")
                return 0
            else:
                log.info("사용자가 실계좌 모드를 승인했습니다.")
                monitor_window.add_log("✅ 실계좌 모드로 진행합니다.", "orange")
        
        # 안내 메시지
        print("\n" + "=" * 60)
        print("GUI 창이 표시되었습니다.")
        print("=" * 60)
        print("📊 GUI 창에서 '자동매매 시작' 버튼을 클릭하세요.")
        if Config.ENABLE_SURGE_DETECTION:
            print("🚀 급등주를 자동으로 감지하여 즉시 매수합니다.")
        print("⚠️  GUI 창을 닫거나 Ctrl+C를 눌러 종료할 수 있습니다.")
        print("=" * 60)
        print()
        
        # 자동매매는 GUI 버튼으로 시작 (자동 시작 제거)
        
        # PyQt 이벤트 루프 실행 (GUI 응답 유지)
        log.info("📡 PyQt 이벤트 루프 실행 중... (GUI 응답 유지)")
        log.info("   종료하려면 Ctrl+C를 누르세요.")
        
        # Ctrl+C (SIGINT) 처리를 위한 signal 핸들러 설정
        def signal_handler(signum, frame):
            log.warning("\n🛑 Ctrl+C 감지 - 프로그램을 안전하게 종료합니다...")
            app.quit()
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Python의 시그널 처리를 허용하기 위한 타이머 (500ms마다 Python 코드 실행)
        def keep_alive():
            """PyQt 이벤트 루프에서 Python 시그널 처리를 위한 빈 함수"""
            pass  # 명시적으로 None 반환 방지
        
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(keep_alive)  # 안전한 빈 함수 연결
        
        # 이벤트 루프 실행
        exit_code = app.exec_()
        
        # 종료 처리
        log.info("자동매매를 종료합니다...")
        engine.stop_trading()
        kiwoom.disconnect()
        
        # 최종 통계
        log.success("✅ 프로그램을 정상 종료했습니다.")
        
        return exit_code
        
    except KeyboardInterrupt:
        log.info("\n사용자가 프로그램을 중단했습니다.")
        # 안전한 종료
        try:
            if 'engine' in locals():
                engine.stop_trading()
            if 'kiwoom' in locals():
                kiwoom.disconnect()
        except:
            pass
        return 0
        
    except Exception as e:
        log.error(f"❌ 예상치 못한 오류 발생: {e}")
        log.error("상세 오류는 로그 파일을 확인하세요.")
        # 안전한 종료
        try:
            if 'engine' in locals():
                engine.stop_trading()
            if 'kiwoom' in locals():
                kiwoom.disconnect()
        except:
            pass
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        log.critical(f"치명적 오류: {e}")
        sys.exit(1)

