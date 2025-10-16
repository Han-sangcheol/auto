"""
로깅 시스템 모듈
Loguru를 사용하여 파일과 콘솔에 로그를 기록합니다.
"""

import sys
from pathlib import Path
from loguru import logger
from config import Config


class Logger:
    """로깅 설정 및 관리 클래스"""
    
    def __init__(self):
        self.setup_logger()
    
    def setup_logger(self):
        """로거 설정"""
        # 기존 핸들러 제거
        logger.remove()
        
        # 콘솔 로그 설정 (색상 포함)
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
            level=Config.LOG_LEVEL,
            colorize=True
        )
        
        # 로그 디렉토리 생성
        log_path = Path(Config.LOG_FILE_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일 로그 설정 (상세 정보 포함)
        logger.add(
            Config.LOG_FILE_PATH,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="1 day",      # 매일 자정에 로그 파일 교체
            retention="30 days",   # 30일간 로그 보관
            compression="zip",     # 오래된 로그는 압축
            encoding="utf-8"
        )
        
        # 에러 로그는 별도 파일에 저장
        error_log_path = log_path.parent / "error.log"
        logger.add(
            error_log_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="1 week",
            retention="60 days",
            compression="zip",
            encoding="utf-8"
        )
        
        logger.info("로깅 시스템 초기화 완료")
    
    @staticmethod
    def get_logger():
        """로거 인스턴스 반환"""
        return logger


# 전역 로거 인스턴스
log_instance = Logger()
log = log_instance.get_logger()


# 편의 함수들
def debug(message, **kwargs):
    """디버그 로그"""
    log.debug(message, **kwargs)


def info(message, **kwargs):
    """정보 로그"""
    log.info(message, **kwargs)


def warning(message, **kwargs):
    """경고 로그"""
    log.warning(message, **kwargs)


def error(message, **kwargs):
    """에러 로그"""
    log.error(message, **kwargs)


def critical(message, **kwargs):
    """심각한 에러 로그"""
    log.critical(message, **kwargs)


def success(message, **kwargs):
    """성공 로그"""
    log.success(message, **kwargs)


# 주요 이벤트 로깅 함수들
def log_order(order_type, stock_code, quantity, price, order_number=None):
    """주문 로그"""
    log.info(
        f"📝 주문: {order_type} | 종목: {stock_code} | 수량: {quantity}주 | 가격: {price:,}원"
        + (f" | 주문번호: {order_number}" if order_number else "")
    )


def log_execution(stock_code, quantity, price, order_type):
    """체결 로그"""
    log.success(
        f"✅ 체결: {order_type} | 종목: {stock_code} | 수량: {quantity}주 | 가격: {price:,}원"
    )


def log_signal(stock_code, signal_type, strategy, strength):
    """매매 신호 로그"""
    log.info(
        f"📊 신호: {signal_type} | 종목: {stock_code} | 전략: {strategy} | 강도: {strength}"
    )


def log_position(stock_code, quantity, entry_price, current_price, profit_loss_pct):
    """포지션 로그"""
    profit_symbol = "🟢" if profit_loss_pct >= 0 else "🔴"
    log.info(
        f"{profit_symbol} 보유: {stock_code} | {quantity}주 | "
        f"매입가: {entry_price:,}원 | 현재가: {current_price:,}원 | "
        f"손익률: {profit_loss_pct:+.2f}%"
    )


def log_balance(cash, stock_value, total_value, profit_loss):
    """잔고 로그"""
    log.info(
        f"💰 잔고: 현금 {cash:,}원 | 주식 {stock_value:,}원 | "
        f"총평가: {total_value:,}원 | 손익: {profit_loss:+,}원"
    )


if __name__ == "__main__":
    # 테스트
    info("로거 테스트 시작")
    debug("디버그 메시지")
    warning("경고 메시지")
    error("에러 메시지")
    success("성공 메시지")
    
    log_order("매수", "005930", 10, 75000, "20231016001")
    log_execution("005930", 10, 75000, "매수")
    log_signal("005930", "BUY", "이동평균선", 3)
    log_position("005930", 10, 75000, 76000, 1.33)
    log_balance(10000000, 750000, 10750000, 750000)

