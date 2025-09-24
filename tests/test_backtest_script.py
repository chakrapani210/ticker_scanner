import pytest
import sys

def test_backtest_import():
    import src.backtest

@pytest.mark.parametrize('simulate', [True, False])
def test_backtest_main(monkeypatch, simulate):
    import src.backtest
    import pandas as pd
    src.backtest.main.__globals__['pd'] = pd
    monkeypatch.setattr('src.backtest.MarketData', lambda config: type('FakeMD', (), {'fetch': lambda self, t, s, e: pd.DataFrame({
        'c': [100]*400, 't': list(range(400))})})())
    monkeypatch.setattr('src.backtest.StrategyManager', lambda config: type('FakeSM', (), {'run': lambda self, d, b: [{'action': 'buy', 'qty': 1, 'strategy': 'sma_rsi_combo', 'reason': 'test', 'index': len(d)-1}]})())
    monkeypatch.setattr('src.backtest.Config', type('FakeConfig', (), {'load': staticmethod(lambda path=None: type('C', (), {
        'backtest': {'years_of_data': 1, 'years_to_backtest': 0.5}, 'tickers': ['FAKE'], 'data': {}, 'polygon': {}})() )}))
    monkeypatch.setattr('builtins.print', lambda *a, **k: None)
    import sys
    sys.modules['tests.test_backtest'] = type('FakeTB', (), {'run_backtest': lambda *a, **k: []})
    src.backtest.main()
