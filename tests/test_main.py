def test_main_import():
    import src.main

def test_run_main(monkeypatch):
    monkeypatch.setattr('src.core.app.run_trading_app', lambda: None)
    import importlib
    import sys
    sys.modules.pop('src.main', None)
    import src.main
    importlib.reload(src.main)
