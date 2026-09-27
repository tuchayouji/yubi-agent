import logging
from harnesspen.config import settings

logger = logging.getLogger(__name__)


def check_tool_allowed(tool_name: str) -> bool:
    return tool_name in settings.allow_tool_list


def validate_args(tool_name: str, args: dict) -> str | None:
    if tool_name == "search":
        if not args.get("query"):
            return "缺少必需参数: query"
        if not isinstance(args["query"], str):
            return "参数 query 必须是字符串"
    return None


class RateLimiter:
    def __init__(self):
        self._call_count = 0

    def check_and_increment(self) -> bool:
        if self._call_count >= settings.tool_rate_limit:
            return False
        self._call_count += 1
        return True


rate_limiter = RateLimiter()
