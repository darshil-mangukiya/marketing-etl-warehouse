from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    retry_statuses: frozenset[int] = frozenset({408, 429, 500, 502, 503, 504})

    def delay(self, attempt: int, retry_after: str | None = None) -> float:
        if retry_after:
            try:
                return min(float(retry_after), self.max_delay_seconds)
            except ValueError:
                try:
                    delta = (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds()
                    if delta >= 0:
                        return min(delta, self.max_delay_seconds)
                except (TypeError, ValueError, OverflowError):
                    pass
        return min(self.base_delay_seconds * (2 ** max(attempt - 1, 0)), self.max_delay_seconds)


def sleep_with_policy(policy: RetryPolicy, attempt: int, retry_after: str | None, sleeper: Callable[[float], None] = time.sleep) -> None:
    sleeper(policy.delay(attempt, retry_after))
