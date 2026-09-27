from pathlib import Path

from pathlib import Path

from pathlib import Path

from pathlib import Path

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM 配置
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # 容错配置
    max_retry: int = 3
    timeout: int = 30
    quality_max_rewrite_rounds: int = 3

    # 搜索 API
    search_api: str = "tavily"
    search_api_key: str = ""

    # 工具管控
    allow_tool_list: list[str] = ["search"]
    tool_rate_limit: int = 10

    # LangGraph
    recursion_limit: int = 25

    model_config = {"env_file": str(Path(__file__).resolve().parent.parent / ".env"), "env_file_encoding": "utf-8"}


settings = Settings()
