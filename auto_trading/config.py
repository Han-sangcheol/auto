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
    """프로그램 설정 클래스 (동적 재로드 지원)"""
    
    # 🆕 설정 변경 콜백 리스트
    _reload_callbacks = []
    
    # 키움증권 계좌 정보
    KIWOOM_ACCOUNT_NUMBER = os.getenv('KIWOOM_ACCOUNT_NUMBER', '')
    KIWOOM_ACCOUNT_PASSWORD = os.getenv('KIWOOM_ACCOUNT_PASSWORD', '')
    
    # 거래 설정
    USE_SIMULATION = os.getenv('USE_SIMULATION', 'True').lower() == 'true'
    MAX_STOCKS = int(os.getenv('MAX_STOCKS', '3'))  # 최대 동시 보유 종목 수
    AUTO_TRADING_RATIO = float(os.getenv('AUTO_TRADING_RATIO', '80'))  # 전체 잔고 중 자동매매 사용 비율 (%)
    POSITION_SIZE_PERCENT = float(os.getenv('POSITION_SIZE_PERCENT', '10'))  # 자동매매 잔고 중 종목당 비율 (%)
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '5'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '10'))
    DAILY_LOSS_LIMIT_PERCENT = float(os.getenv('DAILY_LOSS_LIMIT_PERCENT', '3'))
    
    # 🆕 시장 시간 설정
    ENABLE_AFTER_HOURS_TRADING = os.getenv('ENABLE_AFTER_HOURS_TRADING', 'False').lower() == 'true'  # 시간외 거래 활성화
    DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'False').lower() == 'true'  # 개발 모드 (시간 제약 없음)
    
    # 추가 매수 설정 (물타기)
    ENABLE_AVERAGE_DOWN = os.getenv('ENABLE_AVERAGE_DOWN', 'False').lower() == 'true'  # 추가 매수 활성화
    AVERAGE_DOWN_TRIGGER_PERCENT = float(os.getenv('AVERAGE_DOWN_TRIGGER_PERCENT', '2.5'))  # 추가 매수 트리거 비율 (손실 %)
    MAX_AVERAGE_DOWN_COUNT = int(os.getenv('MAX_AVERAGE_DOWN_COUNT', '2'))  # 최대 추가 매수 횟수
    AVERAGE_DOWN_SIZE_RATIO = float(os.getenv('AVERAGE_DOWN_SIZE_RATIO', '1.0'))  # 추가 매수 수량 비율
    
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
    
    # 급등주 감지 설정 (⚡ 과부하 방지 최적화 + 호가 분석 + 연속조회)
    ENABLE_SURGE_DETECTION = os.getenv('ENABLE_SURGE_DETECTION', 'True').lower() == 'true'
    SURGE_AUTO_APPROVE = os.getenv('SURGE_AUTO_APPROVE', 'True').lower() == 'true'
    SURGE_CANDIDATE_COUNT = int(os.getenv('SURGE_CANDIDATE_COUNT', '30'))  # 100→30 (과부하 방지)
    SURGE_USE_CONTINUOUS = os.getenv('SURGE_USE_CONTINUOUS', 'True').lower() == 'true'  # 🆕 연속조회 사용
    SURGE_MAX_CONTINUOUS = int(os.getenv('SURGE_MAX_CONTINUOUS', '3'))  # 🆕 최대 연속조회 횟수 (1-5)
    SURGE_MIN_CHANGE_RATE = float(os.getenv('SURGE_MIN_CHANGE_RATE', '5.0'))  # 10.0→5.0 (조건 완화)
    SURGE_MONITORING_CHANGE_RATE = float(os.getenv('SURGE_MONITORING_CHANGE_RATE', '5.0'))  # 🆕 모니터링 시작 이후 추가 상승률 (%)
    SURGE_MIN_VOLUME_RATIO = float(os.getenv('SURGE_MIN_VOLUME_RATIO', '2.0'))  # 3.0→2.0 (조건 완화)
    SURGE_MIN_BUYING_PRESSURE = float(os.getenv('SURGE_MIN_BUYING_PRESSURE', '0.0'))  # 60→0 (호가 조건 비활성화)
    SURGE_COOLDOWN_MINUTES = int(os.getenv('SURGE_COOLDOWN_MINUTES', '30'))
    
    # 뉴스 분석 설정 (🆕 기본 비활성화 - 성능 최적화)
    ENABLE_NEWS_ANALYSIS = os.getenv('ENABLE_NEWS_ANALYSIS', 'False').lower() == 'true'
    NEWS_UPDATE_INTERVAL = int(os.getenv('NEWS_UPDATE_INTERVAL', '300'))  # 5분
    NEWS_MIN_COUNT = int(os.getenv('NEWS_MIN_COUNT', '1'))  # 최소 뉴스 개수 (1개 이상이면 분석)
    NEWS_BUY_THRESHOLD = int(os.getenv('NEWS_BUY_THRESHOLD', '30'))  # 매수 임계값
    NEWS_SELL_THRESHOLD = int(os.getenv('NEWS_SELL_THRESHOLD', '-30'))  # 매도 임계값
    
    # 🆕 뉴스 기반 매수/매도 기준 조정 설정
    NEWS_POSITIVE_SURGE_ADJUST = float(os.getenv('NEWS_POSITIVE_SURGE_ADJUST', '50'))  # 호재 시 급등 기준 완화 (%)
    NEWS_NEGATIVE_STOPLOSS_ADJUST = float(os.getenv('NEWS_NEGATIVE_STOPLOSS_ADJUST', '50'))  # 악재 시 손절 기준 강화 (%)
    
    # 알림 설정
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'True').lower() == 'true'
    ENABLE_SOUND_ALERTS = os.getenv('ENABLE_SOUND_ALERTS', 'True').lower() == 'true'
    
    # 헬스 모니터 설정
    ENABLE_HEALTH_MONITOR = os.getenv('ENABLE_HEALTH_MONITOR', 'True').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))  # 1분
    ENABLE_AUTO_RECOVERY = os.getenv('ENABLE_AUTO_RECOVERY', 'True').lower() == 'true'
    
    # 스케줄러 설정
    ENABLE_AUTO_SHUTDOWN = os.getenv('ENABLE_AUTO_SHUTDOWN', 'False').lower() == 'true'
    
    # 시장 운영 시간 설정
    MARKET_PRE_OPEN_TIME = os.getenv('MARKET_PRE_OPEN_TIME', '08:30')  # 장 시작 전 (동시호가)
    MARKET_OPEN_TIME = os.getenv('MARKET_OPEN_TIME', '09:00')  # 정규장 시작
    MARKET_CLOSE_TIME = os.getenv('MARKET_CLOSE_TIME', '15:30')  # 정규장 마감
    MARKET_AFTER_HOURS_START = os.getenv('MARKET_AFTER_HOURS_START', '15:40')  # 시간외 시작 (단일가)
    MARKET_AFTER_HOURS_END = os.getenv('MARKET_AFTER_HOURS_END', '18:00')  # 시간외 종료 (종가거래 포함)
    
    # 자동 시작/종료 설정
    AUTO_START_ENABLED = os.getenv('AUTO_START_ENABLED', 'False').lower() == 'true'  # 장 시작 시 자동 시작
    AUTO_START_TIME = os.getenv('AUTO_START_TIME', '08:50')  # 자동 시작 시간 (장 시작 10분 전)
    AUTO_STOP_TIME = os.getenv('AUTO_STOP_TIME', '18:05')  # 자동 종료 시간 (시간외 거래 종료 후)
    
    # 시간외 매매 설정
    ENABLE_AFTER_HOURS_TRADING = os.getenv('ENABLE_AFTER_HOURS_TRADING', 'False').lower() == 'true'
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/trading.log')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')  # 로그 및 데이터베이스 저장 디렉토리
    
    # 데이터베이스 설정 (SQLite: 32/64비트 모두 지원)
    # ⚡ 기본값 False: 실시간 성능 우선 (필요 시 .env에서 활성화)
    DB_ENABLED = os.getenv('DB_ENABLED', 'False').lower() == 'true'
    DB_PATH = os.getenv('DB_PATH', 'data/stocks.db')
    DB_PARQUET_DIR = os.getenv('DB_PARQUET_DIR', 'data/csv')  # CSV 파일 저장
    DB_CANDLE_INTERVAL = int(os.getenv('DB_CANDLE_INTERVAL', '1'))  # 분
    DB_RETENTION_DAYS = int(os.getenv('DB_RETENTION_DAYS', '0'))  # 0=무제한
    DB_AUTO_BACKUP = os.getenv('DB_AUTO_BACKUP', 'True').lower() == 'true'
    DB_BACKUP_INTERVAL_DAYS = int(os.getenv('DB_BACKUP_INTERVAL_DAYS', '7'))
    
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
        
        if cls.AUTO_TRADING_RATIO <= 0 or cls.AUTO_TRADING_RATIO > 100:
            errors.append("AUTO_TRADING_RATIO는 0과 100 사이여야 합니다.")
        
        if cls.POSITION_SIZE_PERCENT <= 0 or cls.POSITION_SIZE_PERCENT > 100:
            errors.append("POSITION_SIZE_PERCENT는 0과 100 사이여야 합니다.")
        
        if cls.STOP_LOSS_PERCENT <= 0 or cls.STOP_LOSS_PERCENT >= 100:
            errors.append("STOP_LOSS_PERCENT는 0과 100 사이여야 합니다.")
        
        if cls.TAKE_PROFIT_PERCENT <= 0:
            errors.append("TAKE_PROFIT_PERCENT는 0보다 커야 합니다.")
        
        if cls.MIN_SIGNAL_STRENGTH < 1 or cls.MIN_SIGNAL_STRENGTH > 3:
            errors.append("MIN_SIGNAL_STRENGTH는 1과 3 사이여야 합니다.")
        
        # 추가 매수 검증
        if cls.ENABLE_AVERAGE_DOWN:
            if cls.AVERAGE_DOWN_TRIGGER_PERCENT <= 0 or cls.AVERAGE_DOWN_TRIGGER_PERCENT >= cls.STOP_LOSS_PERCENT:
                errors.append(f"AVERAGE_DOWN_TRIGGER_PERCENT({cls.AVERAGE_DOWN_TRIGGER_PERCENT}%)는 0보다 크고 STOP_LOSS_PERCENT({cls.STOP_LOSS_PERCENT}%)보다 작아야 합니다.")
            
            if cls.MAX_AVERAGE_DOWN_COUNT < 1 or cls.MAX_AVERAGE_DOWN_COUNT > 5:
                errors.append("MAX_AVERAGE_DOWN_COUNT는 1과 5 사이여야 합니다.")
            
            if cls.AVERAGE_DOWN_SIZE_RATIO <= 0 or cls.AVERAGE_DOWN_SIZE_RATIO > 5:
                errors.append("AVERAGE_DOWN_SIZE_RATIO는 0보다 크고 5 이하여야 합니다.")
        
        return errors
    
    @classmethod
    def register_reload_callback(cls, callback):
        """
        🆕 설정 재로드 콜백 등록
        
        Args:
            callback: 설정 변경 시 호출할 함수
        """
        if callback not in cls._reload_callbacks:
            cls._reload_callbacks.append(callback)
    
    @classmethod
    def reload_from_env(cls):
        """
        🆕 환경변수에서 설정 다시 로드
        """
        from dotenv import load_dotenv
        from pathlib import Path
        
        # .env 파일 다시 로드
        env_path = Path(__file__).parent / '.env'
        load_dotenv(dotenv_path=env_path, override=True)  # override=True로 기존 값 덮어쓰기
        
        # 모든 설정 값 다시 로드
        cls.KIWOOM_ACCOUNT_NUMBER = os.getenv('KIWOOM_ACCOUNT_NUMBER', '')
        cls.KIWOOM_ACCOUNT_PASSWORD = os.getenv('KIWOOM_ACCOUNT_PASSWORD', '')
        
        # 거래 설정
        cls.USE_SIMULATION = os.getenv('USE_SIMULATION', 'True').lower() == 'true'
        cls.MAX_STOCKS = int(os.getenv('MAX_STOCKS', '3'))
        cls.AUTO_TRADING_RATIO = float(os.getenv('AUTO_TRADING_RATIO', '80'))
        cls.POSITION_SIZE_PERCENT = float(os.getenv('POSITION_SIZE_PERCENT', '10'))
        cls.STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '5'))
        cls.TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '10'))
        cls.DAILY_LOSS_LIMIT_PERCENT = float(os.getenv('DAILY_LOSS_LIMIT_PERCENT', '3'))
        
        # 시장 시간 설정
        cls.ENABLE_AFTER_HOURS_TRADING = os.getenv('ENABLE_AFTER_HOURS_TRADING', 'False').lower() == 'true'
        cls.DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'False').lower() == 'true'
        
        # 물타기 설정
        cls.ENABLE_AVERAGE_DOWN = os.getenv('ENABLE_AVERAGE_DOWN', 'False').lower() == 'true'
        cls.AVERAGE_DOWN_TRIGGER_PERCENT = float(os.getenv('AVERAGE_DOWN_TRIGGER_PERCENT', '2.5'))
        cls.MAX_AVERAGE_DOWN_COUNT = int(os.getenv('MAX_AVERAGE_DOWN_COUNT', '2'))
        cls.AVERAGE_DOWN_SIZE_RATIO = float(os.getenv('AVERAGE_DOWN_SIZE_RATIO', '1.0'))
        
        # 관심 종목
        cls.WATCH_LIST_STR = os.getenv('WATCH_LIST', '005930,000660,035720')
        cls.WATCH_LIST = [code.strip() for code in cls.WATCH_LIST_STR.split(',') if code.strip()]
        
        # 전략 설정
        cls.MA_SHORT_PERIOD = int(os.getenv('MA_SHORT_PERIOD', '5'))
        cls.MA_LONG_PERIOD = int(os.getenv('MA_LONG_PERIOD', '20'))
        cls.RSI_PERIOD = int(os.getenv('RSI_PERIOD', '14'))
        cls.RSI_OVERSOLD = float(os.getenv('RSI_OVERSOLD', '30'))
        cls.RSI_OVERBOUGHT = float(os.getenv('RSI_OVERBOUGHT', '70'))
        cls.MACD_FAST = int(os.getenv('MACD_FAST', '12'))
        cls.MACD_SLOW = int(os.getenv('MACD_SLOW', '26'))
        cls.MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', '9'))
        cls.MIN_SIGNAL_STRENGTH = int(os.getenv('MIN_SIGNAL_STRENGTH', '2'))
        
        # 급등주 설정
        cls.ENABLE_SURGE_DETECTION = os.getenv('ENABLE_SURGE_DETECTION', 'True').lower() == 'true'
        cls.SURGE_AUTO_APPROVE = os.getenv('SURGE_AUTO_APPROVE', 'True').lower() == 'true'
        cls.SURGE_CANDIDATE_COUNT = int(os.getenv('SURGE_CANDIDATE_COUNT', '30'))
        cls.SURGE_USE_CONTINUOUS = os.getenv('SURGE_USE_CONTINUOUS', 'True').lower() == 'true'
        cls.SURGE_MAX_CONTINUOUS = int(os.getenv('SURGE_MAX_CONTINUOUS', '3'))
        cls.SURGE_MIN_CHANGE_RATE = float(os.getenv('SURGE_MIN_CHANGE_RATE', '5.0'))
        cls.SURGE_MONITORING_CHANGE_RATE = float(os.getenv('SURGE_MONITORING_CHANGE_RATE', '5.0'))
        cls.SURGE_MIN_VOLUME_RATIO = float(os.getenv('SURGE_MIN_VOLUME_RATIO', '2.0'))
        cls.SURGE_MIN_BUYING_PRESSURE = float(os.getenv('SURGE_MIN_BUYING_PRESSURE', '0.0'))
        cls.SURGE_COOLDOWN_MINUTES = int(os.getenv('SURGE_COOLDOWN_MINUTES', '30'))
        
        # 뉴스 설정
        cls.ENABLE_NEWS_ANALYSIS = os.getenv('ENABLE_NEWS_ANALYSIS', 'False').lower() == 'true'
        cls.NEWS_UPDATE_INTERVAL = int(os.getenv('NEWS_UPDATE_INTERVAL', '300'))
        cls.NEWS_MIN_COUNT = int(os.getenv('NEWS_MIN_COUNT', '1'))
        cls.NEWS_BUY_THRESHOLD = int(os.getenv('NEWS_BUY_THRESHOLD', '30'))
        cls.NEWS_SELL_THRESHOLD = int(os.getenv('NEWS_SELL_THRESHOLD', '-30'))
        cls.NEWS_POSITIVE_SURGE_ADJUST = float(os.getenv('NEWS_POSITIVE_SURGE_ADJUST', '50'))
        cls.NEWS_NEGATIVE_STOPLOSS_ADJUST = float(os.getenv('NEWS_NEGATIVE_STOPLOSS_ADJUST', '50'))
        
        # 알림 설정
        cls.ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'True').lower() == 'true'
        cls.ENABLE_SOUND_ALERTS = os.getenv('ENABLE_SOUND_ALERTS', 'True').lower() == 'true'
        
        # 헬스 모니터
        cls.ENABLE_HEALTH_MONITOR = os.getenv('ENABLE_HEALTH_MONITOR', 'True').lower() == 'true'
        cls.HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))
        cls.ENABLE_AUTO_RECOVERY = os.getenv('ENABLE_AUTO_RECOVERY', 'True').lower() == 'true'
        
        # 스케줄러
        cls.ENABLE_AUTO_SHUTDOWN = os.getenv('ENABLE_AUTO_SHUTDOWN', 'False').lower() == 'true'
        
        # 시장 시간
        cls.MARKET_PRE_OPEN_TIME = os.getenv('MARKET_PRE_OPEN_TIME', '08:30')
        cls.MARKET_OPEN_TIME = os.getenv('MARKET_OPEN_TIME', '09:00')
        cls.MARKET_CLOSE_TIME = os.getenv('MARKET_CLOSE_TIME', '15:30')
        cls.MARKET_AFTER_HOURS_START = os.getenv('MARKET_AFTER_HOURS_START', '15:40')
        cls.MARKET_AFTER_HOURS_END = os.getenv('MARKET_AFTER_HOURS_END', '18:00')
        cls.AUTO_START_ENABLED = os.getenv('AUTO_START_ENABLED', 'False').lower() == 'true'
        cls.AUTO_START_TIME = os.getenv('AUTO_START_TIME', '08:50')
        cls.AUTO_STOP_TIME = os.getenv('AUTO_STOP_TIME', '18:05')
        
        # DB 설정
        cls.DB_ENABLED = os.getenv('DB_ENABLED', 'False').lower() == 'true'
        cls.DB_PATH = os.getenv('DB_PATH', 'trading_data.db')
        cls.DB_CANDLE_INTERVAL = int(os.getenv('DB_CANDLE_INTERVAL', '1'))
        cls.DB_RETENTION_DAYS = int(os.getenv('DB_RETENTION_DAYS', '90'))
        cls.DB_AUTO_BACKUP = os.getenv('DB_AUTO_BACKUP', 'True').lower() == 'true'
        cls.DB_BACKUP_INTERVAL_DAYS = int(os.getenv('DB_BACKUP_INTERVAL_DAYS', '7'))
        cls.DB_PARQUET_DIR = os.getenv('DB_PARQUET_DIR', 'db_exports')
        
        cls.LOG_DIR = os.getenv('LOG_DIR', 'logs')
        
        # 검증
        validation_errors = cls.validate()
        if validation_errors:
            from logger import log
            log.warning("⚠️  설정 재로드 후 검증 오류:")
            for error in validation_errors:
                log.warning(f"  - {error}")
        else:
            from logger import log
            log.success("✅ 설정 재로드 완료 - 검증 통과")
        
        # 등록된 콜백 호출
        for callback in cls._reload_callbacks:
            try:
                callback()
            except Exception as e:
                from logger import log
                log.error(f"설정 재로드 콜백 실행 오류: {e}")
    
    @classmethod
    def print_config(cls):
        """현재 설정값 출력"""
        print("=" * 60)
        print("현재 설정값")
        print("=" * 60)
        print(f"계좌번호: {cls.KIWOOM_ACCOUNT_NUMBER}")
        print(f"모의투자 사용: {cls.USE_SIMULATION}")
        print(f"🆕 개발 모드: {'활성화 (시간 제약 없음)' if cls.DEVELOPMENT_MODE else '비활성화'}")
        print(f"🆕 시간외 거래: {'활성화' if cls.ENABLE_AFTER_HOURS_TRADING else '비활성화'}")
        print(f"최대 보유 종목 수: {cls.MAX_STOCKS}")
        print(f"자동매매 투자 비율: {cls.AUTO_TRADING_RATIO}% (잔고 중 자동매매 사용 비율)")
        print(f"종목당 투자 비율: {cls.POSITION_SIZE_PERCENT}% (자동매매 잔고 중 종목당 비율)")
        print(f"손절매 비율: {cls.STOP_LOSS_PERCENT}%")
        print(f"익절매 비율: {cls.TAKE_PROFIT_PERCENT}%")
        print(f"일일 손실 한도: {cls.DAILY_LOSS_LIMIT_PERCENT}%")
        print(f"\n추가 매수 (물타기):")
        print(f"  활성화: {'예' if cls.ENABLE_AVERAGE_DOWN else '아니오'}")
        if cls.ENABLE_AVERAGE_DOWN:
            print(f"  트리거 비율: {cls.AVERAGE_DOWN_TRIGGER_PERCENT}% (손실)")
            print(f"  최대 횟수: {cls.MAX_AVERAGE_DOWN_COUNT}회")
            print(f"  수량 비율: {cls.AVERAGE_DOWN_SIZE_RATIO}배")
        print(f"\n관심 종목: {', '.join(cls.WATCH_LIST)}")
        print(f"\n전략 설정:")
        print(f"  이동평균선: 단기 {cls.MA_SHORT_PERIOD}일, 장기 {cls.MA_LONG_PERIOD}일")
        print(f"  RSI: 기간 {cls.RSI_PERIOD}일, 과매도 {cls.RSI_OVERSOLD}, 과매수 {cls.RSI_OVERBOUGHT}")
        print(f"  MACD: 빠른선 {cls.MACD_FAST}, 느린선 {cls.MACD_SLOW}, 시그널 {cls.MACD_SIGNAL}")
        print(f"  최소 신호 강도: {cls.MIN_SIGNAL_STRENGTH}/3")
        print(f"\n급등주 감지 (🆕 연속조회 + 호가 분석):")
        print(f"  급등주 감지: {'활성화' if cls.ENABLE_SURGE_DETECTION else '비활성화'}")
        if cls.ENABLE_SURGE_DETECTION:
            print(f"  자동 승인: {'활성화' if cls.SURGE_AUTO_APPROVE else '수동 승인 필요'}")
            print(f"  후보 종목 수: {cls.SURGE_CANDIDATE_COUNT}개")
            print(f"  🆕 연속조회: {'사용' if cls.SURGE_USE_CONTINUOUS else '미사용'} (최대 {cls.SURGE_MAX_CONTINUOUS}회)")
            print(f"  최소 상승률 (전일 대비): {cls.SURGE_MIN_CHANGE_RATE}%")
            print(f"  🆕 최소 추가 상승률 (모니터링 시작 이후): {cls.SURGE_MONITORING_CHANGE_RATE}%")
            print(f"  최소 거래량 비율: {cls.SURGE_MIN_VOLUME_RATIO}배")
            print(f"  🆕 매수 압력 점수: {cls.SURGE_MIN_BUYING_PRESSURE}점 (0~100)")
            print(f"  재감지 대기시간: {cls.SURGE_COOLDOWN_MINUTES}분")
        print(f"\n뉴스 분석:")
        print(f"  뉴스 분석: {'활성화' if cls.ENABLE_NEWS_ANALYSIS else '비활성화'}")
        if cls.ENABLE_NEWS_ANALYSIS:
            print(f"  갱신 간격: {cls.NEWS_UPDATE_INTERVAL}초")
            print(f"  매수 임계값: {cls.NEWS_BUY_THRESHOLD}")
            print(f"  매도 임계값: {cls.NEWS_SELL_THRESHOLD}")
            print(f"  🆕 호재 시 급등 기준 완화: {cls.NEWS_POSITIVE_SURGE_ADJUST}%")
            print(f"  🆕 악재 시 손절 기준 강화: {cls.NEWS_NEGATIVE_STOPLOSS_ADJUST}%")
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
        
        print("\n🕐 시장 운영 시간:")
        print(f"  장 시작 전: {cls.MARKET_PRE_OPEN_TIME}")
        print(f"  정규장: {cls.MARKET_OPEN_TIME} ~ {cls.MARKET_CLOSE_TIME}")
        print(f"  시간외: {cls.MARKET_AFTER_HOURS_START} ~ {cls.MARKET_AFTER_HOURS_END}")
        print(f"  자동 시작: {'활성화' if cls.AUTO_START_ENABLED else '비활성화'} ({cls.AUTO_START_TIME})")
        print(f"  자동 종료: {cls.AUTO_STOP_TIME}")
        print(f"  시간외 매매: {'활성화' if cls.ENABLE_AFTER_HOURS_TRADING else '비활성화'}")
        
        print("\n💾 데이터베이스 (SQLite):")
        print(f"  DB 저장: {'활성화' if cls.DB_ENABLED else '비활성화'}")
        if cls.DB_ENABLED:
            print(f"  DB 경로: {cls.DB_PATH}")
            print(f"  CSV 경로: {cls.DB_PARQUET_DIR}")
            print(f"  1분봉 간격: {cls.DB_CANDLE_INTERVAL}분")
            print(f"  보관 기간: {'무제한' if cls.DB_RETENTION_DAYS == 0 else f'{cls.DB_RETENTION_DAYS}일'}")
            print(f"  자동 백업: {'활성화' if cls.DB_AUTO_BACKUP else '비활성화'}")
            if cls.DB_AUTO_BACKUP:
                print(f"  백업 간격: {cls.DB_BACKUP_INTERVAL_DAYS}일")
        
        print("=" * 60)


# 설정값 유효성 검사 (모듈 로드 시)
if __name__ != '__main__':
    validation_errors = Config.validate()
    if validation_errors:
        print("⚠️  설정 오류:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\n.env 파일을 확인하고 올바르게 설정해주세요.")

