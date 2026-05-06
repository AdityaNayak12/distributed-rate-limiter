from abc import ABC, abstractmethod
from typing import Tuple

class BaseLimiter(ABC):
    @abstractmethod
    def allow(self, key: str, now:float)-> Tuple[bool, int]:
        pass
