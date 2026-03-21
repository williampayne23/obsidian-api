"""Redis Streams integration for the embed queue.

Publishes note change events so the embed worker can process them.
Gracefully degrades if Redis is unavailable.
"""

import logging

import redis

from app.config import settings
from app.models import ChangeSet

log = logging.getLogger(__name__)

STREAM_NAME = "embed_queue"

_client: redis.Redis | None = None


def _get_client() -> redis.Redis | None:
    """Get or create Redis client. Returns None if Redis is not configured."""
    global _client
    if not settings.redis_host:
        return None
    if _client is None:
        _client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password or None,
            decode_responses=True,
            socket_connect_timeout=2,
        )
    return _client


def publish_changes(changeset: ChangeSet) -> int:
    """Publish modified/deleted paths to the embed queue. Returns count published."""
    client = _get_client()
    if client is None:
        return 0

    count = 0
    for path in changeset.modified:
        client.xadd(STREAM_NAME, {"action": "upsert", "path": path})
        count += 1

    for path in changeset.deleted:
        client.xadd(STREAM_NAME, {"action": "delete", "path": path})
        count += 1

    if count:
        log.info("Published %d events to %s", count, STREAM_NAME)
    return count


def publish_paths(paths: list[str], action: str = "upsert") -> int:
    """Publish a list of paths to the embed queue. Returns count published."""
    client = _get_client()
    if client is None:
        raise RuntimeError("Redis is not configured")

    count = 0
    for path in paths:
        client.xadd(STREAM_NAME, {"action": action, "path": path})
        count += 1

    log.info("Published %d %s events to %s", count, action, STREAM_NAME)
    return count
