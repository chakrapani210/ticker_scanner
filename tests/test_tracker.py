import pytest
from src.core.tracker import PerformanceTracker

def test_log_and_report_stats(capsys):
    tracker = PerformanceTracker()
    tracker.log_order({'id': 1}, 'Test order')
    tracker.update(None)
    tracker.report()
    out = capsys.readouterr().out
    assert 'Order Log:' in out
    assert 'Performance:' in out
    assert 'Advanced Report' in out
