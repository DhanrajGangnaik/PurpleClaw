from __future__ import annotations

import json
import logging

import httpx

from notifications.models import WebhookConfig, WebhookEvent
from notifications.store import list_webhooks

logger = logging.getLogger("purpleclaw.notifications")

_SEVERITY_COLORS = {
    "critical": "#DC2626",
    "high": "#EA580C",
    "medium": "#D97706",
    "low": "#65A30D",
    "info": "#2563EB",
}


def send_event(event: WebhookEvent) -> None:
    webhooks = [w for w in list_webhooks() if w.enabled and (not w.events or event.event_type in w.events)]
    if not webhooks:
        return
    for webhook in webhooks:
        try:
            _dispatch(webhook, event)
        except Exception as exc:
            logger.warning("event=webhook_failed webhook_id=%s error=%s", webhook.webhook_id, exc)


def _dispatch(webhook: WebhookConfig, event: WebhookEvent) -> None:
    if webhook.type == "slack":
        body = _build_slack_payload(event)
    elif webhook.type == "teams":
        body = _build_teams_payload(event)
    else:
        body = _build_generic_payload(event)

    response = httpx.post(webhook.url, json=body, timeout=8)
    response.raise_for_status()
    logger.info(
        "event=webhook_sent webhook_id=%s event_type=%s status=%d",
        webhook.webhook_id,
        event.event_type,
        response.status_code,
    )


def _build_slack_payload(event: WebhookEvent) -> dict[str, object]:
    color = _SEVERITY_COLORS.get(event.severity, "#6B7280")
    return {
        "attachments": [
            {
                "color": color,
                "title": f"[PurpleClaw] {event.title}",
                "text": event.body,
                "fields": [
                    {"title": "Event", "value": event.event_type, "short": True},
                    {"title": "Severity", "value": event.severity.upper(), "short": True},
                    {"title": "Environment", "value": event.environment_id, "short": True},
                ],
                "footer": "PurpleClaw Security Platform",
            }
        ]
    }


def _build_teams_payload(event: WebhookEvent) -> dict[str, object]:
    color = _SEVERITY_COLORS.get(event.severity, "#6B7280").lstrip("#")
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": event.title,
        "sections": [
            {
                "activityTitle": f"**[PurpleClaw]** {event.title}",
                "activitySubtitle": f"Event: `{event.event_type}` | Severity: **{event.severity.upper()}**",
                "activityText": event.body,
                "facts": [
                    {"name": "Environment", "value": event.environment_id},
                    {"name": "Severity", "value": event.severity.upper()},
                ],
            }
        ],
    }


def _build_generic_payload(event: WebhookEvent) -> dict[str, object]:
    return {
        "source": "purpleclaw",
        "event_type": event.event_type,
        "environment_id": event.environment_id,
        "severity": event.severity,
        "title": event.title,
        "body": event.body,
        "metadata": event.metadata,
    }
