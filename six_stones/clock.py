from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ChessClock:
    total_seconds: float
    remaining_seconds: float | None = None
    started_at: float | None = None

    def __post_init__(self) -> None:
        if self.remaining_seconds is None:
            self.remaining_seconds = self.total_seconds

    def start(self) -> None:
        if self.started_at is None:
            self.started_at = time.perf_counter()

    def stop(self) -> None:
        if self.started_at is not None:
            self.remaining_seconds = max(0.0, self.remaining() )
            self.started_at = None

    def remaining(self) -> float:
        assert self.remaining_seconds is not None
        if self.started_at is None:
            return self.remaining_seconds
        return max(0.0, self.remaining_seconds - (time.perf_counter() - self.started_at))

    def expired(self) -> bool:
        return self.remaining() <= 0

