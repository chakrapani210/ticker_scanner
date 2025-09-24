import pytest
from src.core.app import run_trading_app
from src.core.data import MarketData
from src.core.config import Config

def test_run_trading_app(monkeypatch):
    # Patch all dependencies to avoid real API calls and side effects
    monkeypatch.setattr('src.core.data.MarketData.fetch', lambda self, ticker, start_date, end_date: {'c':[100]*30, 'o':[99]*30, 'h':[101]*30, 'l':[98]*30, 'v':[1000]*30})
    monkeypatch.setattr('src.core.strategy.StrategyManager.run', lambda self, data, bucket, ticker=None: [{'action':'buy','qty':1,'reason':'test','risk':'low','strategy':'sma_rsi_combo','ticker':ticker}])
    monkeypatch.setattr('src.core.brokerage.BrokerageManager.place_order', lambda self, signal, bucket: {'order':'placed'})
    monkeypatch.setattr('src.core.tracker.PerformanceTracker.log_order', lambda self, order, explanation: None)
    monkeypatch.setattr('src.core.tracker.PerformanceTracker.update', lambda self, brokerage: None)
    monkeypatch.setattr('src.core.tracker.PerformanceTracker.report', lambda self: None)
    # Patch meta loading to avoid reading meta.json
    monkeypatch.setattr('src.core.data.MarketData._load_meta', lambda self: setattr(self, 'meta', {}))
    # Patch BrokerageManager to avoid real webull login
    monkeypatch.setattr('src.core.brokerage.BrokerageManager.__init__', lambda self, config: None)
    dummy_cfg = Config(
        polygon={'api_key':'dummy'},
        data={'cache_dir':'test_cache','cache_expiry_days':1,'keep_days':10,'discard_old_data':True},
        tickers=['FAKE'],
        webull={'username': 'dummy', 'password': 'dummy'}
    )
    data = MarketData(dummy_cfg)
    run_trading_app(config=dummy_cfg)
