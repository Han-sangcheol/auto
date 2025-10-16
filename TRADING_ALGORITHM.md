# 📈 자동매매 알고리즘 설계

## 📋 개요
자동매매 시스템의 핵심인 매매 알고리즘과 리스크 관리 체계를 설계한 문서입니다.

## 🎯 알고리즘 설계 원칙

### 기본 원칙
- **안정성 우선**: 수익보다 손실 최소화에 집중
- **데이터 기반**: 감정을 배제한 객관적 판단
- **리스크 관리**: 철저한 자금 관리 및 손실 제한
- **백테스팅 검증**: 모든 전략은 충분한 검증 후 적용

### 매매 철학
```
"작은 손실은 받아들이고, 큰 손실은 피하며, 
 꾸준한 수익을 추구한다"
```

## 🧮 1. 기본 매매 전략

### 1.1 이동평균선 크로스오버 전략
```python
class MovingAverageCrossover:
    def __init__(self, short_period=5, long_period=20):
        self.short_period = short_period
        self.long_period = long_period
    
    def generate_signal(self, prices):
        """이동평균선 크로스오버 신호 생성"""
        short_ma = self.calculate_ma(prices, self.short_period)
        long_ma = self.calculate_ma(prices, self.long_period)
        
        # 골든크로스: 매수 신호
        if short_ma[-1] > long_ma[-1] and short_ma[-2] <= long_ma[-2]:
            return SignalType.BUY
        
        # 데드크로스: 매도 신호
        elif short_ma[-1] < long_ma[-1] and short_ma[-2] >= long_ma[-2]:
            return SignalType.SELL
        
        return SignalType.HOLD
    
    @staticmethod
    def calculate_ma(prices, period):
        """단순이동평균 계산"""
        return [sum(prices[i-period:i])/period for i in range(period, len(prices)+1)]
```

### 1.2 RSI 기반 과매수/과매도 전략
```python
class RSIStrategy:
    def __init__(self, period=14, overbought=70, oversold=30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def generate_signal(self, prices):
        """RSI 기반 매매 신호 생성"""
        rsi = self.calculate_rsi(prices, self.period)
        current_rsi = rsi[-1]
        previous_rsi = rsi[-2] if len(rsi) > 1 else current_rsi
        
        # 과매도 구간에서 반등 시 매수
        if current_rsi < self.oversold and current_rsi > previous_rsi:
            return SignalType.BUY
        
        # 과매수 구간에서 하락 시 매도
        elif current_rsi > self.overbought and current_rsi < previous_rsi:
            return SignalType.SELL
        
        return SignalType.HOLD
    
    def calculate_rsi(self, prices, period):
        """RSI 계산"""
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(delta, 0) for delta in deltas]
        losses = [abs(min(delta, 0)) for delta in deltas]
        
        rsi_values = []
        for i in range(period-1, len(gains)):
            avg_gain = sum(gains[i-period+1:i+1]) / period
            avg_loss = sum(losses[i-period+1:i+1]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
```

### 1.3 MACD 전략
```python
class MACDStrategy:
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def generate_signal(self, prices):
        """MACD 신호 생성"""
        macd_line, signal_line, histogram = self.calculate_macd(prices)
        
        if len(histogram) < 2:
            return SignalType.HOLD
        
        # MACD 히스토그램이 0선 위에서 양수로 전환
        if histogram[-1] > 0 and histogram[-2] <= 0:
            return SignalType.BUY
        
        # MACD 히스토그램이 0선 아래로 음수로 전환
        elif histogram[-1] < 0 and histogram[-2] >= 0:
            return SignalType.SELL
        
        return SignalType.HOLD
    
    def calculate_macd(self, prices):
        """MACD 지표 계산"""
        ema_fast = self.calculate_ema(prices, self.fast)
        ema_slow = self.calculate_ema(prices, self.slow)
        
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]
        signal_line = self.calculate_ema(macd_line, self.signal)
        
        histogram = [macd_line[i] - signal_line[i] for i in range(len(signal_line))]
        
        return macd_line, signal_line, histogram
```

## 🛡️ 2. 리스크 관리 시스템

