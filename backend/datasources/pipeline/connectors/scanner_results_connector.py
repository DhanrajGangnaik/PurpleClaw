from __future__ import annotations

from datasources.pipeline.connectors.base import BaseConnector
from scanning import list_scans


class ScannerResultsConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        return [
            {
                "record_type": "scan_result",
                "metric": "findings_created",
                "value": scan.result.findings_created if scan.result else 0,
                "dimensions": {"scan_id": scan.request.scan_id, "status": scan.result.status if scan.result else scan.request.status, "target": scan.request.target},
                "tags": ["scanner_results", scan.request.target_type],
            }
            for scan in list_scans(self.datasource.environment_id)
        ]
