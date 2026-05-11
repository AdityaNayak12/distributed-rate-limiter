from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from internal.config.settings import settings
from internal.limiter.token_bucket import TokenBucketLimiter
from internal.limiter.sliding_window import SlidingWindowLimiter
from internal.limiter.fixed_window import FixedWindowLimiter
import time

# Strategy selector
def get_limiter():
    strategy = settings.rate_limit.strategy
    if strategy == "token_bucket":
        return TokenBucketLimiter()
    elif strategy == "sliding_window":
        return SlidingWindowLimiter()
    elif strategy == "fixed_window":
        return FixedWindowLimiter()
    else:
        raise ValueError(f"Unknown rate limit strategy: {strategy}")

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.limiter = get_limiter()

    async def dispatch(self, request: Request, call_next):
        # Key extraction: by IP (customize as needed)
        key = request.client.host
        now = time.time()
        allowed, remaining = self.limiter.allow(key, now)
        limit = settings.rate_limit.capacity
        window = settings.rate_limit.refill_rate
        reset = int(now + window)
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset),
        }
        if not allowed:
            return JSONResponse(
                {"error": "Too Many Requests"},
                status_code=429,
                headers=headers,
            )
        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response