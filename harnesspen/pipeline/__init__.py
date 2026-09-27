from .state import PipelineState, PipelineOutput
from .graph import _build_generate_graph, _build_rewrite_graph


def run_pipeline(messages: list, original: str = None) -> PipelineOutput:
    if original:
        graph = _build_rewrite_graph()
        initial_state: PipelineState = {
            "messages": messages,
            "original": original,
            "mode": "rewrite",
            "outline": "",
            "segments": [],
            "article": "",
            "title": "",
            "search_results": "",
        }
    else:
        graph = _build_generate_graph()
        initial_state: PipelineState = {
            "messages": messages,
            "original": None,
            "mode": "generate",
            "outline": "",
            "segments": [],
            "article": "",
            "title": "",
            "search_results": "",
        }

    final_state = graph.invoke(
        initial_state,
        config={"recursion_limit": 25}
    )

    return PipelineOutput(
        article=final_state.get("article", ""),
        outline=final_state.get("outline", ""),
        title=final_state.get("title", ""),
    )
