"""
리스크 관리 시스템 모듈
손실을 제한하고 안전한 매매를 보장합니다.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from logger import log
from config import Config


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
        self.entry_price = entry_price
        self.entry_time = entry_time or datetime.now()
        self.current_price = entry_price
        self.stop_loss_price = int(entry_price * (1 - Config.STOP_LOSS_PERCENT / 100))
        self.take_profit_price = int(entry_price * (1 + Config.TAKE_PROFIT_PERCENT / 100))
    
    def update_price(self, current_price: int):
        """현재가 업데이트"""
        self.current_price = current_price
    
    def get_profit_loss(self) -> int:
        """손익 금액 계산"""
        return (self.current_price - self.entry_price) * self.quantity
    
    def get_profit_loss_percent(self) -> float:
        """손익률 계산"""
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
    
    def is_stop_loss_triggered(self) -> bool:
        """손절매 조건 확인"""
        return self.current_price <= self.stop_loss_price
    
    def is_take_profit_triggered(self) -> bool:
        """익절매 조건 확인"""
        return self.current_price >= self.take_profit_price
    
    def __repr__(self):
        return (
            f"Position({self.stock_code}, {self.quantity}주, "
            f"매입: {self.entry_price:,}원, 현재: {self.current_price:,}원, "
            f"손익률: {self.get_profit_loss_percent():+.2f}%)"
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
    
    def calculate_position_size(self, price: int) -> int:
        """
        매수 가능 수량 계산
        
        Args:
            price: 주식 가격
        
        Returns:
            매수 가능 수량
        """
        # 계좌 잔고의 일정 비율만 사용
        available_cash = self.current_balance * (Config.POSITION_SIZE_PERCENT / 100)
        
        # 매수 가능 수량 계산
        quantity = int(available_cash / price)
        
        # 최소 1주 이상
        if quantity < 1:
            log.warning(f"자금 부족: 매수 가능 수량 {quantity}주 (가격: {price:,}원)")
            return 0
        
        log.debug(f"포지션 크기 계산: {quantity}주 @ {price:,}원 = {quantity * price:,}원")
        return quantity
    
    def check_daily_loss_limit(self) -> bool:
        """
        일일 손실 한도 확인
        
        Returns:
            한도 초과 여부
        """
        if self.daily_start_balance == 0:
            return False
        
        # 오늘 총 손실 계산
        daily_loss = self.daily_start_balance - self.current_balance
        daily_loss_pct = (daily_loss / self.daily_start_balance) * 100
        
        # 손실 한도 초과 확인
        if daily_loss_pct >= Config.DAILY_LOSS_LIMIT_PERCENT:
            log.critical(
                f"⛔ 일일 손실 한도 초과: {daily_loss_pct:.2f}% "
                f"(기준: {Config.DAILY_LOSS_LIMIT_PERCENT}%) | "
                f"손실금액: {daily_loss:,}원"
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
        
        # 포지션 생성
        position = Position(stock_code, stock_name, quantity, entry_price)
        self.positions[stock_code] = position
        
        # 잔고 차감
        cost = quantity * entry_price
        self.current_balance -= cost
        
        # 거래 기록
        trade = Trade(stock_code, 'BUY', quantity, entry_price)
        self.trades.append(trade)
        
        log.success(
            f"✅ 포지션 추가: {stock_code} {quantity}주 @ {entry_price:,}원 | "
            f"잔고: {self.current_balance:,}원"
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
            손익 금액 또는 None
        """
        if stock_code not in self.positions:
            log.warning(f"포지션 없음: {stock_code}")
            return None
        
        position = self.positions[stock_code]
        
        # 손익 계산
        position.update_price(sell_price)
        profit_loss = position.get_profit_loss()
        profit_loss_pct = position.get_profit_loss_percent()
        
        # 잔고 증가
        revenue = position.quantity * sell_price
        self.current_balance += revenue
        
        # 거래 기록
        trade = Trade(stock_code, 'SELL', position.quantity, sell_price)
        trade.profit_loss = profit_loss
        self.trades.append(trade)
        
        # 포지션 제거
        del self.positions[stock_code]
        
        # 로그
        emoji = "🟢" if profit_loss >= 0 else "🔴"
        log.success(
            f"{emoji} 포지션 청산: {stock_code} {position.quantity}주 @ {sell_price:,}원 | "
            f"손익: {profit_loss:+,}원 ({profit_loss_pct:+.2f}%) | "
            f"잔고: {self.current_balance:,}원"
        )
        if reason:
            log.info(f"  사유: {reason}")
        
        return profit_loss
    
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
            'positions_count': len(self.positions)
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

