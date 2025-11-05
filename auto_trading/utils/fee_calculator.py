"""
수수료 계산 모듈

[파일 역할]
키움증권의 거래 수수료 체계를 정확히 반영하여 실제 수익률을 계산합니다.

[주요 기능]
- 매수 수수료 계산
- 매도 수수료 계산
- 거래세 계산
- 총 비용 계산

[수수료 체계]
키움증권 기준 (2024년):
- 매수 수수료: 0.015% (최소 수수료 없음)
- 매도 수수료: 0.015%
- 증권거래세: 0.23% (매도 시에만 부과)
- 농어촌특별세: 거래세의 0.15% (매도 시)

[사용 방법]
calculator = FeeCalculator()
buy_fee = calculator.calculate_buy_fee(1000000)  # 매수 금액
sell_fee = calculator.calculate_sell_fee(1000000)  # 매도 금액
"""

from typing import Dict
from utils.logger import log


class FeeCalculator:
    """거래 수수료 계산기"""
    
    # 키움증권 수수료율 (%)
    BUY_COMMISSION_RATE = 0.015  # 실계좌 매수 수수료
    SELL_COMMISSION_RATE = 0.015  # 실계좌 매도 수수료
    SIMULATION_COMMISSION_RATE = 0.35  # 모의투자 수수료 (매수/매도 동일)
    TRANSACTION_TAX_RATE = 0.23  # 증권거래세 (매도 시, 실계좌만)
    RURAL_TAX_RATE = 0.15  # 농어촌특별세 (거래세의 %)
    
    def __init__(self, use_simulation: bool = True):
        """
        초기화
        
        Args:
            use_simulation: 모의투자 여부 (모의투자는 수수료 없음)
        """
        self.use_simulation = use_simulation
        
        if use_simulation:
            log.info("📝 수수료 계산기 초기화 (모의투자 모드)")
            log.info(f"   매수/매도 수수료: {self.SIMULATION_COMMISSION_RATE}%")
        else:
            log.info("📝 수수료 계산기 초기화 (실계좌 모드 - 실제 수수료 적용)")
            log.info(f"   매수 수수료: {self.BUY_COMMISSION_RATE}%")
            log.info(f"   매도 수수료: {self.SELL_COMMISSION_RATE}%")
            log.info(f"   증권거래세: {self.TRANSACTION_TAX_RATE}%")
    
    def calculate_buy_fee(self, amount: int) -> int:
        """
        매수 수수료 계산
        
        Args:
            amount: 매수 금액 (주가 * 수량)
        
        Returns:
            수수료 금액 (원 단위, 소수점 반올림)
        """
        if self.use_simulation:
            # 모의투자: 0.35% 수수료 적용
            fee = round(amount * self.SIMULATION_COMMISSION_RATE / 100)
            return fee
        
        # 실계좌: 0.015% 수수료
        fee = round(amount * self.BUY_COMMISSION_RATE / 100)
        
        return fee
    
    def calculate_sell_fee(self, amount: int) -> int:
        """
        매도 수수료 및 세금 계산
        
        Args:
            amount: 매도 금액 (주가 * 수량)
        
        Returns:
            총 비용 (수수료 + 세금, 원 단위)
        """
        if self.use_simulation:
            # 모의투자: 0.35% 수수료만 (거래세 없음)
            fee = round(amount * self.SIMULATION_COMMISSION_RATE / 100)
            return fee
        
        # 실계좌: 수수료 + 거래세 + 농특세
        # 1. 매도 수수료
        commission = round(amount * self.SELL_COMMISSION_RATE / 100)
        
        # 2. 증권거래세
        transaction_tax = round(amount * self.TRANSACTION_TAX_RATE / 100)
        
        # 3. 농어촌특별세 (거래세의 0.15%)
        rural_tax = round(transaction_tax * self.RURAL_TAX_RATE / 100)
        
        # 총 비용
        total_fee = commission + transaction_tax + rural_tax
        
        return total_fee
    
    def calculate_total_cost(
        self,
        buy_amount: int,
        sell_amount: int
    ) -> Dict[str, int]:
        """
        매수부터 매도까지 총 비용 계산
        
        Args:
            buy_amount: 매수 금액
            sell_amount: 매도 금액
        
        Returns:
            비용 상세 딕셔너리
        """
        buy_fee = self.calculate_buy_fee(buy_amount)
        sell_fee = self.calculate_sell_fee(sell_amount)
        total_fee = buy_fee + sell_fee
        
        # 실제 손익 = 매도금액 - 매수금액 - 총수수료
        gross_profit = sell_amount - buy_amount
        net_profit = gross_profit - total_fee
        
        result = {
            'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'total_fee': total_fee,
            'buy_amount': buy_amount,
            'sell_amount': sell_amount,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'fee_rate': (total_fee / buy_amount * 100) if buy_amount > 0 else 0
        }
        
        return result
    
    def calculate_break_even_price(self, buy_price: int) -> int:
        """
        손익분기점 가격 계산 (수수료를 고려한 최소 매도가)
        
        Args:
            buy_price: 매수가
        
        Returns:
            손익분기점 가격
        """
        if self.use_simulation:
            # 모의투자: 매수 0.35% + 매도 0.35% = 0.70%
            total_fee_rate = (self.SIMULATION_COMMISSION_RATE * 2) / 100
            break_even = round(buy_price * (1 + total_fee_rate))
            return break_even
        
        # 매수 시 수수료율
        buy_fee_rate = self.BUY_COMMISSION_RATE / 100
        
        # 매도 시 총 비용률 (수수료 + 세금)
        sell_fee_rate = (
            self.SELL_COMMISSION_RATE + 
            self.TRANSACTION_TAX_RATE + 
            (self.TRANSACTION_TAX_RATE * self.RURAL_TAX_RATE / 100)
        ) / 100
        
        # 손익분기점 = 매수가 * (1 + 매수수수료율) / (1 - 매도비용률)
        break_even = round(buy_price * (1 + buy_fee_rate) / (1 - sell_fee_rate))
        
        return break_even
    
    def get_fee_info(self, buy_price: int, quantity: int) -> Dict:
        """
        특정 거래의 수수료 정보 조회
        
        Args:
            buy_price: 매수가
            quantity: 수량
        
        Returns:
            수수료 정보 딕셔너리
        """
        buy_amount = buy_price * quantity
        buy_fee = self.calculate_buy_fee(buy_amount)
        break_even_price = self.calculate_break_even_price(buy_price)
        break_even_rate = ((break_even_price - buy_price) / buy_price) * 100
        
        # 예상 매도 수수료 (동일 가격으로 매도 시)
        sell_fee = self.calculate_sell_fee(buy_amount)
        
        return {
            'buy_price': buy_price,
            'quantity': quantity,
            'buy_amount': buy_amount,
            'buy_fee': buy_fee,
            'expected_sell_fee': sell_fee,
            'total_expected_fee': buy_fee + sell_fee,
            'break_even_price': break_even_price,
            'break_even_rate': break_even_rate
        }
    
    def print_fee_summary(self, buy_price: int, quantity: int):
        """수수료 정보 출력"""
        if self.use_simulation:
            info = self.get_fee_info(buy_price, quantity)
            
            print("\n" + "=" * 60)
            print("💰 수수료 정보 (모의투자)")
            print("=" * 60)
            print(f"매수가:           {info['buy_price']:>15,}원")
            print(f"수량:             {info['quantity']:>15}주")
            print(f"매수 금액:        {info['buy_amount']:>15,}원")
            print(f"\n매수 수수료:      {info['buy_fee']:>15,}원 (0.35%)")
            print(f"예상 매도 비용:   {info['expected_sell_fee']:>15,}원 (0.35%)")
            print(f"총 예상 수수료:   {info['total_expected_fee']:>15,}원")
            print(f"\n손익분기점:       {info['break_even_price']:>15,}원 "
                  f"({info['break_even_rate']:+.2f}%)")
            print("=" * 60 + "\n")
            return
        
        info = self.get_fee_info(buy_price, quantity)
        
        print("\n" + "=" * 60)
        print("💰 수수료 정보")
        print("=" * 60)
        print(f"매수가:           {info['buy_price']:>15,}원")
        print(f"수량:             {info['quantity']:>15}주")
        print(f"매수 금액:        {info['buy_amount']:>15,}원")
        print(f"\n매수 수수료:      {info['buy_fee']:>15,}원")
        print(f"예상 매도 비용:   {info['expected_sell_fee']:>15,}원")
        print(f"총 예상 수수료:   {info['total_expected_fee']:>15,}원")
        print(f"\n손익분기점:       {info['break_even_price']:>15,}원 "
              f"({info['break_even_rate']:+.2f}%)")
        print("=" * 60 + "\n")


