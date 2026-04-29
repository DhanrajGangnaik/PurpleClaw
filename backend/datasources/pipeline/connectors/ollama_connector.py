from __future__ import annotations

import os

import httpx

from datasources.pipeline.connectors.base import BaseConnector


class OllamaConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        config = self.datasource.config
        url = str(config.get("url", os.getenv("OLLAMA_URL", ""))).strip().rstrip("/")
        timeout = float(config.get("timeout_seconds", os.getenv("OLLAMA_TIMEOUT", "5")))

        if not url:
            return [{"record_type": "status", "metric": "ollama_health", "value": 0, "dimensions": {"status": "not-configured"}}]

        try:
            with httpx.Client(timeout=timeout) as client:
                tags_resp = client.get(f"{url}/api/tags")
                healthy = tags_resp.status_code == 200

                records: list[dict[str, object]] = [
                    {"record_type": "status", "metric": "ollama_health", "value": 1 if healthy else 0,
                     "dimensions": {"status": "healthy" if healthy else "degraded"}},
                ]

                if healthy:
                    models = tags_resp.json().get("models", [])
                    records.append({"record_type": "metric", "metric": "ollama_models_total",
                                    "value": len(models), "dimensions": {}})

                    for model in models[:20]:
                        name = str(model.get("name", "unknown"))
                        size_bytes = model.get("size", 0)
                        records.append({
                            "record_type": "inventory",
                            "metric": "ollama_model",
                            "value": size_bytes,
                            "dimensions": {"name": name, "family": name.split(":")[0]},
                            "tags": ["ollama", "model"],
                        })

                    try:
                        version_resp = client.get(f"{url}/api/version")
                        if version_resp.status_code == 200:
                            version = version_resp.json().get("version", "unknown")
                            records.append({"record_type": "info", "metric": "ollama_version",
                                            "value": version, "dimensions": {"version": str(version)}})
                    except Exception:
                        pass

                return records

        except Exception as exc:
            return [{"record_type": "status", "metric": "ollama_health", "value": 0,
                     "dimensions": {"status": "error", "error": exc.__class__.__name__}}]
