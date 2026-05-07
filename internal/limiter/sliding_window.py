from typing import Tuple
from internal.limiter.base import BaseLimiter
from internal.storage.redis_client import RedisClient

class SlidingWindowLimiter(BaseLimiter):
    def __init__(self, limit: int, window_size: float):
        """
        limit: max requests
        window_size: window in seconds
        """
        self.limit = limit
        self.window_size = window_size
        self.redis = RedisClient().get_client()

    def _window_key(self, key: str) -> str:
        return f"rate_limit:sliding:{key}"

    def allow(self, key: str, now: float) -> Tuple[bool, int]:
        redis_key = self._window_key(key)
        window_start = now - self.window_size

        # Remove old entries
        self.redis.zremrangebyscore(redis_key, 0, window_start)
        # Count requests in window
        count = self.redis.zcard(redis_key)

        if count < self.limit:
            # Allow request, add timestamp
            self.redis.zadd(redis_key, {str(now): now})
            allowed = True
            remaining = self.limit - (count + 1)
        else:
            allowed = False
            remaining = 0

        # Set expiry to window size to auto-cleanup
        self.redis.expire(redis_key, int(self.window_size) + 1)
        return allowed, remaining
