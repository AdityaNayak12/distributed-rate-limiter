from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    capacity: int = 10
    refil_rate: float = 5.0

    strategy: str = "token_bucket"

    key_prefix: str = "rate_limit"


@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0


@dataclass
class AppConfig:
    debug: bool = True
    environment: str = "dev"

class Settings:
    def __init__(self):
        self.rate_limit = RateLimitConfig(
            capacity=int(os.getenv("RATE_LIMIT_CAPACITY", 10)),
            refill_rate=float(os.getenv("RATE_LIMIT_REFILL_RATE", 5.0)),
            strategy=os.getenv("RATE_LIMIT_STRATEGY", "token_bucket"),
            key_prefix=os.getenv("RATE_LIMIT_KEY_PREFIX", "rate_limit"),
        )

        self.redis = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            password=os.getenv("REDIS_PASSWORD"),
        )

        self.app = AppConfig(
            debug=os.getenv("DEBUG", "true").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "dev"),
        )

settings = Settings()