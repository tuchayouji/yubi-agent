import logging
from harnesspen.config import settings

logger = logging.getLogger(__name__)


class SearchTool:
    def __init__(self):
        self.api_key = settings.search_api_key
        self.api_type = settings.search_api

    def execute(self, args: dict) -> str:
        query = args.get("query", "")
        if not self.api_key:
            logger.warning("Search API key not configured, returning empty result")
            return "未获取到外部信息（API Key 未配置）"

        try:
            if self.api_type == "tavily":
                return self._search_tavily(query)
            else:
                return self._search_generic(query)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"未获取到外部信息（搜索失败: {e}）"

    def _search_tavily(self, query: str) -> str:
        from tavily import TavilyClient
        client = TavilyClient(api_key=self.api_key)
        response = client.search(query, max_results=3)
        results = []
        for item in response.get("results", []):
            results.append(f"- {item.get('title', '')}: {item.get('content', '')}")
        return "\n".join(results) if results else "未找到相关搜索结果"

    def _search_generic(self, query: str) -> str:
        return f"搜索结果（{query}）: 通用搜索接口未实现，请配置 tavily"
