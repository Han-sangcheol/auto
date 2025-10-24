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
"""

from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger


class Position:
    """포지션 정보 클래스"""
    
    def __init__(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        entry_price: int,
        entry_time: datetime = None,
        stop_loss_percent: float = 5.0,
        take_profit_percent: float = 10.0
    ):
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_time = entry_time or datetime.now()
        self.current_price = entry_price
        self.stop_loss_price = int(entry_price * (1 - stop_loss_percent / 100))
        self.take_profit_price = int(entry_price * (1 + take_profit_percent / 100))
    
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
    
    def __init__(
        self,
        max_stocks: int = 3,
        position_size_percent: float = 10.0,
        stop_loss_percent: float = 5.0,
        take_profit_percent: float = 10.0,
        daily_loss_limit_percent: float = 3.0
    ):
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.initial_balance = 0
        self.current_balance = 0
        self.daily_start_balance = 0
        
        # 설정
        self.max_stocks = max_stocks
        self.position_size_percent = position_size_percent
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.daily_loss_limit_percent = daily_loss_limit_percent
        
        logger.info("리스크 관리자 초기화 완료")
    
    def set_initial_balance(self, balance: int):
        """초기 잔고 설정"""
        self.initial_balance = balance
        self.current_balance = balance
        self.daily_start_balance = balance
        logger.info(f"초기 잔고 설정: {balance:,}원")
    
    def check_stop_loss(self, position: Position) -> bool:
        """손절매 조건 확인"""
        if position.is_stop_loss_triggered():
            loss_pct = position.get_profit_loss_percent()
            logger.warning(
                f"🔴 손절매 조건 발생: {position.stock_code} "
                f"손익률 {loss_pct:.2f}% (기준: -{self.stop_loss_percent}%)"
            )
            return True
        return False
    
    def check_take_profit(self, position: Position) -> bool:
        """익절매 조건 확인"""
        if position.is_take_profit_triggered():
            profit_pct = position.get_profit_loss_percent()
            logger.success(
                f"🟢 익절매 조건 발생: {position.stock_code} "
                f"손익률 {profit_pct:.2f}% (기준: +{self.take_profit_percent}%)"
            )
            return True
        return False
    
    def calculate_position_size(self, price: int) -> int:
        """매수 가능 수량 계산"""
        available_cash = self.current_balance * (self.position_size_percent / 100)
        quantity = int(available_cash / price)
        
        if quantity < 1:
            logger.warning(f"자금 부족: 매수 가능 수량 {quantity}주 (가격: {price:,}원)")
            return 0
        
        logger.debug(f"포지션 크기 계산: {quantity}주 @ {price:,}원 = {quantity * price:,}원")
        return quantity
    
    def check_daily_loss_limit(self) -> bool:
        """일일 손실 한도 확인"""
        if self.daily_start_balance == 0:
            return False
        
        daily_loss = self.daily_start_balance - self.current_balance
        daily_loss_pct = (daily_loss / self.daily_start_balance) * 100
        
        if daily_loss_pct >= self.daily_loss_limit_percent:
            logger.critical(
                f"⛔ 일일 손실 한도 초과: {daily_loss_pct:.2f}% "
                f"(기준: {self.daily_loss_limit_percent}%) | "
                f"손실금액: {daily_loss:,}원"
            )
            return True
        
        return False
    
    def validate_new_position(self, stock_code: str) -> tuple[bool, str]:
        """새 포지션 진입 가능 여부 검증"""
        if stock_code in self.positions:
            return False, f"{stock_code}를 이미 보유 중입니다."
        
        if len(self.positions) >= self.max_stocks:
            return False, f"최대 보유 종목 수({self.max_stocks}개) 초과"
        
        if self.check_daily_loss_limit():
            return False, "일일 손실 한도 초과"
        
        if self.current_balance < 10000:
            return False, f"잔고 부족 (현재: {self.current_balance:,}원)"
        
        return True, "검증 통과"
    
    def add_position(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        entry_price: int
    ) -> Optional[Position]:
        """포지션 추가"""
        is_valid, reason = self.validate_new_position(stock_code)
        if not is_valid:
            logger.warning(f"포지션 추가 실패: {reason}")
            return None
        
        position = Position(
            stock_code, stock_name, quantity, entry_price,
            stop_loss_percent=self.stop_loss_percent,
            take_profit_percent=self.take_profit_percent
        )
        self.positions[stock_code] = position
        
        cost = quantity * entry_price
        self.current_balance -= cost
        
        trade = Trade(stock_code, 'BUY', quantity, entry_price)
        self.trades.append(trade)
        
        logger.success(
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
        """포지션 제거 (매도)"""
        if stock_code not in self.positions:
            logger.warning(f"포지션 없음: {stock_code}")
            return None
        
        position = self.positions[stock_code]
        position.update_price(sell_price)
        profit_loss = position.get_profit_loss()
        profit_loss_pct = position.get_profit_loss_percent()
        
        revenue = position.quantity * sell_price
        self.current_balance += revenue
        
        trade = Trade(stock_code, 'SELL', position.quantity, sell_price)
        trade.profit_loss = profit_loss
        self.trades.append(trade)
        
        del self.positions[stock_code]
        
        emoji = "🟢" if profit_loss >= 0 else "🔴"
        logger.success(
            f"{emoji} 포지션 청산: {stock_code} {position.quantity}주 @ {sell_price:,}원 | "
            f"손익: {profit_loss:+,}원 ({profit_loss_pct:+.2f}%) | "
            f"잔고: {self.current_balance:,}원"
        )
        if reason:
            logger.info(f"  사유: {reason}")
        
        return profit_loss
    
    def update_position_price(self, stock_code: str, current_price: int):
        """포지션 현재가 업데이트"""
        if stock_code in self.positions:
            self.positions[stock_code].update_price(current_price)
    
    def get_total_value(self) -> int:
        """총 평가금액 계산 (현금 + 주식)"""
        stock_value = sum(
            pos.current_price * pos.quantity
            for pos in self.positions.values()
        )
        return self.current_balance + stock_value
    
    def get_total_profit_loss(self) -> int:
        """총 손익 계산"""
        return self.get_total_value() - self.initial_balance
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total_value = self.get_total_value()
        total_pl = self.get_total_profit_loss()
        total_pl_pct = (total_pl / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
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
    
    def reset_daily(self):
        """일일 초기화 (매일 장 시작 전 호출)"""
        self.daily_start_balance = self.get_total_value()
        logger.info(f"일일 초기화: 시작 자금 {self.daily_start_balance:,}원")

