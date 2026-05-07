from dataclasses import dataclass


@dataclass
class Bucket:
    tokens: float
    last_refill: float