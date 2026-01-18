"""성능 측정 유틸리티."""

import logging
import time

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """성능 추적 클래스."""

    MS_PER_SECOND = 1000

    def __init__(self, operation: str):
        self.operation = operation
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.checkpoints: list[tuple[str, float]] = []

    def start(self):
        """측정 시작."""
        self.start_time = time.perf_counter()
        return self

    def checkpoint(self, name: str):
        """체크포인트 기록."""
        if self.start_time:
            elapsed = (time.perf_counter() - self.start_time) * self.MS_PER_SECOND
            self.checkpoints.append((name, elapsed))
            logger.debug(f"[Performance] {self.operation} - {name}: {elapsed:.2f}ms")

    def stop(self):
        """측정 종료."""
        self.end_time = time.perf_counter()
        if self.start_time:
            total = (self.end_time - self.start_time) * self.MS_PER_SECOND
            logger.info(f"[Performance] {self.operation} total: {total:.2f}ms")
        return self

    @property
    def elapsed_ms(self) -> float:
        """경과 시간 (밀리초)."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * self.MS_PER_SECOND
        return 0.0
