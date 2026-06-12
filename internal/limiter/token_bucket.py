import os
from typing import Tuple
from internal.limiter.base import BaseLimiter
from internal.storage.redis_client import RedisClient
from internal.config.settings import settings

class TokenBucketLimiter(BaseLimiter):
    def __init__(self):
        self.capacity = settings.rate_limit.capacity
        self.refill_rate = settings.rate_limit.refill_rate
        self.key_prefix = settings.rate_limit.key_prefix
        self.redis = RedisClient().get_client()

        # Load token bucket Lua script
        script_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "internal", "storage", "scripts"
        )
        script_path = os.path.join(script_dir, "token_bucket.lua")
        with open(script_path, "r") as f:
            script_code = f.read()
        self.lua_script = self.redis.register_script(script_code)

    def _bucket_key(self, key: str) -> str:
        return f"{self.key_prefix}:bucket:{key}"

    def allow(self, key: str, now: float) -> Tuple[bool, int]:
        redis_key = self._bucket_key(key)
        # Calculate TTL dynamically (minimum 60 seconds)
        ttl = int(max(2 * (self.capacity / self.refill_rate), 60))

        # Execute Lua script atomically
        res = self.lua_script(keys=[redis_key], args=[now, self.refill_rate, self.capacity, ttl])
        allowed_val, remaining = res[0], res[1]

        return allowed_val == 1, remaining