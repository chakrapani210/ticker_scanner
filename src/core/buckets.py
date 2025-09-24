class BucketManager:
    def __init__(self, config):
        self.buckets = {
            'short_term': {'capital': config.get('short_term', 1000)},
            'long_term': {'capital': config.get('long_term', 2000)},
            'options': {'capital': config.get('options', 500)}
        }
