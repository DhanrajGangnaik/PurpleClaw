from __future__ import annotations

import json
from typing import Any


ENTITY_TABLES = {
    "environments": "environment_id",
    "assets": "id",
    "findings": "id",
    "remediations": "id",
    "inventory": "inventory_id",
    "telemetry_summaries": "id",
    "automation_runs": "run_id",
    "alerts": "alert_id",
    "signals": "signal_id",
    "intelligence_update_runs": "run_id",
}


def json_dumps(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("database payload must be a non-empty JSON object")
    return json.dumps(payload)
