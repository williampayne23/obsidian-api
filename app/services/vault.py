import os
from datetime import datetime, timezone
from pathlib import Path

import frontmatter


class CachedNote:
    def __init__(self, path: str, mtime: float, metadata: dict, title: str, size: int):
        self.path = path
        self.mtime = mtime
        self.metadata = metadata
        self.title = title
        self.size = size


class VaultService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self._cache: dict[str, CachedNote] = {}

    def _relative_path(self, abs_path: Path) -> str:
        return str(abs_path.relative_to(self.vault_path))

    def _mtime(self, abs_path: Path) -> float:
        return abs_path.stat().st_mtime

    def _modified_dt(self, mtime: float) -> datetime:
        return datetime.fromtimestamp(mtime, tz=timezone.utc)

    def _parse_note(self, abs_path: Path) -> CachedNote:
        rel = self._relative_path(abs_path)
        mtime = self._mtime(abs_path)

        cached = self._cache.get(rel)
        if cached and cached.mtime == mtime:
            return cached

        try:
            post = frontmatter.load(str(abs_path))
            metadata = dict(post.metadata)
        except Exception:
            metadata = {}

        title = metadata.pop("title", abs_path.stem)
        size = abs_path.stat().st_size

        cached = CachedNote(path=rel, mtime=mtime, metadata=metadata, title=title, size=size)
        self._cache[rel] = cached
        return cached

    def _iter_notes(self, dir_filter: str | None = None) -> list[Path]:
        base = self.vault_path
        if dir_filter:
            base = base / dir_filter
            if not base.is_dir():
                return []
        return sorted(base.rglob("*.md"))

    def _matches_tag(self, metadata: dict, tag: str) -> bool:
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        return tag in tags

    def list_notes(
        self, dir_filter: str | None = None, tag: str | None = None
    ) -> list[CachedNote]:
        results = []
        for abs_path in self._iter_notes(dir_filter):
            note = self._parse_note(abs_path)
            if tag and not self._matches_tag(note.metadata, tag):
                continue
            results.append(note)
        return results

    def get_note(self, path: str) -> dict | None:
        abs_path = self.vault_path / path
        if not abs_path.is_file():
            return None
        # Prevent path traversal
        try:
            abs_path.resolve().relative_to(self.vault_path.resolve())
        except ValueError:
            return None

        try:
            post = frontmatter.load(str(abs_path))
            metadata = dict(post.metadata)
            content = post.content
        except Exception:
            metadata = {}
            content = abs_path.read_text(encoding="utf-8", errors="replace")

        title = metadata.pop("title", abs_path.stem)
        mtime = self._mtime(abs_path)

        return {
            "path": path,
            "title": title,
            "content": content,
            "metadata": metadata,
            "modified": self._modified_dt(mtime),
        }

    def get_changes(
        self, since: datetime, dir_filter: str | None = None
    ) -> dict:
        since_ts = since.timestamp()
        modified = []
        for abs_path in self._iter_notes(dir_filter):
            if self._mtime(abs_path) > since_ts:
                modified.append(self._relative_path(abs_path))

        return {
            "modified": modified,
            "deleted": [],
            "checked_at": datetime.now(tz=timezone.utc),
        }

    def search(
        self,
        query: str,
        dir_filter: str | None = None,
        tag: str | None = None,
    ) -> list[dict]:
        query_lower = query.lower()
        results = []
        for abs_path in self._iter_notes(dir_filter):
            note = self._parse_note(abs_path)
            if tag and not self._matches_tag(note.metadata, tag):
                continue

            content = abs_path.read_text(encoding="utf-8", errors="replace")
            matches = []
            for line in content.splitlines():
                if query_lower in line.lower():
                    matches.append(line.strip())
            if matches:
                results.append(
                    {
                        "path": note.path,
                        "title": note.title,
                        "metadata": note.metadata,
                        "modified": self._modified_dt(note.mtime),
                        "matches": matches,
                    }
                )
        return results

    def check_frontmatter(self, dir_filter: str | None = None) -> list[dict]:
        """Scan for notes with malformed YAML frontmatter."""
        issues = []
        for abs_path in self._iter_notes(dir_filter):
            rel = self._relative_path(abs_path)
            try:
                post = frontmatter.load(str(abs_path))
                if not isinstance(post.metadata, dict):
                    issues.append({
                        "path": rel,
                        "error": f"Frontmatter parsed as {type(post.metadata).__name__}, expected mapping",
                    })
            except Exception as e:
                issues.append({
                    "path": rel,
                    "error": str(e),
                })
        return issues
