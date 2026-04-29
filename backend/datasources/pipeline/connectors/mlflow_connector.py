from __future__ import annotations

import os

import httpx

from datasources.pipeline.connectors.base import BaseConnector


class MLflowConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        config = self.datasource.config
        url = str(config.get("url", os.getenv("MLFLOW_URL", ""))).strip().rstrip("/")
        timeout = float(config.get("timeout_seconds", os.getenv("MLFLOW_TIMEOUT", "5")))
        token = str(config.get("token", os.getenv("MLFLOW_TOKEN", ""))).strip()

        if not url:
            return [{"record_type": "status", "metric": "mlflow_health", "value": 0, "dimensions": {"status": "not-configured"}}]

        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            with httpx.Client(timeout=timeout) as client:
                health_resp = client.get(f"{url}/health")
                healthy = health_resp.status_code == 200

                records: list[dict[str, object]] = [
                    {"record_type": "status", "metric": "mlflow_health", "value": 1 if healthy else 0,
                     "dimensions": {"status": "healthy" if healthy else "degraded"}},
                ]

                if healthy:
                    try:
                        exp_resp = client.get(
                            f"{url}/api/2.0/mlflow/experiments/search",
                            headers=headers,
                            params={"max_results": "1000"},
                        )
                        if exp_resp.status_code == 200:
                            experiments = exp_resp.json().get("experiments", [])
                            records.append({"record_type": "metric", "metric": "mlflow_experiments_total",
                                            "value": len(experiments), "dimensions": {}})
                    except Exception:
                        pass

                    try:
                        runs_resp = client.post(
                            f"{url}/api/2.0/mlflow/runs/search",
                            headers=headers,
                            json={"max_results": 200},
                        )
                        if runs_resp.status_code == 200:
                            runs = runs_resp.json().get("runs", [])
                            active = sum(1 for r in runs if r.get("info", {}).get("status") == "RUNNING")
                            failed = sum(1 for r in runs if r.get("info", {}).get("status") == "FAILED")
                            records += [
                                {"record_type": "metric", "metric": "mlflow_runs_total", "value": len(runs), "dimensions": {}},
                                {"record_type": "metric", "metric": "mlflow_runs_active", "value": active, "dimensions": {"status": "RUNNING"}},
                                {"record_type": "metric", "metric": "mlflow_runs_failed", "value": failed, "dimensions": {"status": "FAILED"}},
                            ]
                    except Exception:
                        pass

                return records

        except Exception as exc:
            return [{"record_type": "status", "metric": "mlflow_health", "value": 0,
                     "dimensions": {"status": "error", "error": exc.__class__.__name__}}]
