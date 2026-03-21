from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends

from app.dependencies import get_vault
from app.models import VaultEvent
from app.services import webhooks
from app.services.vault import VaultService

router = APIRouter()


@router.post("/reindex")
async def reindex(
    background_tasks: BackgroundTasks,
    vault: VaultService = Depends(get_vault),
):
    """Emit webhook events for all notes, triggering a full re-index."""
    notes = vault.list_notes()
    paths = [n.path for n in notes]
    event = VaultEvent(
        event="modified",
        paths=paths,
        timestamp=datetime.now(tz=timezone.utc),
    )
    background_tasks.add_task(webhooks.dispatch, event)
    return {"queued": len(paths)}
