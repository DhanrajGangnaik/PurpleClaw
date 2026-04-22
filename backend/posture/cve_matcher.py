from __future__ import annotations

from collections.abc import Mapping

from planner.schemas import utc_now
from posture.cve_data import SEEDED_CVES, CveRecord
from posture.models import DataSource, Finding, InventoryRecord
from posture.scoring import calculate_finding_score


def match_inventory_to_cves(inventory_records: list[InventoryRecord], asset_context: Mapping[str, object] | None = None) -> list[Finding]:
    """Match known inventory records against the seeded CVE knowledge base."""

    assets = asset_context or {}
    findings: list[Finding] = []
    for record in inventory_records:
        for cve in SEEDED_CVES:
            if _matches(record, cve):
                finding = _finding_from_match(record, cve)
                asset = assets.get(record.asset_id) if isinstance(assets, Mapping) else None
                findings.append(finding.model_copy(update={"score": calculate_finding_score(finding, asset)}))
    return findings


def _matches(record: InventoryRecord, cve: CveRecord) -> bool:
    return record.component_name.lower() == cve.component_name.lower() and record.version in cve.vulnerable_versions


def _finding_from_match(record: InventoryRecord, cve: CveRecord) -> Finding:
    now = utc_now()
    return Finding(
        id=f"cve-{record.environment_id}-{record.asset_id}-{record.component_name}-{cve.cve_id}".lower(),
        environment_id=record.environment_id,
        asset_id=record.asset_id,
        title=f"{cve.cve_id}: {cve.title}",
        severity=cve.severity,
        category="vulnerability",
        status="open",
        exposure="seeded CVE match from approved inventory",
        evidence_summary=f"{record.component_name} {record.version} on asset {record.asset_id} matches {cve.cve_id}. {cve.description}",
        verification=cve.recommendation,
        confidence="high",
        affected_component=cve.affected_component,
        source=DataSource.TRACKING if record.source == DataSource.TRACKING else DataSource.DEMO,
        opened_at=now,
        updated_at=now,
    )
