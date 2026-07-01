from langgraph.graph import StateGraph, END
from .state import PipelineState
from .nodes import (
    search_node, analyze_requirement_node, outline_node,
    write_section_node_factory,
    integrate_node, title_optimize_node,
    analyze_original_node, consistency_check_node,
    rewrite_section_node_factory,
)


def _build_generate_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("search", search_node)
    graph.add_node("analyze", analyze_requirement_node)
    graph.add_node("outline", outline_node)
    graph.add_node("write_1", write_section_node_factory(1, "引言"))
    graph.add_node("write_2", write_section_node_factory(2, "正文"))
    graph.add_node("write_3", write_section_node_factory(3, "总结"))
    graph.add_node("integrate", integrate_node)
    graph.add_node("title", title_optimize_node)

    graph.set_entry_point("search")
    graph.add_edge("search", "analyze")
    graph.add_edge("analyze", "outline")
    graph.add_edge("outline", "write_1")
    graph.add_edge("write_1", "write_2")
    graph.add_edge("write_2", "write_3")
    graph.add_edge("write_3", "integrate")
    graph.add_edge("integrate", "title")
    graph.add_edge("title", END)

    return graph.compile()


def _build_rewrite_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("analyze_original", analyze_original_node)
    graph.add_node("rewrite_1", rewrite_section_node_factory(1, "段落1"))
    graph.add_node("rewrite_2", rewrite_section_node_factory(2, "段落2"))
    graph.add_node("integrate", integrate_node)
    graph.add_node("consistency", consistency_check_node)

    graph.set_entry_point("analyze_original")
    graph.add_edge("analyze_original", "rewrite_1")
    graph.add_edge("rewrite_1", "rewrite_2")
    graph.add_edge("rewrite_2", "integrate")
    graph.add_edge("integrate", "consistency")
    graph.add_edge("consistency", END)

    return graph.compile()
