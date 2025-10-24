"""
Trading Engine 메인 진입점

키움 OpenAPI를 사용한 자동매매 엔진 (32-bit Python 전용)
"""

import sys
from PyQt5.QtWidgets import QApplication
from core.engine import TradingEngine
from brokers.kiwoom import KiwoomBroker
from loguru import logger


def setup_logging():
    """로깅 설정"""
    logger.remove()  # 기본 핸들러 제거
    
    # 콘솔 출력
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 파일 출력
    logger.add(
        "logs/trading_engine.log",
        rotation="00:00",  # 자정에 로테이션
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG"
    )


def main():
    """메인 함수"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║      ⚡ CleonAI Trading Engine v1.0                     ║
    ║                                                          ║
    ║      키움 OpenAPI 자동매매 엔진 (32-bit)                ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # 로깅 초기화
    setup_logging()
    logger.info("Trading Engine 시작")
    
    # Qt 애플리케이션 생성 (키움 API 요구사항)
    app = QApplication(sys.argv)
    
    try:
        # 키움 브로커 초기화
        logger.info("키움 브로커 초기화 중...")
        broker = KiwoomBroker()
        
        # 로그인
        if not broker.login():
            logger.error("키움 로그인 실패")
            return 1
        
        logger.success("키움 로그인 성공")
        
        # Trading Engine 초기화
        logger.info("Trading Engine 초기화 중...")
        engine = TradingEngine(broker)
        
        if not engine.initialize():
            logger.error("Trading Engine 초기화 실패")
            return 1
        
        logger.success("Trading Engine 초기화 완료")
        
        # 자동매매 시작
        logger.info("자동매매 시작")
        engine.start()
        
        # Qt 이벤트 루프 실행
        sys.exit(app.exec_())
    
    except KeyboardInterrupt:
        logger.info("사용자가 중단했습니다.")
        return 0
    
    except Exception as e:
        logger.exception(f"오류 발생: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

