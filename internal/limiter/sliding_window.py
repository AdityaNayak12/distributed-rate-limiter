import os
import uuid
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

        # Load sliding window Lua script
        script_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "internal", "storage", "scripts"
        )
        script_path = os.path.join(script_dir, "sliding_window.lua")
        with open(script_path, "r") as f:
            script_code = f.read()
        self.lua_script = self.redis.register_script(script_code)

    def _window_key(self, key: str) -> str:
        return f"{self.key_prefix}:sliding:{key}"

    def allow(self, key: str, now: float) -> Tuple[bool, int]:
        redis_key = self._window_key(key)
        # Create a unique member name to avoid overwriting during concurrent requests at the same timestamp
        member = f"{now}:{uuid.uuid4()}"

        # Execute the Lua script atomically
        res = self.lua_script(keys=[redis_key], args=[now, self.window_size, self.limit, member])
        allowed_val, remaining = res[0], res[1]

        return allowed_val == 1, remaining