### 2.1 손절매/익절매 관리
```python
class RiskManager:
    def __init__(self, stop_loss_pct=0.05, take_profit_pct=0.1):
        self.stop_loss_pct = stop_loss_pct  # 5% 손절
        self.take_profit_pct = take_profit_pct  # 10% 익절
    
    def check_exit_conditions(self, position, current_price):
        """청산 조건 확인"""
        if not position:
            return None
        
        entry_price = position.entry_price
        position_type = position.type
        
        if position_type == PositionType.LONG:
            # 롱 포지션 손절매 확인
            if current_price <= entry_price * (1 - self.stop_loss_pct):
                return ExitReason.STOP_LOSS
            
            # 롱 포지션 익절매 확인
            elif current_price >= entry_price * (1 + self.take_profit_pct):
                return ExitReason.TAKE_PROFIT
        
        elif position_type == PositionType.SHORT:
            # 숏 포지션 손절매 확인
            if current_price >= entry_price * (1 + self.stop_loss_pct):
                return ExitReason.STOP_LOSS
            
            # 숏 포지션 익절매 확인
            elif current_price <= entry_price * (1 - self.take_profit_pct):
                return ExitReason.TAKE_PROFIT
        
        return None
```

### 2.2 포지션 사이징
```python
class PositionSizer:
    def __init__(self, max_risk_per_trade=0.02, max_portfolio_risk=0.1):
        self.max_risk_per_trade = max_risk_per_trade  # 거래당 최대 2% 리스크
        self.max_portfolio_risk = max_portfolio_risk  # 포트폴리오 최대 10% 리스크
    
    def calculate_position_size(self, account_balance, entry_price, stop_loss_price):
        """포지션 크기 계산"""
        # 1회 거래 최대 손실 금액
        max_loss = account_balance * self.max_risk_per_trade
        
        # 주당 손실 금액
        loss_per_share = abs(entry_price - stop_loss_price)
        
        if loss_per_share == 0:
            return 0
        
        # 최대 매수 가능 주식 수
        max_shares = int(max_loss / loss_per_share)
        
        # 자금 제약 확인
        available_funds = account_balance * 0.9  # 90%만 사용
        max_shares_by_funds = int(available_funds / entry_price)
        
        return min(max_shares, max_shares_by_funds)
    
    def check_portfolio_risk(self, current_positions, new_position_risk):
        """포트폴리오 전체 리스크 확인"""
        total_risk = sum(pos.risk_amount for pos in current_positions)
        total_risk += new_position_risk
        
        portfolio_value = sum(pos.market_value for pos in current_positions)
        risk_ratio = total_risk / portfolio_value if portfolio_value > 0 else 0
        
        return risk_ratio <= self.max_portfolio_risk
```

## 🔄 3. 통합 매매 엔진

### 3.1 메인 트레이딩 엔진
```python
class TradingEngine:
    def __init__(self):
        self.strategies = [
            MovingAverageCrossover(5, 20),
            RSIStrategy(14, 70, 30),
            MACDStrategy(12, 26, 9)
        ]
        self.risk_manager = RiskManager()
        self.position_sizer = PositionSizer()
        self.current_positions = {}
    
    def process_market_data(self, stock_code, market_data):
        """실시간 시장 데이터 처리"""
        try:
            # 1. 현재 포지션 확인
            current_position = self.current_positions.get(stock_code)
            current_price = market_data.current_price
            
            # 2. 청산 조건 확인 (우선순위)
            if current_position:
                exit_reason = self.risk_manager.check_exit_conditions(
                    current_position, current_price
                )
                if exit_reason:
                    self.execute_exit(stock_code, exit_reason)
                    return
            
            # 3. 진입 신호 확인
            if not current_position:
                signal = self.generate_consensus_signal(market_data)
                
                if signal in [SignalType.BUY, SignalType.SELL]:
                    self.execute_entry(stock_code, signal, market_data)
            
        except Exception as e:
            logger.error(f"Trading engine error for {stock_code}: {e}")
    
    def generate_consensus_signal(self, market_data):
        """복수 전략 종합 신호 생성"""
        signals = []
        
        for strategy in self.strategies:
            try:
                signal = strategy.generate_signal(market_data.price_history)
                signals.append(signal)
            except Exception as e:
                logger.warning(f"Strategy error: {e}")
                continue
        
        if not signals:
            return SignalType.HOLD
        
        # 단순 과반수 결정
        buy_count = signals.count(SignalType.BUY)
        sell_count = signals.count(SignalType.SELL)
        
        if buy_count > len(signals) / 2:
            return SignalType.BUY
        elif sell_count > len(signals) / 2:
            return SignalType.SELL
        else:
            return SignalType.HOLD
    
    def execute_entry(self, stock_code, signal, market_data):
        """진입 주문 실행"""
        try:
            entry_price = market_data.current_price
            
            # 손절가 설정
            if signal == SignalType.BUY:
                stop_price = entry_price * (1 - self.risk_manager.stop_loss_pct)
            else:  # SELL
                stop_price = entry_price * (1 + self.risk_manager.stop_loss_pct)
            
            # 포지션 크기 계산
            position_size = self.position_sizer.calculate_position_size(
                self.get_account_balance(), entry_price, stop_price
            )
            
            if position_size <= 0:
                logger.info(f"Position size too small for {stock_code}")
                return
            
            # 주문 실행
            order_result = self.api_client.send_order(
                stock_code=stock_code,
                order_type=signal,
                quantity=position_size,
                price=entry_price
            )
            
            if order_result.success:
                # 포지션 기록
                self.current_positions[stock_code] = Position(
                    stock_code=stock_code,
                    entry_price=entry_price,
                    quantity=position_size,
                    position_type=signal,
                    entry_time=datetime.now()
                )
                
                logger.info(f"Entry order executed: {stock_code} {signal} {position_size}@{entry_price}")
            
        except Exception as e:
            logger.error(f"Entry execution error: {e}")
```

