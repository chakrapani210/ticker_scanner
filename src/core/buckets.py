class BucketManager:
    def __init__(self, config):
        buckets_cfg = getattr(config, 'buckets', {})
        self.buckets = {
            'short_term': {'capital': buckets_cfg.get('short_term', 1000)},
            'long_term': {'capital': buckets_cfg.get('long_term', 2000)},
            'options': {'capital': buckets_cfg.get('options', 500)}
        }
