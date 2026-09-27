import logging
from pydantic import BaseModel
from .whitelist import check_tool_allowed, validate_args, rate_limiter
from .search import SearchTool

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    success: bool
    data: str | None
    reject_reason: str | None


def call_tool(name: str, args: dict) -> ToolResult:
    # 白名单校验
    if not check_tool_allowed(name):
        logger.warning(f"Tool '{name}' rejected: not in whitelist")
        return ToolResult(success=False, data=None, reject_reason=f"工具 '{name}' 不在白名单中")

    # 参数校验
    error = validate_args(name, args)
    if error:
        return ToolResult(success=False, data=None, reject_reason=error)

    # 限流检查
    if not rate_limiter.check_and_increment():
        return ToolResult(success=False, data=None, reject_reason="工具调用次数超过限制")

    # 审计日志
    logger.info(f"Tool call: {name}, args: {args}")

    # 执行调用
    try:
        if name == "search":
            tool = SearchTool()
            data = tool.execute(args)
            return ToolResult(success=True, data=data, reject_reason=None)
        else:
            return ToolResult(success=False, data=None, reject_reason=f"工具 '{name}' 未实现")
    except Exception as e:
        logger.error(f"Tool '{name}' execution failed: {e}")
        return ToolResult(success=False, data=f"未获取到外部信息（执行失败: {e}）", reject_reason=str(e))
