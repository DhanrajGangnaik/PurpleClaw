from __future__ import annotations

from uuid import uuid4

from core.registry import get_datasource, register_datasource
from datasources.models import DataSource
from datasources.pipeline.connectors.api_connector import APIConnector
from datasources.pipeline.connectors.file_connector import FileConnector
from datasources.pipeline.connectors.grafana_connector import GrafanaConnector
from datasources.pipeline.connectors.inventory_connector import InventoryConnector
from datasources.pipeline.connectors.kubernetes_connector import KubernetesConnector
from datasources.pipeline.connectors.loki_connector import LokiConnector
from datasources.pipeline.connectors.mlflow_connector import MLflowConnector
from datasources.pipeline.connectors.ollama_connector import OllamaConnector
from datasources.pipeline.connectors.prometheus_connector import PrometheusConnector
from datasources.pipeline.connectors.scanner_results_connector import ScannerResultsConnector
from datasources.pipeline.models import DataRecord
from datasources.pipeline.storage import initialize_storage, save_records
from planner.schemas import utc_now


def initialize_pipeline() -> None:
    initialize_storage()
    register_datasource("prometheus", PrometheusConnector)
    register_datasource("loki", LokiConnector)
    register_datasource("api", APIConnector)
    register_datasource("file", FileConnector)
    register_datasource("inventory", InventoryConnector)
    register_datasource("scanner_results", ScannerResultsConnector)
    register_datasource("kubernetes", KubernetesConnector)
    register_datasource("grafana", GrafanaConnector)
    register_datasource("ollama", OllamaConnector)
    register_datasource("mlflow", MLflowConnector)


def ingest_datasource(datasource: DataSource) -> list[DataRecord]:
    connector_cls = get_datasource(datasource.type)
    connector = connector_cls(datasource)
    fetched = connector.fetch()
    records = [
        DataRecord(
            record_id=f"rec-{uuid4().hex[:16]}",
            environment_id=datasource.environment_id,
            datasource_id=datasource.datasource_id,
            record_type=str(item.get("record_type", "metric")),
            metric=str(item.get("metric", datasource.type)),
            value=item.get("value"),
            dimensions=item.get("dimensions", {}) if isinstance(item.get("dimensions"), dict) else {},
            tags=[str(tag) for tag in item.get("tags", [])] if isinstance(item.get("tags"), list) else [datasource.type],
            observed_at=utc_now(),
        )
        for item in fetched
    ]
    return save_records(records)
