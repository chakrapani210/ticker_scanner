import pytest
from src.core.config import Config
import tempfile
import os

def test_config_load_success():
    yaml = """
polygon:
  api_key: dummy
    """
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.yaml') as f:
        f.write(yaml)
        fname = f.name
    cfg = Config.load(fname)
    assert cfg.polygon['api_key'] == 'dummy'
    os.remove(fname)

def test_config_load_file_not_found():
    with pytest.raises(FileNotFoundError):
        Config.load('nonexistent.yaml')
