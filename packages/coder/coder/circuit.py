"""Circuit breaker for the TDD execution engine.

Enforces limits on attempts, wall time, and token consumption to
prevent runaway agent loops.

Implements Requirements:
    15-REQ-1.1 (max attempts), 15-REQ-1.2 (max wall time),
    15-REQ-1.3 (max tokens), 15-REQ-1.4 (halt on breach),
    15-REQ-1.5 (configurable limits), 15-REQ-1.E1 (zero/negative),
    15-REQ-1.E2 (null unlimited).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from coder.errors import ConfigError


@dataclass
class CheckResult:
    """Result of a circuit breaker limit check.

    Attributes:
        halted: Whether execution should be halted.
        reason: Descriptive reason for the halt, or None if not halted.
    """

    halted: bool
    reason: str | None = None


class CircuitBreaker:
    """Check attempt, time, and token limits against graph state.

    Validates limits at construction time and checks them on each
    call to :meth:`check`. Null (``None``) limits are treated as
    unlimited — the corresponding dimension is not enforced.

    Parameters
    ----------
    config:
        A safety configuration object with optional integer attributes
        ``max_attempts_per_task``, ``max_wall_time_seconds``, and
        ``max_tokens``. ``None`` values mean unlimited.
    start_time:
        The wall-clock time when execution started (as returned by
        ``time.time()``). Defaults to the current time.

    Raises
    ------
    ConfigError
        If any non-None limit is zero or negative.
    """

    def __init__(
        self,
        config: object,
        start_time: float | None = None,
    ) -> None:
        self.config = config
        self._start_time = start_time if start_time is not None else time.time()

        # Validate: reject zero or negative limits (15-REQ-1.E1)
        self._validate_limits()

    def _validate_limits(self) -> None:
        """Reject zero or negative limits at construction time."""
        limits = [
            (
                "max_attempts_per_task",
                getattr(self.config, "max_attempts_per_task", None),
            ),
            (
                "max_wall_time_seconds",
                getattr(self.config, "max_wall_time_seconds", None),
            ),
            (
                "max_tokens",
                getattr(self.config, "max_tokens", None),
            ),
        ]
        for name, value in limits:
            if value is not None and value <= 0:
                raise ConfigError(
                    f"Safety limit '{name}' must be positive, got {value}",
                    detail=f"{name}={value}",
                )

    def check(
        self,
        state: dict[str, object],
        token_tracker: object,
    ) -> CheckResult:
        """Check all limits against current state.

        Parameters
        ----------
        state:
            The current graph state dictionary. Must contain
            ``attempt_count`` (int).
        token_tracker:
            An object with a ``total_tokens`` property (int) giving the
            cumulative token count.

        Returns
        -------
        A :class:`CheckResult` indicating whether execution should halt
        and, if so, why.
        """
        # Check attempt limit (15-REQ-1.1)
        max_attempts = getattr(self.config, "max_attempts_per_task", None)
        if max_attempts is not None:
            raw_count = state.get("attempt_count", 0)
            attempt_count = (
                int(raw_count)  # type: ignore[call-overload]
                if raw_count is not None
                else 0
            )
            if attempt_count >= max_attempts:
                return CheckResult(
                    halted=True,
                    reason=(
                        f"Max attempts exceeded: {attempt_count} attempts "
                        f"reached limit of {max_attempts}"
                    ),
                )

        # Check wall time limit (15-REQ-1.2)
        max_wall_time = getattr(self.config, "max_wall_time_seconds", None)
        if max_wall_time is not None:
            elapsed = time.time() - self._start_time
            if elapsed >= max_wall_time:
                return CheckResult(
                    halted=True,
                    reason=(
                        f"Max wall time exceeded: {elapsed:.0f}s elapsed, "
                        f"limit is {max_wall_time}s"
                    ),
                )

        # Check token limit (15-REQ-1.3)
        max_tokens = getattr(self.config, "max_tokens", None)
        if max_tokens is not None:
            total_tokens = getattr(token_tracker, "total_tokens", 0)
            if total_tokens >= max_tokens:
                return CheckResult(
                    halted=True,
                    reason=(
                        f"Max tokens exceeded: {total_tokens} tokens used, "
                        f"limit is {max_tokens}"
                    ),
                )

        return CheckResult(halted=False)
