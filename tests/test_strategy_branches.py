import pandas as pd
import pytest
from src.core.strategy import StrategyManager

def make_data(length=260, close_val=100, open_val=99, high_val=101, low_val=98, vol_val=1000):
    return {
        'c': pd.Series([close_val]*length),
        'o': pd.Series([open_val]*length),
        'h': pd.Series([high_val]*length),
        'l': pd.Series([low_val]*length),
        'v': pd.Series([vol_val]*length)
    }

def test_strategy_all_branches():
    config = {'sma_rsi_combo': True, 'rsi_reversal': True, 'volume_surge': True, 'gap_up': True, 'gap_down': True, 'macd_bullish': True, 'macd_bearish': True, 'breakout_high': True, 'breakout_low': True, 'bullish_engulfing': True, 'trend_following': True, 'trend_reversal': True, 'momentum_options': True}
    sm = StrategyManager(config)
    # Test short_term
    data = make_data(260)
    sm.run(data, 'short_term', ticker='FAKE')
    # Test long_term
    sm.run(data, 'long_term', ticker='FAKE')
    # Test options
    sm.run(data, 'options', ticker='FAKE')

def test_strategy_report_stats():
    config = {'sma_rsi_combo': True}
    sm = StrategyManager(config)
    sm.stats['sma_rsi_combo']['success'] = 2
    sm.stats['sma_rsi_combo']['fail'] = 1
    sm.report_stats()

def test_strategy_explain():
    config = {'sma_rsi_combo': True}
    sm = StrategyManager(config)
    s = {'action': 'buy', 'qty': 1, 'ticker': 'FAKE', 'reason': 'test', 'risk': 'low', 'strategy': 'sma_rsi_combo'}
    out = sm.explain(s)
    assert 'Order:' in out
