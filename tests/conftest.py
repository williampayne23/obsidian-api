import textwrap
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_vault
from app.services.vault import CachedNote, VaultService


# --- Fake (in-memory) vault service ---


class FakeNote:
    """In-memory note definition for FakeVaultService."""

    def __init__(self, path: str, content: str, metadata: dict | None = None,
                 modified: datetime | None = None):
        self.path = path
        self.content = content
        self.metadata = metadata or {}
        self.title = self.metadata.pop("title", path.rsplit("/", 1)[-1].removesuffix(".md"))
        self.modified = modified or datetime(2026, 3, 18, 12, 0, 0, tzinfo=timezone.utc)
        self.size = len(content.encode())


class FakeVaultService:
    """Drop-in replacement for VaultService backed by an in-memory dict.

    Usage:
        fake = FakeVaultService([
            FakeNote("Daily/note.md", "content", {"tags": ["daily"]}),
        ])
    """

    def __init__(self, notes: list[FakeNote] | None = None):
        self._notes: dict[str, FakeNote] = {}
        for note in notes or []:
            self._notes[note.path] = note

    def _matches_tag(self, metadata: dict, tag: str) -> bool:
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        return tag in tags

    def _in_dir(self, path: str, dir_filter: str) -> bool:
        return path.startswith(dir_filter.rstrip("/") + "/")

    def list_notes(self, dir_filter: str | None = None, tag: str | None = None) -> list[CachedNote]:
        results = []
        for note in self._notes.values():
            if dir_filter and not self._in_dir(note.path, dir_filter):
                continue
            if tag and not self._matches_tag(note.metadata, tag):
                continue
            results.append(CachedNote(
                path=note.path, mtime=note.modified.timestamp(),
                metadata=note.metadata, title=note.title, size=note.size,
            ))
        return sorted(results, key=lambda n: n.path)

    def _modified_dt(self, mtime: float) -> datetime:
        return datetime.fromtimestamp(mtime, tz=timezone.utc)

    def get_note(self, path: str) -> dict | None:
        note = self._notes.get(path)
        if note is None:
            return None
        return {
            "path": note.path,
            "title": note.title,
            "content": note.content,
            "metadata": note.metadata,
            "modified": note.modified,
        }

    def get_changes(self, since: datetime, dir_filter: str | None = None) -> dict:
        since_ts = since.timestamp()
        modified = []
        for note in self._notes.values():
            if dir_filter and not self._in_dir(note.path, dir_filter):
                continue
            if note.modified.timestamp() > since_ts:
                modified.append(note.path)
        return {
            "modified": sorted(modified),
            "deleted": [],
            "checked_at": datetime.now(tz=timezone.utc),
        }

    def search(self, query: str, dir_filter: str | None = None, tag: str | None = None) -> list[dict]:
        query_lower = query.lower()
        results = []
        for note in self._notes.values():
            if dir_filter and not self._in_dir(note.path, dir_filter):
                continue
            if tag and not self._matches_tag(note.metadata, tag):
                continue
            matches = [line.strip() for line in note.content.splitlines()
                       if query_lower in line.lower()]
            if matches:
                results.append({
                    "path": note.path, "title": note.title,
                    "metadata": note.metadata, "modified": note.modified,
                    "matches": matches,
                })
        return results


# --- Sample notes used by both fixture types ---

SAMPLE_NOTES = [
    FakeNote("README.md", "# README\nWelcome to the vault.", {"tags": ["meta"]}),
    FakeNote("Daily/2026-03-17.md", "# 2026-03-17\nWorked on kubernetes setup.",
             {"tags": ["daily"]}, datetime(2026, 3, 17, 9, 0, 0, tzinfo=timezone.utc)),
    FakeNote("Daily/2026-03-18.md", "# 2026-03-18\nDeployed obsidian API.",
             {"tags": ["daily"]}, datetime(2026, 3, 18, 9, 0, 0, tzinfo=timezone.utc)),
    FakeNote("Projects/Homelab.md", "# Homelab\nMy homelab runs kubernetes on Proxmox.",
             {"tags": ["projects", "infra"]}),
    FakeNote("plain.md", "# Plain\nNo frontmatter here."),
]


# --- Fixtures ---


@pytest.fixture
def fake_vault():
    """In-memory FakeVaultService with sample notes."""
    return FakeVaultService(SAMPLE_NOTES)


@pytest.fixture
def fake_client(fake_vault):
    """FastAPI test client backed by FakeVaultService (no filesystem)."""
    from app.main import app

    app.dependency_overrides[get_vault] = lambda: fake_vault

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def vault_dir(tmp_path):
    """Create a temporary vault with sample notes on disk."""
    (tmp_path / "README.md").write_text(textwrap.dedent("""\
        ---
        tags: [meta]
        ---
        # README
        Welcome to the vault.
    """))

    daily = tmp_path / "Daily"
    daily.mkdir()
    (daily / "2026-03-17.md").write_text(textwrap.dedent("""\
        ---
        tags: [daily]
        ---
        # 2026-03-17
        Worked on kubernetes setup.
    """))
    (daily / "2026-03-18.md").write_text(textwrap.dedent("""\
        ---
        tags: [daily]
        ---
        # 2026-03-18
        Deployed obsidian API.
    """))

    projects = tmp_path / "Projects"
    projects.mkdir()
    (projects / "Homelab.md").write_text(textwrap.dedent("""\
        ---
        tags: [projects, infra]
        ---
        # Homelab
        My homelab runs kubernetes on Proxmox.
    """))

    (tmp_path / "plain.md").write_text("# Plain\nNo frontmatter here.\n")

    return tmp_path


@pytest.fixture
def vault_service(vault_dir):
    return VaultService(str(vault_dir))


@pytest.fixture
def client(vault_dir):
    """FastAPI test client with vault pointed at tmp_path (real filesystem)."""
    from app.main import app

    service = VaultService(str(vault_dir))
    app.dependency_overrides[get_vault] = lambda: service

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
