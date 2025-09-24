import pytest
import pandas as pd
from src.core.strategy import StrategyManager

def test_sma_rsi_combo():
    # Create fake data for bullish SMA/RSI
    # Make sure last close > 10-day SMA and SMA10 > SMA30 and RSI < 70
    closes = [100]*30 + [101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 105, 106]
    data = {
        'c': pd.Series(closes),
        'o': pd.Series(closes),
        'h': pd.Series([x + 1 for x in closes]),
        'l': pd.Series([x - 1 for x in closes]),
        'v': pd.Series([1000] * len(closes))
    }
    config = {'enabled': {}}
    sm = StrategyManager(config)
    signals = sm.run(data, 'short_term', ticker='FAKE')
    assert any(s['strategy'] == 'sma_rsi_combo' and s['action'] == 'buy' for s in signals)
