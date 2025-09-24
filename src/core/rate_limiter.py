import time

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove calls that are older than the period
            self.calls = [c for c in self.calls if c > now - self.period]
            if len(self.calls) >= self.max_calls:
                # Wait until the oldest call is older than the period
                time.sleep(self.calls[0] - (now - self.period))
            self.calls.append(time.time())
            return f(*args, **kwargs)
        return wrapper
