import os
import shutil
import pytest
from src.core.data import MarketData
from src.core.config import Config

class DummyConfig(dict):
    def get(self, k, default=None):
        return super().get(k, default)

def setup_module(module):
    # Clean up cache dir before tests
    if os.path.exists('test_cache'):
        shutil.rmtree('test_cache')

def test_fetch_and_cache(monkeypatch):
    # Mock requests.get to avoid real API calls
    import requests
    # Patch meta loading to avoid reading meta.json
    monkeypatch.setattr('src.core.data.MarketData._load_meta', lambda self: setattr(self, 'meta', {}))
    # Patch requests.get to avoid real HTTP requests
    class DummyResp:
        def raise_for_status(self): pass
        def json(self):
            # Return 30 rows to ensure DataFrame is not empty and has enough data
            now = int(datetime.datetime.now().timestamp() * 1000)
            return {'results': [
                {'t': now - i * 86400000, 'c': 100 + i, 'o': 99 + i, 'h': 101 + i, 'l': 98 + i, 'v': 1000 + i}
                for i in range(30)
            ]}
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: DummyResp())
    dummy_cfg = Config(
        polygon={'api_key':'dummy'},
        data={'cache_dir':'test_cache','cache_expiry_days':1,'keep_days':10,'discard_old_data':True},
        tickers=['FAKE']
    )
    md = MarketData(dummy_cfg)
    import datetime
    start_date = datetime.date.today() - datetime.timedelta(days=10)
    end_date = datetime.date.today()
    df = md.fetch('FAKE', start_date, end_date)
    assert not df.empty
    # Should use cache on second call
    df2 = md.fetch('FAKE', start_date, end_date)
    assert not df2.empty
    assert (df['c'] == df2['c']).all()
