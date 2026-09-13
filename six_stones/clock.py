from __future__ import annotations

import time
from dataclasses import dataclass
from math import isfinite


@dataclass
class ChessClock:
    total_seconds: float
    remaining_seconds: float | None = None
    started_at: float | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.total_seconds) or self.total_seconds <= 0:
            raise ValueError("棋钟总时间必须是大于 0 的有限数值")
        if self.remaining_seconds is None:
            self.remaining_seconds = self.total_seconds
        elif not isfinite(self.remaining_seconds) or self.remaining_seconds < 0:
            raise ValueError("棋钟剩余时间不能为负数或非有限数值")

    def start(self) -> None:
        """开始计时；重复调用不会重置已经开始的计时点。"""
        if self.started_at is None:
            self.started_at = time.perf_counter()

    def stop(self) -> None:
        """结算本段耗时，并把剩余时间限制在零以上。"""
        if self.started_at is not None:
            self.remaining_seconds = max(0.0, self.remaining())
            self.started_at = None

    def remaining(self) -> float:
        # __post_init__ 保证 remaining_seconds 已初始化为有限数值。
        assert self.remaining_seconds is not None
        if self.started_at is None:
            return self.remaining_seconds
        return max(0.0, self.remaining_seconds - (time.perf_counter() - self.started_at))

    def expired(self) -> bool:
        return self.remaining() <= 0
