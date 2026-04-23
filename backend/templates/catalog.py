from __future__ import annotations

DEFAULT_REPORT_SECTIONS = [
    "Executive Summary",
    "Environment Overview",
    "Key Findings",
    "Prioritized Risks",
    "Risky Assets",
    "Vulnerability Matches",
    "Recommended Remediations",
    "Telemetry / Monitoring Coverage",
    "Appendix",
]

SUPPORTED_WIDGET_TYPES = {
    "metric_card",
    "findings_table",
    "risky_assets",
    "telemetry_summary",
    "alerts_summary",
    "signals_summary",
    "vulnerabilities_summary",
    "service_health",
    "report_list",
}

SUPPORTED_SCAN_TYPES = {
    "inventory_match",
    "tls_check",
    "service_detection",
    "header_analysis",
    "config_audit",
    "exposure_review",
    "telemetry_gap_check",
}
