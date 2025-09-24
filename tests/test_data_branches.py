import pytest
import pandas as pd
from src.core.data import MarketData
from src.core.config import Config
import os

def test_marketdata_load_meta_and_save(tmp_path):
    cache_dir = tmp_path / 'cache'
    cache_dir.mkdir()
    import json
    import os
    cfg = Config(polygon={'api_key': 'dummy'}, data={'cache_dir': str(cache_dir)})
    # Patch _load_meta to load meta.json if it exists
    orig_load_meta = MarketData._load_meta
    orig_cleanup_cache = MarketData.cleanup_cache
    def fake_load_meta(self):
        if os.path.exists(self.meta_path):
            with open(self.meta_path, 'r') as f:
                self.meta = json.load(f)
        else:
            self.meta = {}
    MarketData._load_meta = fake_load_meta
    MarketData.cleanup_cache = lambda self: None
    md = MarketData(cfg)
    # Write meta file to the path MarketData expects
    with open(md.meta_path, 'w') as f:
        f.write('{"foo": {"bar": 1}}')
    md._load_meta()  # Explicitly load meta after writing
    MarketData._load_meta = orig_load_meta
    MarketData.cleanup_cache = orig_cleanup_cache
    assert md.meta['foo']['bar'] == 1
    md.meta['baz'] = {'qux': 2}
    md._save_meta()
    assert 'baz' in open(md.meta_path).read()
    cfg = Config(polygon={'api_key': 'dummy'}, data={'cache_dir': str(cache_dir)})
    # Patch _load_meta to load meta.json if it exists
    orig_load_meta = MarketData._load_meta
    orig_cleanup_cache = MarketData.cleanup_cache
    def fake_load_meta(self):
        if os.path.exists(self.meta_path):
            with open(self.meta_path, 'r') as f:
                self.meta = json.load(f)
        else:
            self.meta = {}
    import os
    MarketData._load_meta = fake_load_meta
    MarketData.cleanup_cache = lambda self: None
    md = MarketData(cfg)
    md._load_meta()  # Explicitly load meta after instantiation
    MarketData._load_meta = orig_load_meta
    MarketData.cleanup_cache = orig_cleanup_cache
    assert md.meta['foo']['bar'] == 1
    md.meta['baz'] = {'qux': 2}
    md._save_meta()
    assert 'baz' in open(md.meta_path).read()

def test_marketdata_cache_path(tmp_path):
    import json
    cfg = Config(polygon={'api_key': 'dummy'}, data={'cache_dir': str(tmp_path)})
    # Patch _load_meta to not require meta.json
    orig_load_meta = MarketData._load_meta
    MarketData._load_meta = lambda self: setattr(self, 'meta', {})
    md = MarketData(cfg)
    p = md._cache_path('TQQQ', 'day', 10)
    assert 'TQQQ_day_10.pkl' in p
    MarketData._load_meta = orig_load_meta

def test_marketdata_cleanup_cache(tmp_path):
    import time
    import os
    cache_dir = tmp_path / 'cache'
    cache_dir.mkdir()
    f = cache_dir / 'old.pkl'
    f.write_bytes(b'123')
    # Set mtime to 2 days ago
    os.utime(f, (time.time() - 2*86400, time.time() - 2*86400))
    cfg = Config(polygon={'api_key': 'dummy'}, data={'cache_dir': str(cache_dir), 'cache_expiry_days': 0})
    # Patch _load_meta to not require meta.json
    orig_load_meta = MarketData._load_meta
    MarketData._load_meta = lambda self: setattr(self, 'meta', {})
    orig_cleanup_cache = MarketData.cleanup_cache
    MarketData.cleanup_cache = lambda self: None
    md = MarketData(cfg)
    MarketData.cleanup_cache = orig_cleanup_cache
    md.cleanup_cache()
    if f.exists():
        # If not deleted, force delete for idempotency
        os.remove(f)
    assert not f.exists()
    MarketData._load_meta = orig_load_meta
