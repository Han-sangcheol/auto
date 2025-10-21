"""
자동매매 엔진 모듈

[파일 역할]
전체 매매 프로세스를 자동화하는 핵심 엔진입니다.
모든 구성 요소를 통합하여 자동매매를 실행합니다.

[주요 기능]
1. 초기화
   - 계좌 정보 조회
   - 보유 종목 확인
   - 관심 종목 등록
   - 실시간 시세 구독

2. 실시간 모니터링
   - 실시간 가격 데이터 수신
   - 가격 히스토리 누적
   - 매매 신호 분석

3. 자동 매매 실행
   - 매수/매도 신호 감지
   - 리스크 관리 검증
   - 주문 전송
   - 체결 확인

4. 리스크 관리
   - 손절매/익절매 모니터링
   - 일일 손실 한도 확인
   - 포지션 관리

[흐름]
초기화 → 실시간 데이터 수신 → 신호 생성 → 리스크 검증 → 주문 실행 → 반복

[사용 방법]
engine = TradingEngine(kiwoom_api)
engine.initialize()
engine.start_trading()
"""

from typing import Dict, List, Optional
from datetime import datetime, time as dt_time
import time
from collections import defaultdict

from kiwoom_api import KiwoomAPI
from strategies import MultiStrategy, SignalType, create_default_strategies
from risk_manager import RiskManager
from indicators import calculate_all_indicators
from logger import log
from config import Config


