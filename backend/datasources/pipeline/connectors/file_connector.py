from __future__ import annotations

import json
from pathlib import Path

from datasources.pipeline.connectors.base import BaseConnector


class FileConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        raw_path = str(self.datasource.config.get("path", "")).strip()
        if not raw_path:
            return []
        path = Path(raw_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[3] / "data" / raw_path
        if not path.exists():
            return []
        payload = json.loads(path.read_text())
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []
