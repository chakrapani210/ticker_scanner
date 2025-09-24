import pandas as pd

class TickerScanner:
    def __init__(self, config):
        self.config = config
        self.tickers = getattr(config, 'tickers', ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMZN'])

    def scan(self, fetch_func):
        bullish = []
        bearish = []
        for ticker in self.tickers:
            data = fetch_func(ticker)
            if data is None or len(data) < 30:
                continue
            close = data['c']
            sma10 = close.rolling(window=10).mean()
            sma30 = close.rolling(window=30).mean()
            # Debug print for test failures
            print(f"[DEBUG] {ticker}: close[-1]={close.iloc[-1]}, sma10[-1]={sma10.iloc[-1]}, sma30[-1]={sma30.iloc[-1]}")
            if close.iloc[-1] > sma10.iloc[-1] > sma30.iloc[-1]:
                bullish.append(ticker)
            elif close.iloc[-1] < sma10.iloc[-1] < sma30.iloc[-1]:
                bearish.append(ticker)
        return {'bullish': bullish, 'bearish': bearish}
