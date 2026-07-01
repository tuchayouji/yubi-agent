import time
import logging

logger = logging.getLogger(__name__)


def retry_with_backoff(func, max_retry=3, delay_base=1):
    last_error = None
    for attempt in range(max_retry):
        try:
            return func()
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1}/{max_retry} failed: {e}")
            if attempt < max_retry - 1:
                time.sleep(delay_base ** (attempt + 1))
    raise last_error
