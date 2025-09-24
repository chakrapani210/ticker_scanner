import yaml
from .data import MarketData
from .strategy import StrategyManager
from .brokerage import BrokerageManager
from .buckets import BucketManager
from .tracker import PerformanceTracker
from .scanner import TickerScanner

def run_trading_app():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize components
    data = MarketData(config['polygon'])
    strategies = StrategyManager(config['strategies'])
    brokerage = BrokerageManager(config['webull'])
    buckets = BucketManager(config['buckets'])
    tracker = PerformanceTracker()
    scanner = TickerScanner(config)

    # Scan for best tickers
    def fetch_func(ticker):
        try:
            return data.fetch_daily(ticker=ticker)
        except Exception:
            return None
    scan_result = scanner.scan(fetch_func)
    print(f"Bullish: {scan_result['bullish']}, Bearish: {scan_result['bearish']}")

    # Run strategies for each bucket and shortlisted tickers
    for bucket_name, bucket in buckets.buckets.items():
        if bucket_name == 'short_term':
            tickers = scan_result['bullish']
        elif bucket_name == 'long_term':
            tickers = scan_result['bullish']
        elif bucket_name == 'options':
            tickers = scan_result['bearish']
        else:
            tickers = []
        for ticker in tickers:
            daily_data = data.fetch_daily(ticker=ticker)
            signals = strategies.run(daily_data, bucket_name, ticker)
            for signal in signals:
                explanation = strategies.explain(signal)
                order = brokerage.place_order(signal, bucket)
                tracker.log_order(order, explanation)

    # Track performance
    tracker.update(brokerage)
    tracker.report()
