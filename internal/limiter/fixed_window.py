from typing import Tuple
from internal.limiter.base import BaseLimiter
from internal.storage.redis_client import RedisClient
import math

class FixedWindowLimiter(BaseLimiter):
    def __init__(self, limit: int, window_size: float):
        """
        limit: max requests per window
        window_size: window in seconds
        """
        self.limit = limit
        self.window_size = window_size
        self.redis = RedisClient().get_client()

    def _window_key(self, key: str, now: float) -> str:
        window = int(math.floor(now / self.window_size))
        return f"rate_limit:fixed:{key}:{window}"

    def allow(self, key: str, now: float) -> Tuple[bool, int]:
        redis_key = self._window_key(key, now)
        count = self.redis.incr(redis_key)
        if count == 1:
            # Set expiry only on first increment
            self.redis.expire(redis_key, int(self.window_size) + 1)
        allowed = count <= self.limit
        remaining = max(self.limit - count, 0) if allowed else 0
        return allowed, remaining
