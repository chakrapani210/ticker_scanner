import pytest
from src.core.brokerage import BrokerageManager

class DummyWebull:
    def login(self, u, p): return True
    def place_order(self, **kwargs): return {'order': 'placed', **kwargs}
    def place_option_order(self, **kwargs): return {'option_order': 'placed', **kwargs}

def test_brokerage_errors(monkeypatch):
    monkeypatch.setattr('src.core.brokerage.paper_webull', lambda: DummyWebull())
    cfg = type('C', (), {'webull': {'username': 'u', 'password': 'p'}})()
    bm = BrokerageManager(cfg)
    # Missing contract_id
    res = bm.place_order({'action': 'buy_call', 'ticker': 'FAKE', 'qty': 1}, {})
    assert 'error' in res
    res = bm.place_order({'action': 'sell_put', 'ticker': 'FAKE', 'qty': 1}, {})
    assert 'error' in res
    # Unknown action
    res = bm.place_order({'action': 'unknown', 'ticker': 'FAKE', 'qty': 1}, {})
    assert res is None
