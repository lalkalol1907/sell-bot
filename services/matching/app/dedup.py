import hashlib

import redis


class DedupStore:
    def __init__(self, redis_url: str, ttl_seconds: int = 6 * 3600):
        self._client = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds

    def try_reserve(self, chat_id: int, author_id: int, product_id: int) -> bool:
        """Atomically reserve dedup slot. Returns True if this caller should proceed."""
        key = self._key(chat_id, author_id, product_id)
        return bool(self._client.set(key, "1", nx=True, ex=self._ttl))

    def release(self, chat_id: int, author_id: int, product_id: int) -> None:
        """Release reservation after failed lead persistence."""
        self._client.delete(self._key(chat_id, author_id, product_id))

    def is_duplicate(self, chat_id: int, author_id: int, product_id: int) -> bool:
        return not self.try_reserve(chat_id, author_id, product_id)

    @staticmethod
    def _key(chat_id: int, author_id: int, product_id: int) -> str:
        raw = f"{chat_id}:{author_id}:{product_id}"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"dedup:{digest}"
