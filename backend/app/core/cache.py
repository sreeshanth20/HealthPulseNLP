"""Optional Redis cache with a transparent in-process fallback.

When REDIS_URL is not configured (or Redis is unreachable) the cache becomes a
best-effort no-op so the platform runs without Redis. Used for analytics
snapshots; never for auth-critical state.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

try:  # pragma: no cover - depends on environment
    import redis as _redis
except ImportError:  # pragma: no cover
    _redis = None

_memory_store: dict[str, str] = {}
_client = None
_checked = False


def _get_client():
    global _client, _checked
    if not _checked and _redis is not None and settings.redis_url:
        try:
            _client = _redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2,
                                            decode_responses=True)
            _client.ping()
            logger.info("Redis cache connected")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis unavailable (%s); using in-process cache", exc)
            _client = None
        _checked = True
    return _client


def cache_get_json(key: str) -> Any | None:
    client = _get_client()
    try:
        raw = client.get(key) if client else _memory_store.get(key)
        return json.loads(raw) if raw else None
    except Exception:  # noqa: BLE001
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int = 60) -> None:
    payload = json.dumps(value, default=str)
    client = _get_client()
    try:
        if client:
            client.setex(key, ttl_seconds, payload)
        else:
            _memory_store[key] = payload  # no TTL in fallback; small values only
    except Exception:  # noqa: BLE001
        pass


def cache_status() -> str:
    return "redis" if _get_client() is not None else ("memory-fallback" if settings.redis_url else "disabled")
