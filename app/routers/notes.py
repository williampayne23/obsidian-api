from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_vault
from app.models import NoteDetail, NoteListResponse, NoteSummary
from app.services.vault import VaultService

router = APIRouter()


@router.get("/notes", response_model=NoteListResponse)
def list_notes(
    vault: VaultService = Depends(get_vault),
    dir: str | None = Query(None, description="Filter by subdirectory"),
    tag: str | None = Query(None, description="Filter by frontmatter tag"),
):
    notes = vault.list_notes(dir_filter=dir, tag=tag)
    return NoteListResponse(
        notes=[
            NoteSummary(
                path=n.path,
                title=n.title,
                metadata=n.metadata,
                modified=vault._modified_dt(n.mtime),
                size=n.size,
            )
            for n in notes
        ],
        total=len(notes),
    )


@router.get("/notes/{path:path}", response_model=NoteDetail)
def get_note(path: str, vault: VaultService = Depends(get_vault)):
    note = vault.get_note(path)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteDetail(**note)
