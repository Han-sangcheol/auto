"""
설정 관리 모듈

[파일 역할]
.env 파일에서 환경 변수를 읽어와서 프로그램 전체에서 사용할 설정값을 제공합니다.

[주요 기능]
- .env 파일 로드 및 파싱
- 환경 변수를 Python 변수로 변환
- 설정값 유효성 검사
- 설정 출력 및 확인 기능

[설정 항목]
- 계좌 정보: 계좌번호, 비밀번호
- 거래 설정: 모의투자, 포지션 크기, 손절매/익절매
- 전략 파라미터: 이동평균, RSI, MACD 설정
- 관심 종목 리스트

[사용 방법]
from config import Config
print(Config.KIWOOM_ACCOUNT_NUMBER)
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
    MAX_STOCKS = int(os.getenv('MAX_STOCKS', '3'))  # 최대 동시 보유 종목 수
    POSITION_SIZE_PERCENT = float(os.getenv('POSITION_SIZE_PERCENT', '10'))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '5'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '10'))
    DAILY_LOSS_LIMIT_PERCENT = float(os.getenv('DAILY_LOSS_LIMIT_PERCENT', '3'))
    
    # API 과부하 방지 설정
    API_REQUEST_DELAY = 0.5  # API 호출 최소 간격 (초)
    API_MAX_PER_SECOND = 2   # 초당 최대 API 호출 수
    REAL_DATA_BATCH_SIZE = 50  # 실시간 데이터 등록 배치 크기
    
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
    
    # 급등주 감지 설정
    ENABLE_SURGE_DETECTION = os.getenv('ENABLE_SURGE_DETECTION', 'True').lower() == 'true'
    SURGE_AUTO_APPROVE = os.getenv('SURGE_AUTO_APPROVE', 'True').lower() == 'true'
    SURGE_CANDIDATE_COUNT = int(os.getenv('SURGE_CANDIDATE_COUNT', '100'))
    SURGE_MIN_CHANGE_RATE = float(os.getenv('SURGE_MIN_CHANGE_RATE', '5.0'))
    SURGE_MIN_VOLUME_RATIO = float(os.getenv('SURGE_MIN_VOLUME_RATIO', '2.0'))
    SURGE_COOLDOWN_MINUTES = int(os.getenv('SURGE_COOLDOWN_MINUTES', '30'))
    
    # 뉴스 분석 설정 (선택적 기능)
    ENABLE_NEWS_ANALYSIS = os.getenv('ENABLE_NEWS_ANALYSIS', 'False').lower() == 'true'
    NEWS_UPDATE_INTERVAL = int(os.getenv('NEWS_UPDATE_INTERVAL', '300'))  # 5분
    NEWS_MIN_COUNT = int(os.getenv('NEWS_MIN_COUNT', '3'))  # 최소 뉴스 개수
    NEWS_BUY_THRESHOLD = int(os.getenv('NEWS_BUY_THRESHOLD', '30'))  # 매수 임계값
    NEWS_SELL_THRESHOLD = int(os.getenv('NEWS_SELL_THRESHOLD', '-30'))  # 매도 임계값
    
    # 알림 설정
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'True').lower() == 'true'
    ENABLE_SOUND_ALERTS = os.getenv('ENABLE_SOUND_ALERTS', 'True').lower() == 'true'
    
    # 헬스 모니터 설정
    ENABLE_HEALTH_MONITOR = os.getenv('ENABLE_HEALTH_MONITOR', 'True').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))  # 1분
    ENABLE_AUTO_RECOVERY = os.getenv('ENABLE_AUTO_RECOVERY', 'True').lower() == 'true'
    
    # 스케줄러 설정
    ENABLE_AUTO_SHUTDOWN = os.getenv('ENABLE_AUTO_SHUTDOWN', 'False').lower() == 'true'
    
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
        print(f"\n급등주 감지:")
        print(f"  급등주 감지: {'활성화' if cls.ENABLE_SURGE_DETECTION else '비활성화'}")
        if cls.ENABLE_SURGE_DETECTION:
            print(f"  자동 승인: {'활성화' if cls.SURGE_AUTO_APPROVE else '수동 승인 필요'}")
            print(f"  후보 종목 수: {cls.SURGE_CANDIDATE_COUNT}개")
            print(f"  최소 상승률: {cls.SURGE_MIN_CHANGE_RATE}%")
            print(f"  최소 거래량 비율: {cls.SURGE_MIN_VOLUME_RATIO}배")
            print(f"  재감지 대기시간: {cls.SURGE_COOLDOWN_MINUTES}분")
        print(f"\n뉴스 분석:")
        print(f"  뉴스 분석: {'활성화' if cls.ENABLE_NEWS_ANALYSIS else '비활성화'}")
        if cls.ENABLE_NEWS_ANALYSIS:
            print(f"  갱신 간격: {cls.NEWS_UPDATE_INTERVAL}초")
            print(f"  매수 임계값: {cls.NEWS_BUY_THRESHOLD}")
            print(f"  매도 임계값: {cls.NEWS_SELL_THRESHOLD}")
        print(f"\n알림:")
        print(f"  알림: {'활성화' if cls.ENABLE_NOTIFICATIONS else '비활성화'}")
        print(f"  소리: {'활성화' if cls.ENABLE_SOUND_ALERTS else '비활성화'}")
        print(f"\n헬스 모니터:")
        print(f"  헬스 모니터: {'활성화' if cls.ENABLE_HEALTH_MONITOR else '비활성화'}")
        if cls.ENABLE_HEALTH_MONITOR:
            print(f"  체크 간격: {cls.HEALTH_CHECK_INTERVAL}초")
            print(f"  자동 복구: {'활성화' if cls.ENABLE_AUTO_RECOVERY else '비활성화'}")
        
        print("\n📅 스케줄러 설정:")
        print(f"  자동 종료: {'활성화 (16:00)' if cls.ENABLE_AUTO_SHUTDOWN else '비활성화'}")
        
        print("=" * 60)


# 설정값 유효성 검사 (모듈 로드 시)
if __name__ != '__main__':
    validation_errors = Config.validate()
    if validation_errors:
        print("⚠️  설정 오류:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\n.env 파일을 확인하고 올바르게 설정해주세요.")

