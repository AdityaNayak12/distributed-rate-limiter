from typing import Tuple
from internal.limiter.base import BaseLimiter
from internal.storage.redis_client import RedisClient
from internal.config.settings import settings

class SlidingWindowLimiter(BaseLimiter):
    def __init__(self):
        self.limit = settings.rate_limit.capacity
        self.window_size = settings.rate_limit.refill_rate  # Assuming refill_rate is used as window size
        self.key_prefix = settings.rate_limit.key_prefix
        self.redis = RedisClient().get_client()

    def _window_key(self, key: str) -> str:
        return f"{self.key_prefix}:sliding:{key}"

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
