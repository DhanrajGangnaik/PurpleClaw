from __future__ import annotations

from datasources.pipeline.connectors.base import BaseConnector
from persistence import list_inventory


class InventoryConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        return [
            {
                "record_type": "inventory",
                "metric": record.component_name,
                "value": record.version,
                "dimensions": {"asset_id": record.asset_id, "component_type": record.component_type},
                "tags": ["inventory", record.component_type],
            }
            for record in list_inventory(self.datasource.environment_id)
        ]
