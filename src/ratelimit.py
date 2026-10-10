"""Rate limiter simple en memoria por token."""
import time
from collections import defaultdict
from typing import Dict, Tuple

# Configuración: 10 req/s, 8000/day
MAX_PER_SECOND = 10
MAX_PER_DAY = 8000

class TokenLimiter:
    def __init__(self):
        self.requests: list = []  # timestamps de requests
        self.daily_count = 0
        self.daily_reset = time.time()

    def is_allowed(self) -> Tuple[bool, str]:
        now = time.time()
        # Reset diario
        if now - self.daily_reset >= 86400:
            self.daily_count = 0
            self.daily_reset = now
        if self.daily_count >= MAX_PER_DAY:
            return False, "daily limit exceeded"
        # Ventana de 1 segundo
        window_start = now - 1.0
        self.requests = [ts for ts in self.requests if ts > window_start]
        if len(self.requests) >= MAX_PER_SECOND:
            return False, "rate limit exceeded"
        self.requests.append(now)
        self.daily_count += 1
        return True, ""

_limiters: Dict[str, TokenLimiter] = defaultdict(TokenLimiter)

def check_rate(token: str) -> Tuple[bool, str]:
    return _limiters[token].is_allowed()
