from fastapi import APIRouter, HTTPException

from app.models import WebhookSubscription, WebhookSubscriptionResponse
from app.services import webhooks

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("", response_model=list[WebhookSubscriptionResponse])
def list_webhooks():
    return webhooks.list_subscriptions()


@router.post("", response_model=WebhookSubscriptionResponse, status_code=201)
def create_webhook(sub: WebhookSubscription):
    return webhooks.subscribe(sub)


@router.delete("/{sub_id}", status_code=204)
def delete_webhook(sub_id: str):
    if not webhooks.unsubscribe(sub_id):
        raise HTTPException(status_code=404, detail="Webhook not found")