### 3.2 백테스팅 엔진
```python
class BacktestEngine:
    def __init__(self, initial_balance=10000000):  # 1천만원
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = []
        self.trades = []
        self.trading_engine = TradingEngine()
    
    def run_backtest(self, stock_data, start_date, end_date):
        """백테스팅 실행"""
        results = BacktestResult()
        
        for date in pd.date_range(start_date, end_date):
            daily_data = stock_data[stock_data.date == date]
            
            for _, row in daily_data.iterrows():
                market_data = MarketData.from_pandas_row(row)
                
                # 트레이딩 엔진 실행
                self.trading_engine.process_market_data(
                    row.stock_code, market_data
                )
        
        # 결과 계산
        results.total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        results.num_trades = len(self.trades)
        results.win_rate = self.calculate_win_rate()
        results.max_drawdown = self.calculate_max_drawdown()
        results.sharpe_ratio = self.calculate_sharpe_ratio()
        
        return results
    
    def calculate_win_rate(self):
        """승률 계산"""
        if not self.trades:
            return 0
        
        winning_trades = len([t for t in self.trades if t.profit > 0])
        return winning_trades / len(self.trades)
    
    def calculate_max_drawdown(self):
        """최대 손실폭 계산"""
        if not self.trades:
            return 0
        
        running_max = self.initial_balance
        max_drawdown = 0
        
        for trade in self.trades:
            current_balance = trade.balance_after
            running_max = max(running_max, current_balance)
            drawdown = (running_max - current_balance) / running_max
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
```

## 📊 4. 성능 평가 지표

### 4.1 주요 KPI
```python
class PerformanceMetrics:
    @staticmethod
    def calculate_metrics(trades, initial_balance):
        """종합 성과 지표 계산"""
        if not trades:
            return {}
        
        total_return = (trades[-1].balance_after - initial_balance) / initial_balance
        
        # 연간 수익률
        days = (trades[-1].exit_time - trades[0].entry_time).days
        annual_return = ((1 + total_return) ** (365 / max(days, 1))) - 1
        
        # 승률
        win_rate = len([t for t in trades if t.profit > 0]) / len(trades)
        
        # 평균 수익/손실 비율
        winning_trades = [t.profit for t in trades if t.profit > 0]
        losing_trades = [abs(t.profit) for t in trades if t.profit < 0]
        
        avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'total_trades': len(trades),
            'max_drawdown': PerformanceMetrics.max_drawdown(trades)
        }
```

## 🎛️ 5. 알고리즘 설정 인터페이스

