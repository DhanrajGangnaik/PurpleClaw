from __future__ import annotations

from collectors.loki import get_environment_log_metrics
from datasources.pipeline.connectors.base import BaseConnector


class LokiConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        metrics = get_environment_log_metrics(self.datasource.environment_id)
        log_summary = metrics.get("log_source_summary", {})
        auth_summary = metrics.get("auth_failure_summary", {})
        return [
            {"record_type": "event", "metric": "loki_log_sources", "value": log_summary.get("source_count", 0), "dimensions": {"status": log_summary.get("status", "unknown")}},
            {"record_type": "event", "metric": "loki_log_events", "value": log_summary.get("event_count", 0), "dimensions": {"status": log_summary.get("status", "unknown")}},
            {"record_type": "event", "metric": "loki_auth_failures", "value": auth_summary.get("event_count", 0), "dimensions": {"status": auth_summary.get("status", "unknown")}},
        ]
