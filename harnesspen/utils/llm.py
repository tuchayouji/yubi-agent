from langchain_openai import ChatOpenAI
from harnesspen.config import settings


def create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )


def invoke_llm(prompt: str) -> str:
    llm = create_llm()
    response = llm.invoke(prompt)
    return response.content
