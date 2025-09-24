from src.core.buckets import BucketManager

def test_bucket_manager():
    from src.core.config import Config
    config = Config(buckets={'short_term': 100, 'long_term': 200, 'options': 50})
    bm = BucketManager(config)
    assert 'short_term' in bm.buckets
    assert bm.buckets['long_term']['capital'] == 200
