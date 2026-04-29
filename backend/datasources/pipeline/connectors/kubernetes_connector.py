from __future__ import annotations

import os

import httpx

from datasources.pipeline.connectors.base import BaseConnector


class KubernetesConnector(BaseConnector):
    def fetch(self) -> list[dict[str, object]]:
        config = self.datasource.config
        url = str(config.get("url", os.getenv("KUBERNETES_URL", ""))).strip().rstrip("/")
        token = str(config.get("token", os.getenv("KUBERNETES_TOKEN", ""))).strip()
        timeout = float(config.get("timeout_seconds", os.getenv("KUBERNETES_TIMEOUT", "5")))
        raw_verify = str(config.get("verify_ssl", os.getenv("KUBERNETES_VERIFY_SSL", "true"))).lower()
        verify_ssl = raw_verify not in ("false", "0", "no")

        if not url:
            return [{"record_type": "status", "metric": "kubernetes_health", "value": 0, "dimensions": {"status": "not-configured"}}]

        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            with httpx.Client(verify=verify_ssl, timeout=timeout) as client:
                health_resp = client.get(f"{url}/healthz", headers=headers)
                healthy = health_resp.status_code == 200

                records: list[dict[str, object]] = [
                    {"record_type": "status", "metric": "kubernetes_health", "value": 1 if healthy else 0,
                     "dimensions": {"status": "healthy" if healthy else "degraded"}},
                ]

                if healthy:
                    try:
                        nodes_resp = client.get(f"{url}/api/v1/nodes", headers=headers)
                        if nodes_resp.status_code == 200:
                            nodes = nodes_resp.json().get("items", [])
                            ready = sum(
                                1 for n in nodes
                                if any(
                                    c.get("type") == "Ready" and c.get("status") == "True"
                                    for c in n.get("status", {}).get("conditions", [])
                                )
                            )
                            records += [
                                {"record_type": "metric", "metric": "kubernetes_nodes_total", "value": len(nodes), "dimensions": {}},
                                {"record_type": "metric", "metric": "kubernetes_nodes_ready", "value": ready, "dimensions": {}},
                                {"record_type": "metric", "metric": "kubernetes_nodes_unready", "value": len(nodes) - ready, "dimensions": {}},
                            ]
                    except Exception:
                        pass

                    try:
                        pods_resp = client.get(f"{url}/api/v1/pods", headers=headers)
                        if pods_resp.status_code == 200:
                            pods = pods_resp.json().get("items", [])
                            by_phase: dict[str, int] = {}
                            for pod in pods:
                                phase = pod.get("status", {}).get("phase", "Unknown")
                                by_phase[phase] = by_phase.get(phase, 0) + 1
                            records += [
                                {"record_type": "metric", "metric": "kubernetes_pods_total", "value": len(pods), "dimensions": {}},
                                {"record_type": "metric", "metric": "kubernetes_pods_running", "value": by_phase.get("Running", 0), "dimensions": {"phase": "Running"}},
                                {"record_type": "metric", "metric": "kubernetes_pods_failed", "value": by_phase.get("Failed", 0), "dimensions": {"phase": "Failed"}},
                                {"record_type": "metric", "metric": "kubernetes_pods_pending", "value": by_phase.get("Pending", 0), "dimensions": {"phase": "Pending"}},
                            ]
                    except Exception:
                        pass

                return records

        except Exception as exc:
            return [{"record_type": "status", "metric": "kubernetes_health", "value": 0,
                     "dimensions": {"status": "error", "error": exc.__class__.__name__}}]
