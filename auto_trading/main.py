"""
자동매매 프로그램 메인 실행 파일
"""

import sys
from PyQt5.QtWidgets import QApplication
from kiwoom_api import KiwoomAPI
from trading_engine import TradingEngine
from logger import log
from config import Config


def print_banner():
    """프로그램 시작 배너 출력"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║          🤖 CleonAI 자동매매 프로그램 v1.0              ║
    ║                                                          ║
    ║          키움증권 Open API 기반 자동매매 시스템          ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)
    print()


def main():
    """메인 실행 함수"""
    
    # 배너 출력
    print_banner()
    
    # 설정 확인
    log.info("프로그램 시작...")
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
        
        # 실계좌 확인
        response = input("\n정말 실계좌로 진행하시겠습니까? (yes 입력): ")
        if response.lower() != 'yes':
            log.info("사용자가 취소했습니다.")
            return 0
    
    try:
        # PyQt 애플리케이션 생성
        log.info("PyQt 애플리케이션 초기화 중...")
        app = QApplication(sys.argv)
        
        # 키움 API 초기화
        log.info("키움 API 초기화 중...")
        kiwoom = KiwoomAPI()
        
        # 로그인
        log.info("키움증권 로그인 중...")
        log.info("공동인증서 창이 나타나면 인증서를 선택하고 비밀번호를 입력하세요.")
        
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
        
        # 안내 메시지
        print("\n" + "=" * 60)
        print("자동매매가 시작됩니다.")
        print("=" * 60)
        print("📊 실시간 시세를 모니터링하고 매매 신호를 생성합니다.")
        print("🤖 신호 발생 시 자동으로 주문을 전송합니다.")
        print("⚠️  Ctrl+C를 눌러 언제든지 중지할 수 있습니다.")
        print("=" * 60)
        print()
        
        # 사용자 확인
        input("Enter 키를 눌러 자동매매를 시작하세요...")
        
        # 자동매매 시작
        engine.start_trading()
        
        # 종료 처리
        log.info("자동매매를 종료합니다...")
        kiwoom.disconnect()
        
        # 최종 통계
        log.success("✅ 프로그램을 정상 종료했습니다.")
        
        return 0
        
    except KeyboardInterrupt:
        log.info("\n사용자가 프로그램을 중단했습니다.")
        return 0
        
    except Exception as e:
        log.error(f"❌ 예상치 못한 오류 발생: {e}")
        log.error("상세 오류는 로그 파일을 확인하세요.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        log.critical(f"치명적 오류: {e}")
        sys.exit(1)

