from fastapi import APIRouter, Depends, Query

from app.dependencies import get_vault
from app.models import FrontmatterCheckResponse, FrontmatterIssue
from app.services.vault import VaultService

router = APIRouter(prefix="/diagnostics")


@router.get("/frontmatter", response_model=FrontmatterCheckResponse)
def check_frontmatter(
    vault: VaultService = Depends(get_vault),
    dir: str | None = Query(None, description="Filter by subdirectory"),
):
    issues = vault.check_frontmatter(dir_filter=dir)
    all_notes = vault.list_notes(dir_filter=dir)
    return FrontmatterCheckResponse(
        issues=[FrontmatterIssue(**i) for i in issues],
        total=len(issues),
        scanned=len(all_notes),
    )
