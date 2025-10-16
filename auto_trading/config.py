"""
설정 관리 모듈
.env 파일에서 환경 변수를 읽어와서 설정값을 제공합니다.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """프로그램 설정 클래스"""
    
    # 키움증권 계좌 정보
    KIWOOM_ACCOUNT_NUMBER = os.getenv('KIWOOM_ACCOUNT_NUMBER', '')
    KIWOOM_ACCOUNT_PASSWORD = os.getenv('KIWOOM_ACCOUNT_PASSWORD', '')
    
    # 거래 설정
    USE_SIMULATION = os.getenv('USE_SIMULATION', 'True').lower() == 'true'
    MAX_STOCKS = int(os.getenv('MAX_STOCKS', '3'))
    POSITION_SIZE_PERCENT = float(os.getenv('POSITION_SIZE_PERCENT', '10'))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '5'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '10'))
    DAILY_LOSS_LIMIT_PERCENT = float(os.getenv('DAILY_LOSS_LIMIT_PERCENT', '3'))
    
    # 관심 종목 리스트
    WATCH_LIST_STR = os.getenv('WATCH_LIST', '005930,000660,035720')
    WATCH_LIST = [code.strip() for code in WATCH_LIST_STR.split(',') if code.strip()]
    
    # 전략 설정 - 이동평균선
    MA_SHORT_PERIOD = int(os.getenv('MA_SHORT_PERIOD', '5'))
    MA_LONG_PERIOD = int(os.getenv('MA_LONG_PERIOD', '20'))
    
    # 전략 설정 - RSI
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', '14'))
    RSI_OVERSOLD = float(os.getenv('RSI_OVERSOLD', '30'))
    RSI_OVERBOUGHT = float(os.getenv('RSI_OVERBOUGHT', '70'))
    
    # 전략 설정 - MACD
    MACD_FAST = int(os.getenv('MACD_FAST', '12'))
    MACD_SLOW = int(os.getenv('MACD_SLOW', '26'))
    MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', '9'))
    
    # 통합 전략 설정
    MIN_SIGNAL_STRENGTH = int(os.getenv('MIN_SIGNAL_STRENGTH', '2'))
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/trading.log')
    
    @classmethod
    def validate(cls):
        """설정값 유효성 검사"""
        errors = []
        
        if not cls.KIWOOM_ACCOUNT_NUMBER:
            errors.append("KIWOOM_ACCOUNT_NUMBER가 설정되지 않았습니다.")
        
        if not cls.KIWOOM_ACCOUNT_PASSWORD:
            errors.append("KIWOOM_ACCOUNT_PASSWORD가 설정되지 않았습니다.")
        
        if not cls.WATCH_LIST:
            errors.append("WATCH_LIST가 비어있습니다. 최소 1개 이상의 종목을 설정하세요.")
        
        if cls.MAX_STOCKS < 1:
            errors.append("MAX_STOCKS는 1 이상이어야 합니다.")
        
        if cls.POSITION_SIZE_PERCENT <= 0 or cls.POSITION_SIZE_PERCENT > 100:
            errors.append("POSITION_SIZE_PERCENT는 0과 100 사이여야 합니다.")
        
        if cls.STOP_LOSS_PERCENT <= 0 or cls.STOP_LOSS_PERCENT >= 100:
            errors.append("STOP_LOSS_PERCENT는 0과 100 사이여야 합니다.")
        
        if cls.TAKE_PROFIT_PERCENT <= 0:
            errors.append("TAKE_PROFIT_PERCENT는 0보다 커야 합니다.")
        
        if cls.MIN_SIGNAL_STRENGTH < 1 or cls.MIN_SIGNAL_STRENGTH > 3:
            errors.append("MIN_SIGNAL_STRENGTH는 1과 3 사이여야 합니다.")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """현재 설정값 출력"""
        print("=" * 60)
        print("현재 설정값")
        print("=" * 60)
        print(f"계좌번호: {cls.KIWOOM_ACCOUNT_NUMBER[:4]}****{cls.KIWOOM_ACCOUNT_NUMBER[-2:]}")
        print(f"모의투자 사용: {cls.USE_SIMULATION}")
        print(f"최대 보유 종목 수: {cls.MAX_STOCKS}")
        print(f"종목당 투자 비율: {cls.POSITION_SIZE_PERCENT}%")
        print(f"손절매 비율: {cls.STOP_LOSS_PERCENT}%")
        print(f"익절매 비율: {cls.TAKE_PROFIT_PERCENT}%")
        print(f"일일 손실 한도: {cls.DAILY_LOSS_LIMIT_PERCENT}%")
        print(f"관심 종목: {', '.join(cls.WATCH_LIST)}")
        print(f"\n전략 설정:")
        print(f"  이동평균선: 단기 {cls.MA_SHORT_PERIOD}일, 장기 {cls.MA_LONG_PERIOD}일")
        print(f"  RSI: 기간 {cls.RSI_PERIOD}일, 과매도 {cls.RSI_OVERSOLD}, 과매수 {cls.RSI_OVERBOUGHT}")
        print(f"  MACD: 빠른선 {cls.MACD_FAST}, 느린선 {cls.MACD_SLOW}, 시그널 {cls.MACD_SIGNAL}")
        print(f"  최소 신호 강도: {cls.MIN_SIGNAL_STRENGTH}/3")
        print("=" * 60)


# 설정값 유효성 검사 (모듈 로드 시)
if __name__ != '__main__':
    validation_errors = Config.validate()
    if validation_errors:
        print("⚠️  설정 오류:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\n.env 파일을 확인하고 올바르게 설정해주세요.")

