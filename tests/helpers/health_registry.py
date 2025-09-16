from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, List, Optional

from claude_builder.utils.health import (
    HealthCheck,
    HealthCheckType,
    HealthStatus,
    default_health_check_registry,
)


@contextmanager
def temp_health_registry(checks: Optional[List[HealthCheck]] = None) -> Iterator[None]:
    """Temporarily replace the default health check registry contents.

    Example:
        with temp_health_registry([AlwaysHealthyCheck()]):
            result = runner.invoke(health, ["check"])  # uses only provided checks

    The previous registry contents are restored after the context exits.
    """
    original = list(default_health_check_registry.get_checks())
    default_health_check_registry.clear()
    try:
        if checks:
            default_health_check_registry.register(*checks)
        yield
    finally:
        default_health_check_registry.clear()
        default_health_check_registry.register(*original)


class StubCheck(HealthCheck):
    """Simple stub health check returning a fixed status and message.

    Useful for CLI E2E tests to force HEALTHY/WARNING/CRITICAL flows
    without relying on real system metrics.
    """

    def __init__(
        self,
        name: str,
        status: HealthStatus,
        check_type: HealthCheckType = HealthCheckType.APPLICATION,
        message: str = "stub",
    ) -> None:
        super().__init__(name, check_type)
        self._status = status
        self._message = message

    def check(self):  # type: ignore[override]
        return self._create_result(self._status, self._message)
