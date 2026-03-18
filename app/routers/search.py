from fastapi import APIRouter, Depends, Query

from app.dependencies import get_vault
from app.models import SearchResponse, SearchResult
from app.services.vault import VaultService

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
def search_notes(
    vault: VaultService = Depends(get_vault),
    q: str = Query(..., description="Search query"),
    dir: str | None = Query(None, description="Filter by subdirectory"),
    tag: str | None = Query(None, description="Filter by frontmatter tag"),
):
    results = vault.search(query=q, dir_filter=dir, tag=tag)
    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )
