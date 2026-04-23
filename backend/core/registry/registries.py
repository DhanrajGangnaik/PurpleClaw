from __future__ import annotations

from collections.abc import Callable
from typing import Any


ConnectorFactory = Callable[..., object]
ScanHandler = Callable[..., dict[str, Any]]

_DATASOURCE_REGISTRY: dict[str, ConnectorFactory] = {}
_SCAN_REGISTRY: dict[str, ScanHandler] = {}


def register_datasource(name: str, factory: ConnectorFactory) -> None:
    _DATASOURCE_REGISTRY[name] = factory


def get_datasource(name: str) -> ConnectorFactory:
    return _DATASOURCE_REGISTRY[name]


def list_datasource_types() -> list[str]:
    return sorted(_DATASOURCE_REGISTRY)


def register_scan(name: str, handler: ScanHandler) -> None:
    _SCAN_REGISTRY[name] = handler


def get_scan(name: str) -> ScanHandler:
    return _SCAN_REGISTRY[name]


def list_scan_types() -> list[str]:
    return sorted(_SCAN_REGISTRY)
