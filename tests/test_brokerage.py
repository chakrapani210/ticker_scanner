import pytest
from src.core.brokerage import BrokerageManager

class DummyWebull:
    def login(self, u, p):
        return True
    def place_order(self, **kwargs):
        return {'order': 'placed', **kwargs}
    def place_option_order(self, **kwargs):
        return {'option_order': 'placed', **kwargs}

def test_place_buy_sell(monkeypatch):
    monkeypatch.setattr('src.core.brokerage.paper_webull', lambda: DummyWebull())
    config = {'username': 'u', 'password': 'p'}
    bm = BrokerageManager(config)
    buy = bm.place_order({'action': 'buy', 'ticker': 'FAKE', 'qty': 1}, {})
    assert buy['action'] == 'BUY'
    sell = bm.place_order({'action': 'sell', 'ticker': 'FAKE', 'qty': 1}, {})
    assert sell['action'] == 'SELL'

def test_place_option(monkeypatch):
    monkeypatch.setattr('src.core.brokerage.paper_webull', lambda: DummyWebull())
    config = {'username': 'u', 'password': 'p'}
    bm = BrokerageManager(config)
    call = bm.place_order({'action': 'buy_call', 'ticker': 'FAKE', 'qty': 1, 'contract_id': 123, 'price': 0}, {})
    assert call['option_order'] == 'placed'
    put = bm.place_order({'action': 'sell_put', 'ticker': 'FAKE', 'qty': 1, 'contract_id': 123, 'price': 0}, {})
    assert put['option_order'] == 'placed'
