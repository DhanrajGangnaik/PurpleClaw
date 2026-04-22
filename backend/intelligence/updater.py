from __future__ import annotations

from collections import Counter

from intelligence.models import IntelTrend, ThreatAdvisory
from posture.models import Asset, Finding, InventoryRecord


def relevant_technologies(inventory_records: list[InventoryRecord], assets: list[Asset]) -> set[str]:
    """Return technology names observed in approved inventory and asset metadata."""

    technologies = {record.component_name.lower() for record in inventory_records}
    for asset in assets:
        technologies.update(tag.lower() for tag in asset.tags)
        technologies.update(source.lower() for source in asset.telemetry_sources)
        technologies.add(asset.asset_type.lower())
    return technologies


def match_advisories(advisories: list[ThreatAdvisory], technologies: set[str]) -> list[ThreatAdvisory]:
    """Return advisories whose affected products are present in approved inventory."""

    return [
        advisory
        for advisory in advisories
        if any(product.lower() in technologies for product in advisory.affected_products)
    ]


def match_trends(trends: list[IntelTrend], technologies: set[str]) -> list[IntelTrend]:
    """Return trends whose technologies are present in approved inventory or assets."""

    return [
        trend
        for trend in trends
        if any(technology.lower() in technologies for technology in trend.affected_technologies)
    ]


def reprioritize_findings(findings: list[Finding], advisories: list[ThreatAdvisory], trends: list[IntelTrend]) -> list[Finding]:
    """Return deterministic intelligence-enriched finding copies sorted by score."""

    advisory_terms = _terms_from_advisories(advisories)
    trend_terms = _terms_from_trends(trends)
    output: list[Finding] = []
    for finding in findings:
        haystack = " ".join(
            [
                finding.title,
                finding.category,
                finding.evidence_summary,
                finding.affected_component or "",
            ]
        ).lower()
        matched_advisory_terms = [term for term in advisory_terms if term in haystack]
        matched_trend_terms = [term for term in trend_terms if term in haystack]
        if not matched_advisory_terms and not matched_trend_terms:
            continue

        boost = min(15, (len(set(matched_advisory_terms)) * 7) + (len(set(matched_trend_terms)) * 4))
        output.append(
            finding.model_copy(
                update={
                    "score": min(100, finding.score + boost),
                    "evidence_summary": f"{finding.evidence_summary} Intelligence context matched current advisory or trend terms.",
                }
            )
        )
    return sorted(output, key=lambda finding: finding.score, reverse=True)


def current_risk_summaries(advisories: list[ThreatAdvisory], trends: list[IntelTrend]) -> list[str]:
    """Create short current risk summaries from matched advisories and trends."""

    categories = Counter([item.category for item in advisories] + [item.category for item in trends])
    return [f"{category}: {count} relevant intelligence item(s)" for category, count in categories.most_common()]


def _terms_from_advisories(advisories: list[ThreatAdvisory]) -> set[str]:
    terms: set[str] = set()
    for advisory in advisories:
        terms.update(product.lower() for product in advisory.affected_products)
        terms.update(tag.lower() for tag in advisory.tags)
    return {term for term in terms if term}


def _terms_from_trends(trends: list[IntelTrend]) -> set[str]:
    terms: set[str] = set()
    for trend in trends:
        terms.update(technology.lower() for technology in trend.affected_technologies)
        terms.add(trend.category.lower())
    return {term for term in terms if term}
