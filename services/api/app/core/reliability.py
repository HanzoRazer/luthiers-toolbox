"""
Reliability utilities for resilient API operations.

Provides:
- retry_with_backoff: Exponential backoff retry decorator
- CircuitBreaker: Fail-fast for degraded dependencies
- TimeoutContext: Standardized timeout handling
"""
from __future__ import annotations

import functools
import logging
import time
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional, Set, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Retry with Exponential Backoff
# =============================================================================


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    retryable_exceptions: tuple = (Exception,)
    on_retry: Optional[Callable[[Exception, int], None]] = None


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    retryable: tuple = (Exception,),
):
    """
    Decorator for retrying operations with exponential backoff.

    Usage:
        @retry_with_backoff(max_attempts=3, retryable=(IOError, TimeoutError))
        def fetch_data():
            ...

        # Or with config object:
        @retry_with_backoff(config=RetryConfig(max_attempts=5))
        def fetch_data():
            ...
    """
    if config is None:
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay_seconds=base_delay,
            max_delay_seconds=max_delay,
            retryable_exceptions=retryable,
        )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = min(
                            config.base_delay_seconds * (config.exponential_base ** attempt),
                            config.max_delay_seconds,
                        )
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__}: {e}. "
                            f"Waiting {delay:.2f}s"
                        )
                        if config.on_retry:
                            config.on_retry(e, attempt + 1)
                        time.sleep(delay)

            raise last_exception  # type: ignore

        return wrapper
    return decorator


# =============================================================================
# Circuit Breaker
# =============================================================================


class CircuitState(str, Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 2          # Successes to close from half-open
    timeout_seconds: float = 30.0       # Time before half-open test
    excluded_exceptions: tuple = ()     # Exceptions that don't count as failures


class CircuitOpenError(Exception):
    """Raised when circuit is open and request is rejected."""

    def __init__(self, name: str, remaining_seconds: float):
        self.name = name
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Circuit '{name}' is open. Retry in {remaining_seconds:.1f}s"
        )


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Usage:
        db_breaker = CircuitBreaker("database", failure_threshold=3)

        @db_breaker
        def query_database():
            ...

        # Or manual:
        with db_breaker:
            result = external_call()
    """

    _instances: dict[str, "CircuitBreaker"] = {}
    _lock = threading.Lock()

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        **kwargs,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig(**kwargs)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()

        # Register instance for monitoring
        CircuitBreaker._instances[name] = self

    @classmethod
    def get(cls, name: str) -> Optional["CircuitBreaker"]:
        """Get circuit breaker by name."""
        return cls._instances.get(name)

    @classmethod
    def all_status(cls) -> dict[str, dict]:
        """Get status of all circuit breakers."""
        return {name: cb.status for name, cb in cls._instances.items()}

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
            return self._state

    @property
    def status(self) -> dict:
        """Current status for monitoring."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
        }

    def _should_attempt_reset(self) -> bool:
        if self._last_failure_time is None:
            return True
        elapsed = datetime.now() - self._last_failure_time
        return elapsed >= timedelta(seconds=self.config.timeout_seconds)

    def _record_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"Circuit '{self.name}' closed after recovery")
            else:
                self._failure_count = 0

    def _record_failure(self, exc: Exception):
        if isinstance(exc, self.config.excluded_exceptions):
            return

        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit '{self.name}' reopened after failure in half-open")
            elif self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit '{self.name}' opened after {self._failure_count} failures"
                )

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Use as decorator."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with self:
                return func(*args, **kwargs)
        return wrapper

    def __enter__(self):
        if self.state == CircuitState.OPEN:
            remaining = 0.0
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                remaining = max(0, self.config.timeout_seconds - elapsed)
            raise CircuitOpenError(self.name, remaining)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            self._record_success()
        elif exc_type is not None:
            self._record_failure(exc_val)
        return False  # Don't suppress exceptions


# =============================================================================
# Timeout Context
# =============================================================================


class TimeoutError(Exception):
    """Operation timed out."""
    pass


@contextmanager
def timeout_context(seconds: float, operation: str = "operation"):
    """
    Context manager for timeout tracking.

    Note: This doesn't actually interrupt blocking operations in Python.
    Use for async operations or operations that check elapsed time.

    Usage:
        with timeout_context(5.0, "database query") as ctx:
            while not done:
                if ctx.remaining <= 0:
                    raise TimeoutError("Query timed out")
                ...
    """
    start = time.monotonic()

    class TimeoutCtx:
        @property
        def elapsed(self) -> float:
            return time.monotonic() - start

        @property
        def remaining(self) -> float:
            return max(0, seconds - self.elapsed)

        @property
        def expired(self) -> bool:
            return self.elapsed >= seconds

        def check(self):
            if self.expired:
                raise TimeoutError(f"{operation} timed out after {seconds}s")

    yield TimeoutCtx()


# =============================================================================
# Request ID utilities
# =============================================================================


import uuid
from contextvars import ContextVar

_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return _request_id.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID in context. Returns the ID."""
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    _request_id.set(request_id)
    return request_id


class RequestIdFilter(logging.Filter):
    """Add request_id to log records."""

    def filter(self, record):
        record.request_id = get_request_id() or "-"
        return True
