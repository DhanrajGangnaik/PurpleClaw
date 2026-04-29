from __future__ import annotations

import os

import httpx

from datasources.pipeline.connectors.base import BaseConnector


class GrafanaConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        config = self.datasource.config
        url = str(config.get("url", os.getenv("GRAFANA_URL", ""))).strip().rstrip("/")
        api_key = str(config.get("api_key", config.get("token", os.getenv("GRAFANA_API_KEY", "")))).strip()
        timeout = float(config.get("timeout_seconds", os.getenv("GRAFANA_TIMEOUT", "5")))

        if not url:
            return [{"record_type": "status", "metric": "grafana_health", "value": 0, "dimensions": {"status": "not-configured"}}]

        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            with httpx.Client(timeout=timeout) as client:
                health_resp = client.get(f"{url}/api/health", headers=headers)
                healthy = health_resp.status_code == 200

                records: list[dict[str, object]] = [
                    {"record_type": "status", "metric": "grafana_health", "value": 1 if healthy else 0,
                     "dimensions": {"status": "healthy" if healthy else "degraded"}},
                ]

                if healthy and api_key:
                    try:
                        ds_resp = client.get(f"{url}/api/datasources", headers=headers)
                        if ds_resp.status_code == 200:
                            records.append({"record_type": "metric", "metric": "grafana_datasources_total",
                                            "value": len(ds_resp.json()), "dimensions": {}})
                    except Exception:
                        pass

                    try:
                        dash_resp = client.get(f"{url}/api/search?type=dash-db", headers=headers)
                        if dash_resp.status_code == 200:
                            records.append({"record_type": "metric", "metric": "grafana_dashboards_total",
                                            "value": len(dash_resp.json()), "dimensions": {}})
                    except Exception:
                        pass

                    try:
                        alerts_resp = client.get(f"{url}/api/v1/provisioning/alert-rules", headers=headers)
                        if alerts_resp.status_code == 200:
                            rules = alerts_resp.json()
                            records.append({"record_type": "metric", "metric": "grafana_alert_rules_total",
                                            "value": len(rules), "dimensions": {}})
                    except Exception:
                        pass

                return records

        except Exception as exc:
            return [{"record_type": "status", "metric": "grafana_health", "value": 0,
                     "dimensions": {"status": "error", "error": exc.__class__.__name__}}]
