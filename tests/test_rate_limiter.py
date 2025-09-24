import time
import pytest
from src.core.rate_limiter import RateLimiter

def test_rate_limiter_allows_calls():
    calls = []
    rl = RateLimiter(3, 1)
    @rl
    def f(x):
        calls.append(x)
        return x
    for i in range(3):
        assert f(i) == i
    assert len(calls) == 3

def test_rate_limiter_blocks(monkeypatch):
    rl = RateLimiter(2, 0.1)
    called = []
    times = [0]
    monkeypatch.setattr(time, 'time', lambda: times[0])
    monkeypatch.setattr(time, 'sleep', lambda s: times.__setitem__(0, times[0]+s))
    @rl
    def f():
        called.append(1)
    f(); f()
    f()
    assert len(called) == 3
