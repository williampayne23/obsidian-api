from fastapi import APIRouter, Depends

from app.dependencies import get_vault
from app.services.redis_queue import publish_paths
from app.services.vault import VaultService

router = APIRouter()


@router.post("/reindex")
def reindex(vault: VaultService = Depends(get_vault)):
    """Push all note paths to the embed queue for bulk re-embedding."""
    notes = vault.list_notes()
    paths = [n.path for n in notes]
    count = publish_paths(paths, action="upsert")
    return {"queued": count}
