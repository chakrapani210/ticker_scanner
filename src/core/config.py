import yaml
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class Config:
    polygon: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    webull: Dict[str, Any] = field(default_factory=dict)
    buckets: Dict[str, Any] = field(default_factory=dict)
    strategies: Dict[str, Any] = field(default_factory=dict)
    tickers: list = field(default_factory=list)
    backtest: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def load(path='config.yaml'):
        with open(path, 'r') as f:
            raw = yaml.safe_load(f)
        return Config(**raw)
