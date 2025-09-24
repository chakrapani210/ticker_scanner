import os
import shutil
import pytest
from src.core.data import MarketData

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
    import datetime
    import pytz
    # Use a recent UTC-aware timestamp
    ts = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
    class DummyResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {'results': [{
                't': ts,
                'c': 100,
                'o': 99,
                'h': 101,
                'l': 98,
                'v': 1000
            }]}
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: DummyResp())
    cfg = DummyConfig(api_key='dummy', cache_dir='test_cache', cache_expiry_days=1, data={'keep_days': 10, 'discard_old_data': True})
    md = MarketData(cfg)
    df = md.fetch_daily('FAKE', limit=1)
    assert not df.empty
    # Should use cache on second call
    df2 = md.fetch_daily('FAKE', limit=1)
    assert not df2.empty
    assert (df['c'] == df2['c']).all()
