from __future__ import annotations

from collectors.prometheus import get_environment_metrics
from datasources.pipeline.connectors.base import BaseConnector


class PrometheusConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        metrics = get_environment_metrics(self.datasource.environment_id)
        target_summary = metrics.get("target_summary", {})
        node_summary = metrics.get("node_summary", {})
        return [
            {"record_type": "metric", "metric": "prometheus_active_targets", "value": target_summary.get("active_target_count", 0), "dimensions": {"status": target_summary.get("status", "unknown")}},
            {"record_type": "metric", "metric": "prometheus_up_targets", "value": target_summary.get("up_target_count", 0), "dimensions": {"status": target_summary.get("status", "unknown")}},
            {"record_type": "metric", "metric": "prometheus_down_targets", "value": target_summary.get("down_target_count", 0), "dimensions": {"status": target_summary.get("status", "unknown")}},
            {"record_type": "metric", "metric": "node_cpu_pressure_percent", "value": node_summary.get("cpu_pressure_percent"), "dimensions": {"status": node_summary.get("status", "unknown")}},
        ]
