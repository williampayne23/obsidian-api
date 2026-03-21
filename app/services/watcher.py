"""Filesystem watcher for the Obsidian vault.

Uses watchfiles to detect changes and dispatches events to webhook
subscribers.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

import frontmatter
from watchfiles import Change, awatch

from app.models import VaultEvent
from app.services import webhooks

log = logging.getLogger(__name__)


async def watch_vault(vault_path: str):
    """Watch the vault directory for file changes and dispatch events."""
    vault = Path(vault_path)
    log.info("Starting vault watcher on %s", vault)

    async for changes in awatch(vault, debounce=2000):
        modified = []
        deleted = []

        for change_type, path_str in changes:
            path = Path(path_str)

            # Only watch markdown files
            if path.suffix != ".md":
                continue

            # Skip hidden files/directories (e.g. .obsidian/)
            try:
                rel = path.relative_to(vault)
            except ValueError:
                continue
            if any(part.startswith(".") for part in rel.parts):
                continue

            rel_str = str(rel)

            if change_type == Change.deleted:
                deleted.append(rel_str)
            else:
                modified.append(rel_str)

        now = datetime.now(tz=timezone.utc)

        if modified:
            event = VaultEvent(event="modified", paths=modified, timestamp=now)
            log.info("Vault modified: %d files", len(modified))
            await webhooks.dispatch(event)

        if deleted:
            event = VaultEvent(event="deleted", paths=deleted, timestamp=now)
            log.info("Vault deleted: %d files", len(deleted))
            await webhooks.dispatch(event)
