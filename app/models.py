from datetime import datetime

from pydantic import BaseModel


class NoteSummary(BaseModel):
    path: str
    title: str
    metadata: dict
    modified: datetime
    size: int


class NoteDetail(BaseModel):
    path: str
    title: str
    content: str
    metadata: dict
    modified: datetime


class NoteListResponse(BaseModel):
    notes: list[NoteSummary]
    total: int


class ChangeSet(BaseModel):
    modified: list[str]
    deleted: list[str]
    checked_at: datetime


class SearchResult(BaseModel):
    path: str
    title: str
    metadata: dict
    modified: datetime
    matches: list[str]


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


class FrontmatterIssue(BaseModel):
    path: str
    error: str


class FrontmatterCheckResponse(BaseModel):
    issues: list[FrontmatterIssue]
    total: int
    scanned: int
