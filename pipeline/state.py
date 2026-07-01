from typing import TypedDict, Annotated
import operator
from pydantic import BaseModel


class PipelineState(TypedDict):
    messages: list
    original: str
    mode: str
    outline: str
    segments: Annotated[list[str], operator.add]
    article: str
    title: str
    search_results: str


class PipelineOutput(BaseModel):
    article: str
    outline: str
    title: str
