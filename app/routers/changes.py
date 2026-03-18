from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_vault
from app.models import ChangeSet
from app.services.vault import VaultService

router = APIRouter()


@router.get("/changes", response_model=ChangeSet)
def get_changes(
    vault: VaultService = Depends(get_vault),
    since: datetime = Query(..., description="ISO timestamp to check changes from"),
    dir: str | None = Query(None, description="Filter by subdirectory"),
):
    changes = vault.get_changes(since=since, dir_filter=dir)
    return ChangeSet(**changes)
