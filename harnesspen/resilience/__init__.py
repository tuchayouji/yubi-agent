from pydantic import BaseModel
from harnesspen.config import settings
from .retry import retry_with_backoff
from .fallback import get_fallback_content


class Result(BaseModel):
    success: bool
    data: str | None
    error: str | None
    fallback_used: bool = False


def safe_invoke(func, *args, **kwargs) -> Result:
    def _call():
        return func(*args, **kwargs)

    try:
        data = retry_with_backoff(_call, max_retry=settings.max_retry)
        return Result(success=True, data=data, error=None, fallback_used=False)
    except Exception as e:
        fallback = get_fallback_content(str(args))
        return Result(
            success=False,
            data=fallback,
            error=str(e),
            fallback_used=True,
        )