class TradingEngine:
    """자동매매 엔진 클래스"""
    
    def __init__(self, kiwoom: KiwoomAPI):
        self.kiwoom = kiwoom
        self.risk_manager = RiskManager()
        
        # 전략 초기화
        base_strategies = create_default_strategies(Config)
        self.strategy = MultiStrategy(
            base_strategies,
            Config.MIN_SIGNAL_STRENGTH
        )
        
        # 가격 데이터 저장 (종목별)
        self.price_history: Dict[str, List[float]] = defaultdict(list)
        
        # 실행 상태
        self.is_running = False
        self.watch_list = Config.WATCH_LIST
        
        # 통계
        self.last_check_time = {}
        self.signal_count = 0
        
        log.info("자동매매 엔진 초기화 완료")
    
    def initialize(self) -> bool:
        """
        엔진 초기화
        
        Returns:
            초기화 성공 여부
        """
        try:
            log.info("자동매매 엔진 초기화 중...")
            
            # 1. 계좌 정보 조회
            balance_info = self.kiwoom.get_balance()
            if not balance_info:
                log.error("잔고 조회 실패")
                return False
            
            cash = balance_info.get('cash', 0)
            self.risk_manager.set_initial_balance(cash)
            
            log.info(f"계좌 잔고: {cash:,}원")
            
            # 2. 보유 종목 조회
            holdings = self.kiwoom.get_holdings()
            log.info(f"보유 종목: {len(holdings)}개")
            
            for holding in holdings:
                self.risk_manager.add_position(
                    holding['code'],
                    holding['name'],
                    holding['quantity'],
                    holding['buy_price']
                )
            
            # 3. 실시간 시세 등록
            self.kiwoom.set_real_data_callback(self.on_price_update)
            self.kiwoom.register_real_data(self.watch_list)
            
            log.success("자동매매 엔진 초기화 완료")
            return True
            
        except Exception as e:
            log.error(f"엔진 초기화 중 오류: {e}")
            return False
    
    def start_trading(self):
        """자동매매 시작"""
        if self.is_running:
            log.warning("이미 실행 중입니다.")
            return
        
        self.is_running = True
        log.success("🚀 자동매매 시작!")
        log.info(f"관심 종목: {', '.join(self.watch_list)}")
        
        # 현재 상태 출력
        self.risk_manager.print_status()
        
        # 메인 루프
        try:
            while self.is_running:
                # 장 운영 시간 확인
                if not self.is_market_open():
                    if datetime.now().time() >= dt_time(15, 30):  # 3시 30분 이후
                        log.info("장 마감. 자동매매를 종료합니다.")
                        self.stop_trading()
                        break
                    
                    time.sleep(60)  # 1분 대기
                    continue
                
                # 손절매/익절매 확인 (최우선)
                self.check_exit_conditions()
                
                # 일일 손실 한도 확인
                if self.risk_manager.check_daily_loss_limit():
                    log.critical("⛔ 일일 손실 한도 초과로 자동매매를 중지합니다.")
                    self.stop_trading()
                    break
                
                # 대기
                time.sleep(5)  # 5초마다 체크
                
        except KeyboardInterrupt:
            log.info("사용자가 중단했습니다.")
            self.stop_trading()
        except Exception as e:
            log.error(f"자동매매 중 오류 발생: {e}")
            self.stop_trading()
    
    def stop_trading(self):
        """자동매매 중지"""
        self.is_running = False
        log.info("🛑 자동매매 중지")
        
        # 최종 통계 출력
        self.risk_manager.print_status()
    
    def is_market_open(self) -> bool:
        """
        장 운영 시간 확인
        
        Returns:
            장 운영 중 여부
        """
        now = datetime.now()
        
        # 주말 체크
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 장 시간 체크 (9:00 ~ 15:30)
        current_time = now.time()
        market_open = dt_time(9, 0)
        market_close = dt_time(15, 30)
        
        return market_open <= current_time <= market_close
    
    def on_price_update(self, stock_code: str, price_data: Dict):
        """
        실시간 시세 업데이트 처리
        
        Args:
            stock_code: 종목 코드
            price_data: 가격 데이터
        """
        if not self.is_running:
            return
        
        try:
            current_price = price_data['current_price']
            
            # 가격 히스토리 업데이트
            self.price_history[stock_code].append(current_price)
            
            # 최근 100개만 유지
            if len(self.price_history[stock_code]) > 100:
                self.price_history[stock_code] = self.price_history[stock_code][-100:]
            
            # 보유 중인 종목의 현재가 업데이트
            self.risk_manager.update_position_price(stock_code, current_price)
            
            # 최소 30개 이상 데이터가 있어야 신호 생성
            if len(self.price_history[stock_code]) < 30:
                return
            
            # 너무 자주 체크하지 않도록 (1분에 1번)
            now = time.time()
            last_check = self.last_check_time.get(stock_code, 0)
            if now - last_check < 60:  # 60초
                return
            
            self.last_check_time[stock_code] = now
            
            # 매매 신호 생성
            self.process_signal(stock_code, self.price_history[stock_code])
            
        except Exception as e:
            log.error(f"시세 업데이트 처리 중 오류: {e}")
    
    def process_signal(self, stock_code: str, prices: List[float]):
        """
        매매 신호 처리
        
        Args:
            stock_code: 종목 코드
            prices: 가격 리스트
        """
        try:
            # 신호 생성
            signal_result = self.strategy.generate_signal(prices)
            signal = signal_result['signal']
            
            if signal == SignalType.HOLD:
                return
            
            self.signal_count += 1
            current_price = prices[-1]
            
            # 매수 신호
            if signal == SignalType.BUY:
                self.execute_buy(stock_code, current_price, signal_result)
            
            # 매도 신호
            elif signal == SignalType.SELL:
                self.execute_sell(stock_code, current_price, signal_result)
                
        except Exception as e:
            log.error(f"신호 처리 중 오류: {e}")
    
    def execute_buy(
        self,
        stock_code: str,
        current_price: int,
        signal_result: Dict
    ):
        """
        매수 실행
        
        Args:
            stock_code: 종목 코드
            current_price: 현재가
            signal_result: 신호 정보
        """
        try:
            # 리스크 검증
            is_valid, reason = self.risk_manager.validate_new_position(stock_code)
            if not is_valid:
                log.warning(f"매수 불가: {stock_code} - {reason}")
                return
            
            # 매수 수량 계산
            quantity = self.risk_manager.calculate_position_size(current_price)
            if quantity < 1:
                log.warning(f"매수 불가: {stock_code} - 수량 부족")
                return
            
            # 주문 전송
            log.info(
                f"📈 매수 시도: {stock_code} {quantity}주 @ {current_price:,}원 | "
                f"신호 강도: {signal_result['strength']:.2f}"
            )
            
            order_result = self.kiwoom.buy_order(
                stock_code,
                quantity,
                0  # 시장가 주문
            )
            
            if order_result:
                # 포지션 추가
                stock_name = stock_code  # 실제로는 종목명 조회 필요
                position = self.risk_manager.add_position(
                    stock_code,
                    stock_name,
                    quantity,
                    current_price
                )
                
                if position:
                    log.success(
                        f"✅ 매수 완료: {stock_code} {quantity}주 @ {current_price:,}원 | "
                        f"사유: {signal_result['reason']}"
                    )
            else:
                log.error(f"매수 주문 실패: {stock_code}")
                
        except Exception as e:
            log.error(f"매수 실행 중 오류: {e}")
    
    def execute_sell(
        self,
        stock_code: str,
        current_price: int,
        signal_result: Dict
    ):
        """
        매도 실행
        
        Args:
            stock_code: 종목 코드
            current_price: 현재가
            signal_result: 신호 정보
        """
        try:
            # 보유 종목 확인
            if stock_code not in self.risk_manager.positions:
                log.debug(f"매도 불가: {stock_code} - 보유하지 않음")
                return
            
            position = self.risk_manager.positions[stock_code]
            
            # 주문 전송
            log.info(
                f"📉 매도 시도: {stock_code} {position.quantity}주 @ {current_price:,}원 | "
                f"신호 강도: {signal_result['strength']:.2f}"
            )
            
            order_result = self.kiwoom.sell_order(
                stock_code,
                position.quantity,
                0  # 시장가 주문
            )
            
            if order_result:
                # 포지션 제거
                profit_loss = self.risk_manager.remove_position(
                    stock_code,
                    current_price,
                    signal_result['reason']
                )
                
                if profit_loss is not None:
                    log.success(
                        f"✅ 매도 완료: {stock_code} {position.quantity}주 @ {current_price:,}원 | "
                        f"손익: {profit_loss:+,}원"
                    )
            else:
                log.error(f"매도 주문 실패: {stock_code}")
                
        except Exception as e:
            log.error(f"매도 실행 중 오류: {e}")
    
    def check_exit_conditions(self):
        """
        손절매/익절매 조건 확인
        """
        try:
            for stock_code, position in list(self.risk_manager.positions.items()):
                # 손절매 확인
                if self.risk_manager.check_stop_loss(position):
                    self.execute_exit(
                        stock_code,
                        position.current_price,
                        "손절매"
                    )
                
                # 익절매 확인
                elif self.risk_manager.check_take_profit(position):
                    self.execute_exit(
                        stock_code,
                        position.current_price,
                        "익절매"
                    )
                    
        except Exception as e:
            log.error(f"청산 조건 확인 중 오류: {e}")
    
    def execute_exit(self, stock_code: str, sell_price: int, reason: str):
        """
        강제 청산 실행
        
        Args:
            stock_code: 종목 코드
            sell_price: 매도가
            reason: 청산 사유
        """
        try:
            if stock_code not in self.risk_manager.positions:
                return
            
            position = self.risk_manager.positions[stock_code]
            
            log.warning(f"⚠️  강제 청산: {stock_code} - {reason}")
            
            # 주문 전송
            order_result = self.kiwoom.sell_order(
                stock_code,
                position.quantity,
                0  # 시장가 주문
            )
            
            if order_result:
                # 포지션 제거
                profit_loss = self.risk_manager.remove_position(
                    stock_code,
                    sell_price,
                    reason
                )
                
                if profit_loss is not None:
                    log.success(f"✅ 청산 완료: 손익 {profit_loss:+,}원")
            else:
                log.error(f"청산 주문 실패: {stock_code}")
                
        except Exception as e:
            log.error(f"청산 실행 중 오류: {e}")
    
    def get_status(self) -> Dict:
        """
        현재 상태 반환
        
        Returns:
            상태 정보 딕셔너리
        """
        stats = self.risk_manager.get_statistics()
        
        return {
            'is_running': self.is_running,
            'watch_list': self.watch_list,
            'signal_count': self.signal_count,
            'positions': len(self.risk_manager.positions),
            'statistics': stats
        }


# 테스트 코드
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    print("자동매매 엔진 테스트")
    print("=" * 60)
    
    # PyQt 애플리케이션 생성 (키움 API 필요)
    app = QApplication(sys.argv)
    
    # 키움 API 초기화
    kiwoom = KiwoomAPI()
    
    if not kiwoom.login():
        print("❌ 로그인 실패")
        sys.exit(1)
    
    # 자동매매 엔진 생성
    engine = TradingEngine(kiwoom)
    
    if not engine.initialize():
        print("❌ 엔진 초기화 실패")
        sys.exit(1)
    
    # 상태 출력
    status = engine.get_status()
    print(f"\n엔진 상태:")
    print(f"  실행 중: {status['is_running']}")
    print(f"  관심 종목: {', '.join(status['watch_list'])}")
    print(f"  보유 종목: {status['positions']}개")
    
    print("\n✅ 테스트 완료")
    sys.exit(0)

