"""Retry decorator with exponential backoff and jitter."""
import functools
import random
import time
from typing import Callable, Tuple, Type

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


def retry(
    max_attempts: int | None = None,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
) -> Callable:
    attempts = max_attempts or settings.max_retries

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == attempts:
                        log.error("%s failed after %d attempts: %s", fn.__name__, attempt, exc)
                        raise
                    delay = min(max_delay, base_delay * 2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    log.warning("%s attempt %d/%d failed (%s). Retrying in %.1fs",
                                fn.__name__, attempt, attempts, exc, delay)
                    time.sleep(delay)

        return wrapper

    return decorator