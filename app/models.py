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


class WebhookSubscription(BaseModel):
    url: str
    events: list[str] = ["modified", "deleted"]
    secret: str | None = None


class WebhookSubscriptionResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    created_at: datetime


class VaultEvent(BaseModel):
    event: str  # "modified" or "deleted"
    paths: list[str]
    timestamp: datetime