### 5.1 Flutter 앱에서 전략 설정
```dart
// 전략 설정 화면
class StrategySettingsScreen extends StatefulWidget {
  @override
  _StrategySettingsScreenState createState() => _StrategySettingsScreenState();
}

class _StrategySettingsScreenState extends State<StrategySettingsScreen> {
  final _formKey = GlobalKey<FormState>();
  
  // 이동평균선 설정
  int shortMaPeriod = 5;
  int longMaPeriod = 20;
  
  // RSI 설정
  int rsiPeriod = 14;
  double oversoldLevel = 30.0;
  double overboughtLevel = 70.0;
  
  // 리스크 관리 설정
  double stopLossPercent = 5.0;
  double takeProfitPercent = 10.0;
  double maxRiskPerTrade = 2.0;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('매매 전략 설정')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: EdgeInsets.all(16.0),
          children: [
            // 이동평균선 설정
            Card(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('이동평균선 전략', style: Theme.of(context).textTheme.headline6),
                    SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            initialValue: shortMaPeriod.toString(),
                            decoration: InputDecoration(
                              labelText: '단기 이동평균 (일)',
                              border: OutlineInputBorder(),
                            ),
                            keyboardType: TextInputType.number,
                            onSaved: (value) => shortMaPeriod = int.parse(value ?? '5'),
                          ),
                        ),
                        SizedBox(width: 16),
                        Expanded(
                          child: TextFormField(
                            initialValue: longMaPeriod.toString(),
                            decoration: InputDecoration(
                              labelText: '장기 이동평균 (일)',
                              border: OutlineInputBorder(),
                            ),
                            keyboardType: TextInputType.number,
                            onSaved: (value) => longMaPeriod = int.parse(value ?? '20'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            
            // RSI 설정
            Card(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('RSI 전략', style: Theme.of(context).textTheme.headline6),
                    SizedBox(height: 16),
                    TextFormField(
                      initialValue: rsiPeriod.toString(),
                      decoration: InputDecoration(
                        labelText: 'RSI 기간 (일)',
                        border: OutlineInputBorder(),
                      ),
                      onSaved: (value) => rsiPeriod = int.parse(value ?? '14'),
                    ),
                    SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            initialValue: oversoldLevel.toString(),
                            decoration: InputDecoration(
                              labelText: '과매도 기준',
                              border: OutlineInputBorder(),
                            ),
                            onSaved: (value) => oversoldLevel = double.parse(value ?? '30'),
                          ),
                        ),
                        SizedBox(width: 16),
                        Expanded(
                          child: TextFormField(
                            initialValue: overboughtLevel.toString(),
                            decoration: InputDecoration(
                              labelText: '과매수 기준',
                              border: OutlineInputBorder(),
                            ),
                            onSaved: (value) => overboughtLevel = double.parse(value ?? '70'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            
            // 리스크 관리 설정
            Card(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('리스크 관리', style: Theme.of(context).textTheme.headline6),
                    SizedBox(height: 16),
                    TextFormField(
                      initialValue: stopLossPercent.toString(),
                      decoration: InputDecoration(
                        labelText: '손절매 비율 (%)',
                        border: OutlineInputBorder(),
                      ),
                      onSaved: (value) => stopLossPercent = double.parse(value ?? '5'),
                    ),
                    SizedBox(height: 16),
                    TextFormField(
                      initialValue: takeProfitPercent.toString(),
                      decoration: InputDecoration(
                        labelText: '익절매 비율 (%)',
                        border: OutlineInputBorder(),
                      ),
                      onSaved: (value) => takeProfitPercent = double.parse(value ?? '10'),
                    ),
                  ],
                ),
              ),
            ),
            
            SizedBox(height: 32),
            ElevatedButton(
              onPressed: _saveSettings,
              child: Text('설정 저장'),
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  void _saveSettings() {
    if (_formKey.currentState?.validate() ?? false) {
      _formKey.currentState?.save();
      
      final settings = TradingSettings(
        shortMaPeriod: shortMaPeriod,
        longMaPeriod: longMaPeriod,
        rsiPeriod: rsiPeriod,
        oversoldLevel: oversoldLevel,
        overboughtLevel: overboughtLevel,
        stopLossPercent: stopLossPercent / 100,
        takeProfitPercent: takeProfitPercent / 100,
      );
      
      context.read<TradingProvider>().updateSettings(settings);
      Navigator.of(context).pop();
    }
  }
}
```

## 📋 알고리즘 검증 체크리스트

### 백테스팅 검증
- [ ] 최소 3년간 데이터로 테스트
- [ ] 다양한 시장 조건에서 검증 (상승장, 하락장, 횡보장)
- [ ] 수수료 및 슬리피지 포함한 실제 비용 반영
- [ ] 과최적화 (Over-fitting) 방지 확인

### 실전 검증
- [ ] 소액으로 실거래 테스트 (1-3개월)
- [ ] 시뮬레이션과 실거래 성과 비교
- [ ] 예외 상황 대응 테스트
- [ ] 시스템 오류 시나리오 테스트

### 성능 기준
- **최소 승률**: 40% 이상
- **최대 손실폭**: 20% 이하  
- **연간 수익률**: 10% 이상 (무위험 수익률 대비)
- **샤프 비율**: 1.0 이상

---

**작성일**: 2025년 9월 12일  
**검증 상태**: 백테스팅 준비 단계  
**리스크 등급**: 중위험 중수익 전략