# 테스트 코드
if __name__ == "__main__":
    print("수수료 계산기 테스트")
    print("=" * 60)
    
    # 실계좌 모드 테스트
    calculator = FeeCalculator(use_simulation=False)
    
    # 예시 1: 삼성전자 10주 매수 (주가 75,000원)
    print("\n예시 1: 삼성전자 10주 @ 75,000원")
    buy_amount = 75000 * 10
    buy_fee = calculator.calculate_buy_fee(buy_amount)
    print(f"매수 금액: {buy_amount:,}원")
    print(f"매수 수수료: {buy_fee:,}원")
    
    # 78,000원에 매도
    sell_amount = 78000 * 10
    sell_fee = calculator.calculate_sell_fee(sell_amount)
    print(f"\n매도 금액: {sell_amount:,}원")
    print(f"매도 비용: {sell_fee:,}원")
    
    # 총 비용 계산
    result = calculator.calculate_total_cost(buy_amount, sell_amount)
    print(f"\n총 수수료: {result['total_fee']:,}원")
    print(f"명목 손익: {result['gross_profit']:,}원")
    print(f"실제 손익: {result['net_profit']:,}원")
    print(f"수수료율: {result['fee_rate']:.3f}%")
    
    # 손익분기점
    break_even = calculator.calculate_break_even_price(75000)
    print(f"\n손익분기점: {break_even:,}원")
    
    # 상세 정보 출력
    calculator.print_fee_summary(75000, 10)
    
    # 모의투자 모드 테스트
    print("\n모의투자 모드 테스트")
    sim_calculator = FeeCalculator(use_simulation=True)
    sim_calculator.print_fee_summary(75000, 10)
    
    print("=" * 60)

