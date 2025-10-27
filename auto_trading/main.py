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
import threading
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from kiwoom_api import KiwoomAPI
from trading_engine import TradingEngine
from monitor_gui import MonitorWindow
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


def create_surge_approval_callback():
    """급등주 승인 콜백 함수 생성"""
    
    def surge_approval_callback(stock_code: str, stock_name: str, surge_info: dict) -> bool:
        """
        급등주 매수 승인 요청
        
        Args:
            stock_code: 종목 코드
            stock_name: 종목명
            surge_info: 급등 정보 {'price', 'change_rate', 'volume_ratio'}
        
        Returns:
            승인 여부
        """
        try:
            # 급등 정보 출력
            print("\n" + "=" * 70)
            print("🚀 급등주 감지!")
            print("=" * 70)
            print(f"종목명:      {stock_name} ({stock_code})")
            print(f"현재가:      {surge_info['price']:,}원")
            print(f"상승률:      {surge_info['change_rate']:+.2f}%")
            print(f"거래량 비율: {surge_info['volume_ratio']:.2f}배")
            print("=" * 70)
            
            # 자동 승인 모드 확인
            if Config.SURGE_AUTO_APPROVE:
                log.success(f"✅ 급등주 자동 승인: {stock_name}")
                print("⚡ 자동 승인 모드: 즉시 매수 진행")
                print("=" * 70)
                return True
            
            # 수동 승인 모드: 사용자 입력 (타임아웃 30초)
            print("이 종목을 관심 종목에 추가하고 매수하시겠습니까?")
            print("승인: y/yes | 거부: n/no | 시간 제한: 30초")
            print("-" * 70)
            
            # 타임아웃을 위한 이벤트
            user_input = [None]
            input_event = threading.Event()
            
            def get_input():
                try:
                    user_input[0] = input("선택 (y/n): ").strip().lower()
                    input_event.set()
                except Exception as e:
                    log.error(f"입력 오류: {e}")
                    input_event.set()
            
            # 입력 스레드 시작
            input_thread = threading.Thread(target=get_input, daemon=True)
            input_thread.start()
            
            # 30초 대기
            if input_event.wait(timeout=30):
                # 사용자가 입력함
                response = user_input[0]
                if response in ['y', 'yes']:
                    log.success(f"✅ 급등주 매수 승인: {stock_name}")
                    return True
                else:
                    log.info(f"❌ 급등주 매수 거부: {stock_name}")
                    return False
            else:
                # 타임아웃
                log.warning(f"⏱️  시간 초과 (30초) - 급등주 매수 자동 거부: {stock_name}")
                return False
                
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
    
    # 모의투자 경고
    if Config.USE_SIMULATION:
        log.warning("⚠️  모의투자 모드로 실행합니다.")
        log.warning("실제 자금이 투자되지 않습니다.")
    else:
        log.critical("⚠️⚠️⚠️  실계좌 모드로 실행합니다! ⚠️⚠️⚠️")
        log.critical("실제 자금이 투자됩니다. 신중하게 사용하세요!")
        
        # 급등주 자동 승인 추가 경고
        if Config.ENABLE_SURGE_DETECTION and Config.SURGE_AUTO_APPROVE:
            log.critical("🔥 급등주 자동 승인이 활성화되어 있습니다!")
            log.critical("감지된 모든 급등주를 자동으로 매수합니다!")
        
        # 실계좌 확인
        response = input("\n정말 실계좌로 진행하시겠습니까? (yes 입력): ")
        if response.lower() != 'yes':
            log.info("사용자가 취소했습니다.")
            return 0
    
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
        log.info("📌 공동인증서 창이 자동으로 표시됩니다")
        log.info("📌 인증서를 선택하고 비밀번호를 입력하세요")
        log.info("📌 별도의 계좌 비밀번호 입력은 필요하지 않습니다")
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
        
        # 급등주 승인 콜백 설정
        if Config.ENABLE_SURGE_DETECTION and engine.surge_detector:
            surge_callback = create_surge_approval_callback()
            engine.set_surge_approval_callback(surge_callback)
            log.info("급등주 승인 콜백 등록 완료")
        
        # 모니터링 GUI 창 생성 및 표시
        log.info("📊 실시간 모니터링 GUI 창 생성 중...")
        monitor_window = MonitorWindow(engine)
        monitor_window.show()
        monitor_window.add_log("✅ 자동매매 프로그램 시작", "green")
        monitor_window.add_log(f"📋 관심 종목: {', '.join(Config.WATCH_LIST)}", "blue")
        if Config.ENABLE_SURGE_DETECTION:
            monitor_window.add_log("🚀 급등주 감지 활성화", "orange")
        
        # 엔진에 모니터 창 설정 (이벤트를 GUI에 전달)
        engine.set_monitor_window(monitor_window)
        
        log.success("✅ 모니터링 GUI 창 표시 완료!")
        
        # 안내 메시지
        print("\n" + "=" * 60)
        print("자동매매가 시작됩니다.")
        print("=" * 60)
        print("📊 실시간 시세를 모니터링하고 매매 신호를 생성합니다.")
        print("🤖 신호 발생 시 자동으로 주문을 전송합니다.")
        if Config.ENABLE_SURGE_DETECTION:
            if Config.SURGE_AUTO_APPROVE:
                print("🚀 급등주를 자동으로 감지하여 즉시 매수합니다. (자동 승인)")
                print("⚠️  모든 급등주가 자동으로 매수됩니다!")
            else:
                print("🚀 급등주를 자동으로 감지하여 승인을 요청합니다. (수동 승인)")
        print("⚠️  Ctrl+C를 눌러 언제든지 중지할 수 있습니다.")
        print("=" * 60)
        print()
        
        # 사용자 확인
        input("Enter 키를 눌러 자동매매를 시작하세요...")
        
        # 자동매매 시작 (논블로킹)
        engine.start_trading()
        
        # PyQt 이벤트 루프 실행 (GUI 응답 유지)
        log.info("📡 PyQt 이벤트 루프 실행 중... (GUI 응답 유지)")
        log.info("   종료하려면 Ctrl+C를 누르세요.")
        
        # Ctrl+C (SIGINT) 처리를 위한 signal 핸들러 설정
        def signal_handler(signum, frame):
            log.warning("\n🛑 Ctrl+C 감지 - 프로그램을 안전하게 종료합니다...")
            app.quit()
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Python의 시그널 처리를 허용하기 위한 타이머 (500ms마다 Python 코드 실행)
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)  # 빈 함수 실행으로 Python 시그널 체크
        
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

