"""Utility functions for API retry logic with exponential backoff."""

import logging
import time
from functools import wraps
from typing import Callable, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exceptions: Tuple of exceptions to catch and retry (default: all exceptions)
        on_retry: Optional callback function called on each retry with (exception, attempt_number)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_retries=3, initial_delay=2.0)
        def fetch_data_from_api():
            response = requests.get('https://api.example.com/data')
            response.raise_for_status()
            return response.json()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        # Last attempt failed, raise the exception
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise

                    # Calculate delay for this retry
                    current_delay = min(delay, max_delay)

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )

                    # Call on_retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {callback_error}")

                    # Wait before retrying
                    time.sleep(current_delay)

                    # Increase delay for next retry (exponential backoff)
                    delay *= backoff_factor

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed unexpectedly")

        return wrapper

    return decorator


def is_retryable_error(exception: Exception) -> bool:
    """Check if an exception is retryable.

    Args:
        exception: Exception to check

    Returns:
        True if exception is retryable, False otherwise
    """
    # Network errors are generally retryable
    retryable_types = (
        "ConnectionError",
        "Timeout",
        "TimeoutError",
        "HTTPError",
        "RequestException",
    )

    exception_type = type(exception).__name__

    # Check if it's a retryable type
    if any(rt in exception_type for rt in retryable_types):
        return True

    # Check for specific HTTP status codes (if it's an HTTP error)
    if hasattr(exception, "response") and hasattr(exception.response, "status_code"):
        status_code = exception.response.status_code
        # Retry on server errors (5xx) and rate limiting (429)
        if status_code >= 500 or status_code == 429:
            return True

    return False


def retry_on_network_error(max_retries: int = 4, initial_delay: float = 2.0):
    """Decorator specifically for network errors with conservative backoff.

    This is tailored for network operations that may fail due to temporary
    connectivity issues.

    Args:
        max_retries: Maximum retry attempts (default: 4)
        initial_delay: Initial delay in seconds (default: 2.0)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_network_error(max_retries=4, initial_delay=2.0)
        def sync_github_data():
            # API call that may fail due to network issues
            pass
    """
    # Import here to avoid circular dependencies
    try:
        import requests

        network_exceptions = (
            requests.exceptions.RequestException,
            ConnectionError,
            TimeoutError,
        )
    except ImportError:
        network_exceptions = (ConnectionError, TimeoutError)

    def on_retry_callback(exception: Exception, attempt: int):
        """Log retry attempts with additional context."""
        if hasattr(exception, "response"):
            logger.info(f"HTTP Status: {exception.response.status_code}")

    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=2.0,  # Double delay each time (2s, 4s, 8s, 16s)
        max_delay=30.0,
        exceptions=network_exceptions,
        on_retry=on_retry_callback,
    )


class RetryExhausted(Exception):
    """Exception raised when all retry attempts are exhausted."""

    pass


def retry_with_exponential_backoff(
    func: Callable[..., T], max_attempts: int = 4, base_delay: float = 2.0, *args, **kwargs
) -> T:
    """Execute a function with exponential backoff retry logic.

    This is a non-decorator version for cases where you want to apply
    retry logic inline rather than as a decorator.

    Args:
        func: Function to execute
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds (2s, 4s, 8s, 16s)
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from successful function execution

    Raises:
        RetryExhausted: If all attempts fail

    Example:
        result = retry_with_exponential_backoff(
            fetch_data,
            max_attempts=4,
            base_delay=2.0,
            url='https://api.example.com'
        )
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt == max_attempts - 1:
                # Last attempt, give up
                break

            # Calculate delay (2s, 4s, 8s, 16s)
            delay = base_delay * (2**attempt)
            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. " f"Retrying in {delay}s..."
            )
            time.sleep(delay)

    # All attempts failed
    raise RetryExhausted(
        f"Failed after {max_attempts} attempts. Last error: {last_exception}"
    ) from last_exception
