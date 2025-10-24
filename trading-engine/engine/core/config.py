"""
Trading Engine 설정 관리

[파일 역할]
환경 변수 및 설정값을 중앙에서 관리합니다.

[주요 기능]
- 환경 변수 로드
- 설정 검증
- 기본값 제공
"""

import os
from typing import Optional
from dotenv import load_dotenv


# .env 파일 로드
load_dotenv()


class Config:
    """Trading Engine 설정"""
    
    # ==========================================
    # Backend API 연결
    # ==========================================
    BACKEND_URL: str = os.getenv('BACKEND_URL', 'http://localhost:8000')
    
    # ==========================================
    # 키움 계좌 설정
    # ==========================================
    KIWOOM_ACCOUNT_NUMBER: str = os.getenv('KIWOOM_ACCOUNT_NUMBER', '')
    KIWOOM_ACCOUNT_PASSWORD: str = os.getenv('KIWOOM_ACCOUNT_PASSWORD', '')
    USE_SIMULATION: bool = os.getenv('USE_SIMULATION', 'True').lower() == 'true'
    
    # ==========================================
    # Redis 설정
    # ==========================================
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    USE_REDIS_EVENTS: bool = os.getenv('USE_REDIS_EVENTS', 'False').lower() == 'true'
    
    # ==========================================
    # 리스크 관리 설정
    # ==========================================
    MAX_STOCKS: int = int(os.getenv('MAX_STOCKS', '3'))
    POSITION_SIZE_PERCENT: float = float(os.getenv('POSITION_SIZE_PERCENT', '10.0'))
    STOP_LOSS_PERCENT: float = float(os.getenv('STOP_LOSS_PERCENT', '5.0'))
    TAKE_PROFIT_PERCENT: float = float(os.getenv('TAKE_PROFIT_PERCENT', '10.0'))
    DAILY_LOSS_LIMIT_PERCENT: float = float(os.getenv('DAILY_LOSS_LIMIT_PERCENT', '3.0'))
    
    # ==========================================
    # 전략 설정
    # ==========================================
    # 이동평균선
    MA_SHORT_PERIOD: int = int(os.getenv('MA_SHORT_PERIOD', '5'))
    MA_LONG_PERIOD: int = int(os.getenv('MA_LONG_PERIOD', '20'))
    
    # RSI
    RSI_PERIOD: int = int(os.getenv('RSI_PERIOD', '14'))
    RSI_OVERSOLD: float = float(os.getenv('RSI_OVERSOLD', '30.0'))
    RSI_OVERBOUGHT: float = float(os.getenv('RSI_OVERBOUGHT', '70.0'))
    
    # MACD
    MACD_FAST: int = int(os.getenv('MACD_FAST', '12'))
    MACD_SLOW: int = int(os.getenv('MACD_SLOW', '26'))
    MACD_SIGNAL: int = int(os.getenv('MACD_SIGNAL', '9'))
    
    # 통합 전략
    MIN_SIGNAL_STRENGTH: int = int(os.getenv('MIN_SIGNAL_STRENGTH', '2'))
    
    # ==========================================
    # 급등주 감지 설정
    # ==========================================
    ENABLE_SURGE_DETECTION: bool = os.getenv('ENABLE_SURGE_DETECTION', 'True').lower() == 'true'
    SURGE_AUTO_APPROVE: bool = os.getenv('SURGE_AUTO_APPROVE', 'False').lower() == 'true'
    SURGE_CANDIDATE_COUNT: int = int(os.getenv('SURGE_CANDIDATE_COUNT', '100'))
    SURGE_MIN_CHANGE_RATE: float = float(os.getenv('SURGE_MIN_CHANGE_RATE', '5.0'))
    SURGE_MIN_VOLUME_RATIO: float = float(os.getenv('SURGE_MIN_VOLUME_RATIO', '2.0'))
    SURGE_COOLDOWN_MINUTES: int = int(os.getenv('SURGE_COOLDOWN_MINUTES', '30'))
    
    # ==========================================
    # 로깅 설정
    # ==========================================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/trading_engine.log')
    
    @classmethod
    def validate(cls) -> bool:
        """설정 검증"""
        errors = []
        
        # 필수 설정 확인 (실계좌 사용 시)
        if not cls.USE_SIMULATION:
            if not cls.KIWOOM_ACCOUNT_NUMBER:
                errors.append("KIWOOM_ACCOUNT_NUMBER가 설정되지 않았습니다.")
            if not cls.KIWOOM_ACCOUNT_PASSWORD:
                errors.append("KIWOOM_ACCOUNT_PASSWORD가 설정되지 않았습니다.")
        
        # 범위 검증
        if cls.MAX_STOCKS < 1 or cls.MAX_STOCKS > 10:
            errors.append("MAX_STOCKS는 1~10 사이여야 합니다.")
        
        if cls.POSITION_SIZE_PERCENT <= 0 or cls.POSITION_SIZE_PERCENT > 100:
            errors.append("POSITION_SIZE_PERCENT는 0~100 사이여야 합니다.")
        
        if cls.STOP_LOSS_PERCENT < 0 or cls.STOP_LOSS_PERCENT > 50:
            errors.append("STOP_LOSS_PERCENT는 0~50 사이여야 합니다.")
        
        if errors:
            for error in errors:
                print(f"❌ 설정 오류: {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """설정 정보 출력"""
        print("\n" + "=" * 60)
        print("Trading Engine 설정")
        print("=" * 60)
        
        print(f"\n🔌 Backend API:")
        print(f"  URL: {cls.BACKEND_URL}")
        
        print(f"\n🏦 키움 계좌:")
        print(f"  모드: {'모의투자' if cls.USE_SIMULATION else '실계좌'}")
        if cls.USE_SIMULATION:
            print(f"  계좌번호: (모의투자 - 자동 선택)")
        else:
            masked = cls.KIWOOM_ACCOUNT_NUMBER[:4] + "****" if cls.KIWOOM_ACCOUNT_NUMBER else "(미설정)"
            print(f"  계좌번호: {masked}")
        
        print(f"\n⚡ Redis:")
        print(f"  URL: {cls.REDIS_URL}")
        print(f"  이벤트 버스: {'활성화' if cls.USE_REDIS_EVENTS else '비활성화'}")
        
        print(f"\n🛡️  리스크 관리:")
        print(f"  최대 보유 종목: {cls.MAX_STOCKS}개")
        print(f"  포지션 크기: {cls.POSITION_SIZE_PERCENT}%")
        print(f"  손절매: -{cls.STOP_LOSS_PERCENT}%")
        print(f"  익절매: +{cls.TAKE_PROFIT_PERCENT}%")
        print(f"  일일 손실 한도: -{cls.DAILY_LOSS_LIMIT_PERCENT}%")
        
        print(f"\n📊 전략 설정:")
        print(f"  이동평균: {cls.MA_SHORT_PERIOD}/{cls.MA_LONG_PERIOD}일")
        print(f"  RSI: {cls.RSI_PERIOD}일 ({cls.RSI_OVERSOLD}/{cls.RSI_OVERBOUGHT})")
        print(f"  MACD: {cls.MACD_FAST}/{cls.MACD_SLOW}/{cls.MACD_SIGNAL}")
        print(f"  최소 동의 전략: {cls.MIN_SIGNAL_STRENGTH}개")
        
        if cls.ENABLE_SURGE_DETECTION:
            print(f"\n🚀 급등주 감지:")
            print(f"  상태: 활성화")
            print(f"  자동 승인: {'예' if cls.SURGE_AUTO_APPROVE else '아니오'}")
            print(f"  후보 종목: {cls.SURGE_CANDIDATE_COUNT}개")
            print(f"  최소 상승률: {cls.SURGE_MIN_CHANGE_RATE}%")
            print(f"  최소 거래량 비율: {cls.SURGE_MIN_VOLUME_RATIO}배")
            print(f"  쿨다운: {cls.SURGE_COOLDOWN_MINUTES}분")
        else:
            print(f"\n🚀 급등주 감지: 비활성화")
        
        print("=" * 60 + "\n")

