from typing import Tuple
from internal.limiter.base import BaseLimiter
from internal.models.bucket import Bucket
from internal.storage.redis_client import RedisClient


class TokenBucketLimiter(BaseLimiter):
    def __init__(self, capacity: int, refill_rate: float):
        """
        capacity: max tokens
        refill_rate: tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.redis = RedisClient().get_client()

    def _bucket_key(self, key: str) -> str:
        return f"rate_limit:bucket:{key}"

    def allow(self, key: str, now: float) -> Tuple[bool, int]:
        redis_key = self._bucket_key(key)
        bucket_data = self.redis.hgetall(redis_key)

        if not bucket_data:
            tokens = self.capacity
            last_refill = now
        else:
            tokens = float(bucket_data.get("tokens", self.capacity))
            last_refill = float(bucket_data.get("last_refill", now))

        # Refill tokens
        elapsed = now - last_refill
        refill = elapsed * self.refill_rate
        tokens = min(self.capacity, tokens + refill)
        last_refill = now

        # Check if request can be allowed
        if tokens >= 1:
            tokens -= 1
            allowed = True
        else:
            allowed = False

        # Save updated state to Redis
        self.redis.hmset(redis_key, {"tokens": tokens, "last_refill": last_refill})
        # Optionally set expiry
        self.redis.expire(redis_key, int(max(2 * (self.capacity / self.refill_rate), 60)))

        return allowed, int(tokens)