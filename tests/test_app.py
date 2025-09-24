import pytest
from src.core.app import run_trading_app

def test_run_trading_app(monkeypatch):
    # Patch all dependencies to avoid real API calls and side effects
    monkeypatch.setattr('src.core.data.MarketData.fetch_daily', lambda self, ticker, timespan='day', limit=30: {'c':[100]*30, 'o':[99]*30, 'h':[101]*30, 'l':[98]*30, 'v':[1000]*30})
    monkeypatch.setattr('src.core.strategy.StrategyManager.run', lambda self, data, bucket, ticker=None: [{'action':'buy','qty':1,'reason':'test','risk':'low','strategy':'sma_rsi_combo','ticker':ticker}])
    monkeypatch.setattr('src.core.brokerage.BrokerageManager.place_order', lambda self, signal, bucket: {'order':'placed'})
    monkeypatch.setattr('src.core.tracker.PerformanceTracker.log_order', lambda self, order, explanation: None)
    monkeypatch.setattr('src.core.tracker.PerformanceTracker.update', lambda self, brokerage: None)
    monkeypatch.setattr('src.core.tracker.PerformanceTracker.report', lambda self: None)
    run_trading_app()
