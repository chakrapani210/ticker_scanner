from src.core.scanner import TickerScanner
import pandas as pd

def test_scanner_bullish_bearish():
    config = {'tickers': ['A', 'B']}
    scanner = TickerScanner(config)
    def fake_fetch(ticker):
        # A is bullish, B is bearish
        if ticker == 'A':
            return pd.DataFrame({'c': [100]*10 + [101]*10 + [102]*10 + [103, 104, 105, 106, 107, 108, 109, 110, 111, 112]})
        else:
            return pd.DataFrame({'c': [80] + [100]*29})
    result = scanner.scan(fake_fetch)
    assert 'A' in result['bullish']
    assert 'B' in result['bearish']
