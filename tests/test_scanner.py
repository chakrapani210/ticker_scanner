from src.core.scanner import TickerScanner
import pandas as pd

def test_scanner_bullish_bearish():
    config = {'tickers': ['A', 'B']}
    scanner = TickerScanner(config)
    def fake_fetch(ticker):
        # A is bullish, B is bearish
        if ticker == 'A':
            # Gently increasing series with some dips to keep RSI down but SMAs up
            return pd.DataFrame({'c': [100]*26 + [105, 104, 105, 104, 105, 106, 107, 106, 107, 108, 107, 108, 109, 110]})
        else:
            # Sharply decreasing series
            return pd.DataFrame({'c': [110]*26 + [109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96]})
    result = scanner.scan(fake_fetch)
    assert 'A' in result['bullish']
    assert 'B' in result['bearish']
