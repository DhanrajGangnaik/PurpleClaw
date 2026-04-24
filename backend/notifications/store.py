from __future__ import annotations

from notifications.models import WebhookConfig, WebhookConfigCreate

_webhooks: dict[str, WebhookConfig] = {}


def initialize_notifications() -> None:
    pass


def list_webhooks() -> list[WebhookConfig]:
    return sorted(_webhooks.values(), key=lambda w: w.created_at)


def get_webhook(webhook_id: str) -> WebhookConfig | None:
    return _webhooks.get(webhook_id)


def create_webhook(payload: WebhookConfigCreate) -> WebhookConfig:
    webhook = WebhookConfig(
        name=payload.name,
        type=payload.type,
        url=payload.url,
        enabled=payload.enabled,
        events=payload.events,
    )
    _webhooks[webhook.webhook_id] = webhook
    return webhook


def update_webhook(webhook_id: str, payload: WebhookConfigCreate) -> WebhookConfig | None:
    webhook = _webhooks.get(webhook_id)
    if webhook is None:
        return None
    updated = webhook.model_copy(update=payload.model_dump())
    _webhooks[webhook_id] = updated
    return updated


def delete_webhook(webhook_id: str) -> bool:
    return _webhooks.pop(webhook_id, None) is not None
