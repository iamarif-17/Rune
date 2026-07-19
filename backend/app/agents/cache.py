"""
Simple in-memory cache for research sub-task results, keyed by a hash of the
sub-task string. Avoids re-calling web_search for the same or a repeated
sub-task within the TTL window - saves API calls and latency for repeated or
overlapping queries (e.g. "how does X work" asked twice).

This is intentionally in-memory and single-process: fine for a local/single-
instance deployment. A multi-instance production deployment would need a
shared store (Redis) instead, since each process would otherwise have its
own separate cache.
"""
import hashlib
import time

_cache: dict[str, tuple[float, list]] = {}
TTL_SECONDS = 60 * 30  # 30 minutes - web content can go stale, so entries
                        # expire rather than living forever


def _cache_key(sub_task: str) -> str:
    return hashlib.sha256(sub_task.strip().lower().encode()).hexdigest()


def get_cached(sub_task: str):
    key = _cache_key(sub_task)
    entry = _cache.get(key)
    if entry is None:
        return None
    cached_at, results = entry
    if time.time() - cached_at > TTL_SECONDS:
        del _cache[key]  # expired, treat as a miss
        return None
    return results


def set_cached(sub_task: str, results: list):
    key = _cache_key(sub_task)
    _cache[key] = (time.time(), results)