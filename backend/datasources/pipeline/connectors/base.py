from __future__ import annotations

from datasources.models import DataSource


class BaseConnector:
    def __init__(self, datasource: DataSource) -> None:
        self.datasource = datasource

    def fetch(self) -> list[dict[str, object]]:
        raise NotImplementedError
