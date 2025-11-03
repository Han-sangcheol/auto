"""
리스크 관리 시스템 모듈

[파일 역할]
손실을 제한하고 안전한 매매를 보장하는 리스크 관리 시스템입니다.

[주요 기능]
1. 포지션 관리
   - 보유 종목 추적
   - 손익 실시간 계산
   - 포지션 크기 제한

2. 손절매/익절매
   - 매수가 대비 일정 % 하락 시 자동 손절
   - 매수가 대비 일정 % 상승 시 자동 익절
   - 실시간 가격 모니터링

3. 일일 손실 한도
   - 하루 총 손실 제한
   - 한도 초과 시 신규 매수 중지
   - 다음 거래일에 자동 리셋

4. 포지션 사이징
   - 계좌 잔고 대비 적절한 투자 비율
   - 최대 보유 종목 수 제한
   - 분산 투자 강제

[사용 방법]
risk_manager = RiskManager()
position = risk_manager.add_position(...)
if risk_manager.should_stop_loss(position, current_price):
    # 손절매 실행
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from logger import log
from config import Config
from fee_calculator import FeeCalculator


class Position:
    """포지션 정보 클래스"""
    
    def __init__(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        entry_price: int,
        entry_time: datetime = None
    ):
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.quantity = quantity
        self.entry_price = entry_price  # 최초 매수가
        self.avg_price = entry_price    # 평균 매수가 (추가 매수 시 변경됨)
        self.entry_time = entry_time or datetime.now()
        self.current_price = entry_price
        
        # 추가 매수 추적
        self.average_down_count = 0  # 추가 매수 횟수
        self.average_down_prices = []  # 추가 매수가 기록
        self.total_invested = entry_price * quantity  # 총 투자 금액
        
        # 🆕 뉴스 감성 분석 결과
        self.news_score = 0  # -100 ~ +100 (부정 ~ 긍정)
        
        # 🆕 매도 제어
        self.sell_blocked = False  # True: 자동 매도 금지 (손절/익절 제외)
        
        # 손절/익절가는 평균가 기준으로 계산
        self.update_stop_profit_prices()
    
    def update_stop_profit_prices(self):
        """손절/익절가 재계산 (평균가 기준)"""
        self.stop_loss_price = int(self.avg_price * (1 - Config.STOP_LOSS_PERCENT / 100))
        self.take_profit_price = int(self.avg_price * (1 + Config.TAKE_PROFIT_PERCENT / 100))
    
    def add_position(self, add_quantity: int, add_price: int):
        """추가 매수 (물타기)"""
        self.average_down_count += 1
        self.average_down_prices.append({
            'price': add_price,
            'quantity': add_quantity,
            'time': datetime.now()
        })
        
        # 평균 매수가 재계산
        self.total_invested += add_price * add_quantity
        self.quantity += add_quantity
        self.avg_price = int(self.total_invested / self.quantity)
        
        # 손절/익절가 재계산
        self.update_stop_profit_prices()
        
        log.info(f"추가 매수 완료: 수량 {add_quantity}주 @ {add_price:,}원")
        log.info(f"평균가 변경: {self.entry_price:,}원 -> {self.avg_price:,}원")
        log.info(f"총 수량: {self.quantity}주, 총 투자: {self.total_invested:,}원")
    
    def should_average_down(self) -> bool:
        """추가 매수 조건 확인"""
        if not Config.ENABLE_AVERAGE_DOWN:
            return False
        
        # 최대 추가 매수 횟수 체크
        if self.average_down_count >= Config.MAX_AVERAGE_DOWN_COUNT:
            return False
        
        # 현재 손실률 계산 (평균가 기준)
        current_loss_pct = ((self.current_price - self.avg_price) / self.avg_price) * 100
        
        # 추가 매수 트리거 체크 (각 레벨별로 1회만)
        # 예: -2.5%, -5.0% (손절 -7.5%인 경우)
        trigger_level = (self.average_down_count + 1) * Config.AVERAGE_DOWN_TRIGGER_PERCENT
        
        if current_loss_pct <= -trigger_level and current_loss_pct > -Config.STOP_LOSS_PERCENT:
            return True
        
        return False
    
    def update_price(self, current_price: int):
        """현재가 업데이트"""
        self.current_price = current_price
    
    def get_profit_loss(self) -> int:
        """손익 금액 계산 (평균가 기준)"""
        return (self.current_price - self.avg_price) * self.quantity
    
    def get_profit_loss_percent(self) -> float:
        """손익률 계산 (평균가 기준)"""
        return ((self.current_price - self.avg_price) / self.avg_price) * 100
    
    def get_adjusted_stop_loss_percent(self) -> float:
        """
        🆕 뉴스 점수에 따른 손절 기준 동적 조정
        
        Returns:
            조정된 손절 기준 (%)
            
        Examples:
            - 뉴스 점수 -50 (악재), 기본 3% → 1.5% (50% 강화)
            - 뉴스 점수 0 (중립), 기본 3% → 3% (조정 없음)
            - 뉴스 점수 +50 (호재), 기본 3% → 3% (손절 기준은 유지)
        """
        base_percent = Config.STOP_LOSS_PERCENT
        
        # 뉴스 분석이 비활성화되었거나 뉴스 점수가 없으면 기본값
        if not Config.ENABLE_NEWS_ANALYSIS or self.news_score == 0:
            return base_percent
        
        # 부정 뉴스 (악재): 손절 기준 강화 (더 빨리 손절)
        if self.news_score <= Config.NEWS_SELL_THRESHOLD:
            # 점수 비율 계산 (0 ~ 1)
            score_ratio = min(abs(self.news_score) / 100, 1.0)
            # 강화 비율 적용 (예: 50% 강화)
            adjust_ratio = Config.NEWS_NEGATIVE_STOPLOSS_ADJUST / 100
            adjusted_percent = base_percent * (1 - adjust_ratio * score_ratio)
            return adjusted_percent
        
        # 긍정 뉴스 또는 중립: 손절 기준 유지
        return base_percent
    
    def is_stop_loss_triggered(self) -> bool:
        """손절매 조건 확인 (🆕 뉴스 점수 반영)"""
        adjusted_percent = self.get_adjusted_stop_loss_percent()
        adjusted_stop_loss_price = int(self.avg_price * (1 - adjusted_percent / 100))
        return self.current_price <= adjusted_stop_loss_price
    
    def is_take_profit_triggered(self) -> bool:
        """익절매 조건 확인"""
        return self.current_price >= self.take_profit_price
    
    def __repr__(self):
        return (
            f"Position({self.stock_code}, {self.quantity}주, "
            f"평균가: {self.avg_price:,}원, 현재: {self.current_price:,}원, "
            f"손익률: {self.get_profit_loss_percent():+.2f}%, "
            f"추가매수: {self.average_down_count}회)"
        )


class Trade:
    """거래 기록 클래스"""
    
    def __init__(
        self,
        stock_code: str,
        trade_type: str,
        quantity: int,
        price: int,
        timestamp: datetime = None
    ):
        self.stock_code = stock_code
        self.trade_type = trade_type  # 'BUY' or 'SELL'
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp or datetime.now()
        self.profit_loss = 0
    
    def __repr__(self):
        return (
            f"Trade({self.trade_type}, {self.stock_code}, {self.quantity}주, "
            f"{self.price:,}원, {self.timestamp.strftime('%H:%M:%S')})"
        )


class RiskManager:
    """리스크 관리자 클래스"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.initial_balance = 0
        self.current_balance = 0
        self.daily_start_balance = 0
        self.max_stocks = Config.MAX_STOCKS
        
        # 수수료 계산기 초기화
        self.fee_calculator = FeeCalculator(use_simulation=Config.USE_SIMULATION)
        
        # 수수료 통계
        self.total_fees_paid = 0  # 총 지불한 수수료
        
        log.info("리스크 관리자 초기화 완료")
    
    def set_initial_balance(self, balance: int):
        """초기 잔고 설정"""
        self.initial_balance = balance
        self.current_balance = balance
        self.daily_start_balance = balance
        log.info(f"초기 잔고 설정: {balance:,}원")
    
    def check_stop_loss(self, position: Position) -> bool:
        """
        손절매 조건 확인
        
        Args:
            position: 포지션 정보
        
        Returns:
            손절매 필요 여부
        """
        if position.is_stop_loss_triggered():
            loss_pct = position.get_profit_loss_percent()
            log.warning(
                f"🔴 손절매 조건 발생: {position.stock_code} "
                f"손익률 {loss_pct:.2f}% (기준: -{Config.STOP_LOSS_PERCENT}%)"
            )
            return True
        return False
    
    def check_take_profit(self, position: Position) -> bool:
        """
        익절매 조건 확인
        
        Args:
            position: 포지션 정보
        
        Returns:
            익절매 필요 여부
        """
        if position.is_take_profit_triggered():
            profit_pct = position.get_profit_loss_percent()
            log.success(
                f"🟢 익절매 조건 발생: {position.stock_code} "
                f"손익률 {profit_pct:.2f}% (기준: +{Config.TAKE_PROFIT_PERCENT}%)"
            )
            return True
        return False
    
    def check_average_down(self, position: Position) -> bool:
        """
        추가 매수 조건 확인
        
        Args:
            position: 포지션 정보
        
        Returns:
            추가 매수 필요 여부
        """
        if position.should_average_down():
            loss_pct = position.get_profit_loss_percent()
            log.warning("=" * 70)
            log.warning(f"📉 추가 매수 조건 감지: {position.stock_code}")
            log.warning(f"   평균가: {position.avg_price:,}원")
            log.warning(f"   현재가: {position.current_price:,}원")
            log.warning(f"   손실률: {loss_pct:.2f}%")
            log.warning(f"   추가 매수 횟수: {position.average_down_count}/{Config.MAX_AVERAGE_DOWN_COUNT}")
            log.warning("=" * 70)
            return True
        return False
    
    def execute_average_down(self, stock_code: str, current_price: int) -> bool:
        """
        추가 매수 실행
        
        Args:
            stock_code: 종목 코드
            current_price: 현재가
        
        Returns:
            추가 매수 성공 여부
        """
        position = self.positions.get(stock_code)
        if not position:
            return False
        
        # 추가 매수 수량 계산
        initial_quantity = int(position.total_invested / position.entry_price)  # 최초 매수 수량
        add_quantity = int(initial_quantity * Config.AVERAGE_DOWN_SIZE_RATIO)
        if add_quantity < 1:
            add_quantity = 1
        
        # 필요 금액 계산
        required_amount = current_price * add_quantity
        
        # 잔고 확인
        if self.current_balance < required_amount:
            log.warning(f"❌ 추가 매수 불가: 잔고 부족 ({self.current_balance:,}원 < {required_amount:,}원)")
            return False
        
        # 잔고 차감
        self.current_balance -= required_amount
        
        # 포지션에 추가
        position.add_position(add_quantity, current_price)
        
        log.success(f"✅ 추가 매수 내부 처리 완료: {add_quantity}주 @ {current_price:,}원")
        
        return True
    
    def calculate_position_size(self, price: int) -> int:
        """
        매수 가능 수량 계산
        
        Args:
            price: 주식 가격
        
        Returns:
            매수 가능 수량
        """
        # 1단계: 전체 잔고 중 자동매매 사용 비율 적용
        auto_trading_balance = self.current_balance * (Config.AUTO_TRADING_RATIO / 100)
        
        # 2단계: 자동매매 잔고 중 종목당 비율 적용
        available_cash = auto_trading_balance * (Config.POSITION_SIZE_PERCENT / 100)
        
        # 매수 가능 수량 계산
        quantity = int(available_cash / price)
        
        # 디버깅 로그
        log.info(f"[매수 수량 계산]")
        log.info(f"   총 잔고: {self.current_balance:,}원")
        log.info(f"   자동투자 비율: {Config.AUTO_TRADING_RATIO}% -> {auto_trading_balance:,.0f}원")
        log.info(f"   종목당 비율: {Config.POSITION_SIZE_PERCENT}% -> {available_cash:,.0f}원")
        log.info(f"   현재가: {price:,}원")
        log.info(f"   계산 수량: {quantity}주")
        
        # 최소 1주 이상
        if quantity < 1:
            log.warning(f"❌ 자금 부족: 매수 가능 수량 {quantity}주 (가격: {price:,}원)")
            return 0
        
        return quantity
    
    def check_daily_loss_limit(self) -> bool:
        """
        일일 손실 한도 확인
        
        Returns:
            한도 초과 여부
        """
        if self.daily_start_balance == 0:
            return False
        
        # 현재 총 자산 계산 (잔고 + 보유 종목 평가액)
        positions_value = sum(
            position.current_price * position.quantity
            for position in self.positions.values()
        )
        current_total_asset = self.current_balance + positions_value
        
        # 오늘 총 손실 계산 (시작 잔고 - 현재 총 자산)
        daily_loss = self.daily_start_balance - current_total_asset
        daily_loss_pct = (daily_loss / self.daily_start_balance) * 100
        
        # 손실 한도 초과 확인 (손실이 양수일 때만)
        if daily_loss > 0 and daily_loss_pct >= Config.DAILY_LOSS_LIMIT_PERCENT:
            log.critical(
                f"⛔ 일일 손실 한도 초과: {daily_loss_pct:.2f}% "
                f"(기준: {Config.DAILY_LOSS_LIMIT_PERCENT}%) | "
                f"손실금액: {daily_loss:,}원 | "
                f"시작자산: {self.daily_start_balance:,}원, "
                f"현재자산: {current_total_asset:,}원 (잔고: {self.current_balance:,}원 + 평가액: {positions_value:,}원)"
            )
            return True
        
        return False
    
    def validate_new_position(self, stock_code: str) -> tuple[bool, str]:
        """
        새 포지션 진입 가능 여부 검증
        
        Args:
            stock_code: 종목 코드
        
        Returns:
            (가능 여부, 사유)
        """
        # 이미 보유 중인 종목
        if stock_code in self.positions:
            return False, f"{stock_code}를 이미 보유 중입니다."
        
        # 최대 보유 종목 수 초과
        if len(self.positions) >= self.max_stocks:
            return False, f"최대 보유 종목 수({self.max_stocks}개) 초과"
        
        # 일일 손실 한도 초과
        if self.check_daily_loss_limit():
            return False, "일일 손실 한도 초과"
        
        # 잔고 부족
        if self.current_balance < 10000:  # 최소 1만원
            return False, f"잔고 부족 (현재: {self.current_balance:,}원)"
        
        return True, "검증 통과"
    
    def add_position(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        entry_price: int
    ) -> Optional[Position]:
        """
        포지션 추가
        
        Args:
            stock_code: 종목 코드
            stock_name: 종목명
            quantity: 수량
            entry_price: 매입가
        
        Returns:
            생성된 포지션 또는 None
        """
        # 검증
        is_valid, reason = self.validate_new_position(stock_code)
        if not is_valid:
            log.warning(f"포지션 추가 실패: {reason}")
            return None
        
        # 매수 금액 및 수수료 계산
        buy_amount = quantity * entry_price
        buy_fee = self.fee_calculator.calculate_buy_fee(buy_amount)
        total_cost = buy_amount + buy_fee
        
        # 포지션 생성
        position = Position(stock_code, stock_name, quantity, entry_price)
        self.positions[stock_code] = position
        
        # 잔고 차감 (매수 금액 + 수수료)
        self.current_balance -= total_cost
        
        # 수수료 누적
        self.total_fees_paid += buy_fee
        
        # 거래 기록
        trade = Trade(stock_code, 'BUY', quantity, entry_price)
        self.trades.append(trade)
        
        log.success(
            f"✅ 포지션 추가: {stock_code} {quantity}주 @ {entry_price:,}원 | "
            f"매수금액: {buy_amount:,}원 | 수수료: {buy_fee:,}원 | "
            f"잔고: {self.current_balance:,}원"
        )
        
        # 수수료 정보 상세 로그
        if buy_fee > 0:
            fee_info = self.fee_calculator.get_fee_info(entry_price, quantity)
            log.info(
                f"   💰 수수료 상세: 손익분기점 {fee_info['break_even_price']:,}원 "
                f"({fee_info['break_even_rate']:+.2f}%)"
            )
        
        return position
    
    def remove_position(
        self,
        stock_code: str,
        sell_price: int,
        reason: str = ""
    ) -> Optional[int]:
        """
        포지션 제거 (매도)
        
        Args:
            stock_code: 종목 코드
            sell_price: 매도가
            reason: 매도 사유
        
        Returns:
            순 손익 금액 (수수료 차감 후) 또는 None
        """
        if stock_code not in self.positions:
            log.warning(f"포지션 없음: {stock_code}")
            return None
        
        position = self.positions[stock_code]
        
        # 매도 금액 및 수수료 계산
        sell_amount = position.quantity * sell_price
        sell_fee = self.fee_calculator.calculate_sell_fee(sell_amount)
        net_revenue = sell_amount - sell_fee
        
        # 손익 계산 (수수료 제외)
        position.update_price(sell_price)
        gross_profit_loss = position.get_profit_loss()
        gross_profit_loss_pct = position.get_profit_loss_percent()
        
        # 실제 순 손익 (매수 시 수수료도 고려)
        buy_amount = position.quantity * position.entry_price
        buy_fee = self.fee_calculator.calculate_buy_fee(buy_amount)
        net_profit_loss = gross_profit_loss - buy_fee - sell_fee
        net_profit_loss_pct = (net_profit_loss / buy_amount) * 100
        
        # 잔고 증가 (매도 금액 - 수수료)
        self.current_balance += net_revenue
        
        # 수수료 누적
        self.total_fees_paid += sell_fee
        
        # 거래 기록
        trade = Trade(stock_code, 'SELL', position.quantity, sell_price)
        trade.profit_loss = net_profit_loss  # 순 손익 저장
        self.trades.append(trade)
        
        # 포지션 제거
        del self.positions[stock_code]
        
        # 로그
        emoji = "🟢" if net_profit_loss >= 0 else "🔴"
        log.success(
            f"{emoji} 포지션 청산: {stock_code} {position.quantity}주 @ {sell_price:,}원"
        )
        log.success(
            f"   매도금액: {sell_amount:,}원 | 매도비용: {sell_fee:,}원"
        )
        log.success(
            f"   명목손익: {gross_profit_loss:+,}원 ({gross_profit_loss_pct:+.2f}%)"
        )
        log.success(
            f"   순손익: {net_profit_loss:+,}원 ({net_profit_loss_pct:+.2f}%) [수수료 차감]"
        )
        log.success(
            f"   잔고: {self.current_balance:,}원"
        )
        if reason:
            log.info(f"   사유: {reason}")
        
        return net_profit_loss
    
    def update_position_price(self, stock_code: str, current_price: int):
        """
        포지션 현재가 업데이트
        
        Args:
            stock_code: 종목 코드
            current_price: 현재가
        """
        if stock_code in self.positions:
            self.positions[stock_code].update_price(current_price)
    
    def get_total_value(self) -> int:
        """
        총 평가금액 계산 (현금 + 주식)
        
        Returns:
            총 평가금액
        """
        stock_value = sum(
            pos.current_price * pos.quantity
            for pos in self.positions.values()
        )
        return self.current_balance + stock_value
    
    def get_total_profit_loss(self) -> int:
        """
        총 손익 계산
        
        Returns:
            총 손익 금액
        """
        return self.get_total_value() - self.initial_balance
    
    def get_statistics(self) -> Dict:
        """
        통계 정보 반환
        
        Returns:
            통계 딕셔너리
        """
        total_value = self.get_total_value()
        total_pl = self.get_total_profit_loss()
        total_pl_pct = (total_pl / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
        # 승률 계산
        sell_trades = [t for t in self.trades if t.trade_type == 'SELL']
        winning_trades = [t for t in sell_trades if t.profit_loss > 0]
        win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0
        
        # 수수료 비율
        fee_rate = (self.total_fees_paid / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'stock_value': total_value - self.current_balance,
            'total_value': total_value,
            'total_profit_loss': total_pl,
            'total_profit_loss_pct': total_pl_pct,
            'total_trades': len(self.trades),
            'sell_trades': len(sell_trades),
            'winning_trades': len(winning_trades),
            'win_rate': win_rate,
            'positions_count': len(self.positions),
            'total_fees_paid': self.total_fees_paid,
            'fee_rate': fee_rate
        }
    
    def print_status(self):
        """현재 상태 출력"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("리스크 관리자 현황")
        print("=" * 60)
        print(f"초기 자금:   {stats['initial_balance']:>15,}원")
        print(f"현금 잔고:   {stats['current_balance']:>15,}원")
        print(f"주식 평가:   {stats['stock_value']:>15,}원")
        print(f"총 평가액:   {stats['total_value']:>15,}원")
        print(f"총 손익:     {stats['total_profit_loss']:>+15,}원 ({stats['total_profit_loss_pct']:+.2f}%)")
        print(f"총 수수료:   {stats['total_fees_paid']:>15,}원 ({stats['fee_rate']:.3f}%)")
        print(f"\n총 거래:     {stats['total_trades']:>15}건")
        print(f"매도 거래:   {stats['sell_trades']:>15}건")
        print(f"승리 거래:   {stats['winning_trades']:>15}건")
        print(f"승률:        {stats['win_rate']:>14.1f}%")
        print(f"\n보유 종목:   {stats['positions_count']:>15}개 (최대 {self.max_stocks}개)")
        
        if self.positions:
            print("\n보유 포지션:")
            for code, pos in self.positions.items():
                print(f"  {code}: {pos}")
        
        print("=" * 60 + "\n")
    
    def reset_daily(self):
        """일일 초기화 (매일 장 시작 전 호출)"""
        self.daily_start_balance = self.get_total_value()
        log.info(f"일일 초기화: 시작 자금 {self.daily_start_balance:,}원")


# 테스트 코드
if __name__ == "__main__":
    print("리스크 관리자 테스트")
    print("=" * 60)
    
    # 리스크 관리자 생성
    rm = RiskManager()
    rm.set_initial_balance(10000000)  # 1천만원
    
    # 포지션 추가 테스트
    pos1 = rm.add_position("005930", "삼성전자", 10, 75000)
    pos2 = rm.add_position("000660", "SK하이닉스", 5, 140000)
    
    # 현재가 업데이트
    rm.update_position_price("005930", 76000)
    rm.update_position_price("000660", 145000)
    
    # 상태 출력
    rm.print_status()
    
    # 손절매/익절매 확인
    print("\n손절매/익절매 테스트:")
    for code, pos in rm.positions.items():
        print(f"{code}:")
        print(f"  손절매 가격: {pos.stop_loss_price:,}원")
        print(f"  익절매 가격: {pos.take_profit_price:,}원")
        print(f"  현재 손익률: {pos.get_profit_loss_percent():+.2f}%")
    
    # 매도 테스트
    print("\n매도 테스트:")
    rm.remove_position("005930", 78000, "익절매")
    
    # 최종 상태
    rm.print_status()

