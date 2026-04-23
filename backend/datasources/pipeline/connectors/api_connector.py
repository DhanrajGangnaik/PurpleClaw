from __future__ import annotations

import json
from urllib import request

from datasources.pipeline.connectors.base import BaseConnector


class APIConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        url = str(self.datasource.config.get("url", "")).strip()
        if not url:
            return []
        probe = request.Request(url, headers={"User-Agent": "PurpleClaw/0.1 pipeline"})  # noqa: S310
        with request.urlopen(probe, timeout=min(max(int(self.datasource.config.get("timeout_seconds", 2)), 1), 5)) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []
