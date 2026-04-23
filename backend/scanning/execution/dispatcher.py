from __future__ import annotations

from core.registry import get_scan, register_scan
from scanning.execution import implementations


def initialize_dispatcher() -> None:
    register_scan("inventory_match", implementations.run_inventory_match)
    register_scan("tls_check", implementations.run_tls_check)
    register_scan("service_detection", implementations.run_service_detection)
    register_scan("header_analysis", implementations.run_header_analysis)
    register_scan("config_audit", implementations.run_config_audit)
    register_scan("exposure_review", implementations.run_exposure_review)
    register_scan("telemetry_gap_check", implementations.run_telemetry_gap_check)


def dispatch_scan(scan_type: str):
    return get_scan(scan_type)
