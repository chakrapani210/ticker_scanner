import pandas as pd
from src.core.strategy import StrategyManager

def run_backtest(strategy, data, bucket_name, ticker):
    signals = strategy.run(data, bucket_name, ticker)
    # Simulate simple buy/sell returns
    returns = []
    price = data['c']
    for s in signals:
        idx = 0  # always use most recent for this simple test
        if s['action'] == 'buy':
            returns.append(price.iloc[idx+1] - price.iloc[idx])  # next day's return
        elif s['action'] == 'sell':
            returns.append(price.iloc[idx] - price.iloc[idx+1])
    return returns

def test_backtest_sma_rsi():
    # Simulate a price jump for buy signal
    closes = [100]*10 + [101]*10 + [102]*10 + [103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113]
    data = {
        'c': pd.Series(closes),
        'o': pd.Series(closes),
        'h': pd.Series([x+1 for x in closes]),
        'l': pd.Series([x-1 for x in closes]),
        'v': pd.Series([1000]*len(closes))
    }
    config = {'enabled': {}}
    sm = StrategyManager(config)
    returns = run_backtest(sm, data, 'short_term', 'FAKE')
    assert len(returns) > 0
    # Check that at least one return is positive (buy signal worked)
    assert any(r > 0 for r in returns)
