from typing import Tuple
from internal.limiter.base import BaseLimiter
from internal.storage.redis_client import RedisClient
from internal.config.settings import settings
import math

class FixedWindowLimiter(BaseLimiter):
    def __init__(self):
        self.limit = settings.rate_limit.capacity
        self.window_size = settings.rate_limit.refill_rate  # Assuming refill_rate is used as window size
        self.key_prefix = settings.rate_limit.key_prefix
        self.redis = RedisClient().get_client()

    def _window_key(self, key: str, now: float) -> str:
        window = int(math.floor(now / self.window_size))
        return f"{self.key_prefix}:fixed:{key}:{window}"

    def allow(self, key: str, now: float) -> Tuple[bool, int]:
        redis_key = self._window_key(key, now)
        count = self.redis.incr(redis_key)
        if count == 1:
            self.redis.expire(redis_key, int(self.window_size) + 1)
        allowed = count <= self.limit
        remaining = max(self.limit - count, 0) if allowed else 0
        return allowed, remaining
