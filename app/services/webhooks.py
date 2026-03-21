"""Webhook subscription manager.

Stores subscriptions in memory — consumers re-register on pod restart.
Dispatches vault events to subscribers asynchronously.
"""

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone

import httpx

from app.models import VaultEvent, WebhookSubscription, WebhookSubscriptionResponse

log = logging.getLogger(__name__)

_subscriptions: dict[str, tuple[WebhookSubscription, datetime]] = {}


def subscribe(sub: WebhookSubscription) -> WebhookSubscriptionResponse:
    sub_id = str(uuid.uuid4())[:8]
    now = datetime.now(tz=timezone.utc)
    _subscriptions[sub_id] = (sub, now)
    log.info("Webhook registered: %s -> %s (events: %s)", sub_id, sub.url, sub.events)
    return WebhookSubscriptionResponse(
        id=sub_id, url=sub.url, events=sub.events, created_at=now
    )


def unsubscribe(sub_id: str) -> bool:
    if sub_id in _subscriptions:
        del _subscriptions[sub_id]
        log.info("Webhook unregistered: %s", sub_id)
        return True
    return False


def list_subscriptions() -> list[WebhookSubscriptionResponse]:
    return [
        WebhookSubscriptionResponse(id=sub_id, url=sub.url, events=sub.events, created_at=created)
        for sub_id, (sub, created) in _subscriptions.items()
    ]


async def dispatch(event: VaultEvent):
    """Send event to all matching subscribers."""
    if not _subscriptions:
        return

    async with httpx.AsyncClient(timeout=10) as client:
        for sub_id, (sub, _) in list(_subscriptions.items()):
            if event.event not in sub.events:
                continue
            try:
                payload = event.model_dump_json()
                headers = {"Content-Type": "application/json"}
                if sub.secret:
                    sig = hmac.new(
                        sub.secret.encode(), payload.encode(), hashlib.sha256
                    ).hexdigest()
                    headers["X-Webhook-Signature"] = sig
                resp = await client.post(sub.url, content=payload, headers=headers)
                if resp.status_code >= 400:
                    log.warning("Webhook %s returned %d", sub_id, resp.status_code)
            except httpx.HTTPError as e:
                log.warning("Webhook %s delivery failed: %s", sub_id, e)
