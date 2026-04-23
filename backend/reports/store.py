from __future__ import annotations

import textwrap
from pathlib import Path
from uuid import uuid4

from persistence.database import db
from persistence.store import get_environment
from reports.renderer import render_report_preview
from reports.models import GenerateReportRequest, GeneratedReport, ReportTemplate
from templates import DEFAULT_REPORT_SECTIONS


_REPORT_TEMPLATES: dict[str, ReportTemplate] = {}
_GENERATED_REPORTS: dict[str, GeneratedReport] = {}
_REPORT_DIR = Path(__file__).resolve().parents[1] / "data" / "reports"


def initialize_reports() -> None:
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if db.enabled:
        for record in db.list_records("report_templates", ReportTemplate):
            _REPORT_TEMPLATES[record.template_id] = record
        for record in db.list_records("generated_reports", GeneratedReport):
            _GENERATED_REPORTS[record.report_id] = record

    default_template = ReportTemplate(
        template_id="default-assessment",
        name="Assessment Executive Template",
        description="Industry-style assessment report covering risk, exposure, and remediation.",
        sections=DEFAULT_REPORT_SECTIONS,
    )
    if default_template.template_id not in _REPORT_TEMPLATES:
        _REPORT_TEMPLATES[default_template.template_id] = default_template
        if db.enabled:
            db.upsert_many("report_templates", [default_template])


def list_report_templates() -> list[ReportTemplate]:
    return sorted(_REPORT_TEMPLATES.values(), key=lambda item: item.name.lower())


def list_reports(environment_id: str | None = None) -> list[GeneratedReport]:
    records = _GENERATED_REPORTS.values()
    if environment_id:
        records = [report for report in records if report.environment_id == environment_id]
    return sorted(records, key=lambda item: item.generated_at, reverse=True)


def get_report(report_id: str) -> GeneratedReport | None:
    return _GENERATED_REPORTS.get(report_id)


def generate_report(payload: GenerateReportRequest) -> GeneratedReport:
    if get_environment(payload.environment_id) is None:
        raise ValueError("Environment not found")

    template = _REPORT_TEMPLATES.get(payload.template_id or "default-assessment")
    if template is None:
        raise ValueError("Report template not found")

    report_id = f"report-{uuid4().hex[:12]}"
    file_path = _REPORT_DIR / f"{report_id}.pdf"
    preview = render_report_preview(payload, template)
    metadata = {"preview": preview, "template": template.model_dump(mode="json")}

    try:
        _render_pdf(file_path, payload.title, preview["sections"])
        status = "ready"
        stored_path = str(file_path)
    except Exception as exc:  # noqa: BLE001
        status = "failed"
        stored_path = None
        metadata["error"] = str(exc)

    report = GeneratedReport(
        report_id=report_id,
        environment_id=payload.environment_id,
        title=payload.title,
        generated_from=payload.generated_from,
        source_id=payload.source_id,
        status=status,
        file_path=stored_path,
        metadata=metadata,
    )
    _GENERATED_REPORTS[report.report_id] = report
    if db.enabled:
        db.upsert_many("generated_reports", [report])
    return report


def preview_report(payload: GenerateReportRequest) -> dict[str, object]:
    template = _REPORT_TEMPLATES.get(payload.template_id or "default-assessment")
    if template is None:
        raise ValueError("Report template not found")
    return render_report_preview(payload, template)


def _render_pdf(path: Path, title: str, sections: list[dict[str, object]]) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PurpleClawTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, textColor=colors.HexColor("#2E1065"), spaceAfter=16)
    section_style = ParagraphStyle("PurpleClawSection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, textColor=colors.HexColor("#111827"), spaceBefore=12, spaceAfter=8)
    body_style = ParagraphStyle("PurpleClawBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#334155"))

    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42)
    story = [Paragraph(title, title_style), Paragraph("PurpleClaw Defensive Assessment Report", body_style), Spacer(1, 12)]

    executive = next((section for section in sections if section.get("name") == "Executive Summary"), {"content": {}})
    metrics = executive.get("content", {}).get("metrics", {}) if isinstance(executive.get("content"), dict) else {}
    summary_table = Table(
        [
            ["Assets", str(metrics.get("asset_count", 0)), "Findings", str(metrics.get("finding_count", 0))],
            ["Critical Findings", str(metrics.get("critical_findings", 0)), "Source", "PurpleClaw"],
        ],
        colWidths=[100, 80, 120, 80],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)

    for section in sections:
        story.append(Spacer(1, 12))
        story.append(Paragraph(str(section.get("name", "Section")), section_style))
        story.append(Paragraph(_render_section_content(section.get("content")), body_style))

    doc.build(story)

def _render_section_content(payload: object) -> str:
    if isinstance(payload, dict):
        lines: list[str] = []
        for key, value in payload.items():
            if isinstance(value, list):
                rendered = _render_section_content(value)
                lines.append(f"<b>{key.replace('_', ' ').title()}:</b> {rendered}")
            else:
                lines.append(f"<b>{key.replace('_', ' ').title()}:</b> {value}")
        return "<br/>".join(textwrap.shorten(line, width=220, placeholder="...") for line in lines)
    if isinstance(payload, list):
        rendered_items = []
        for item in payload[:8]:
            if isinstance(item, dict):
                fragments = [f"{key.replace('_', ' ').title()}: {value}" for key, value in item.items() if value not in (None, [], "")]
                rendered_items.append("- " + " | ".join(fragments))
            else:
                rendered_items.append(f"- {item}")
        return "<br/>".join(textwrap.shorten(item, width=220, placeholder="...") for item in rendered_items) or "No items available."
    return str(payload or "No content available.")
