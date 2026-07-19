"""
Builds the LangGraph state machine: planner -> research -> synthesis -> critique,
with critique able to loop back to research if it finds issues (up to
MAX_ITERATIONS times before giving up gracefully).
"""
from langgraph.graph import StateGraph, END
from app.state import RuneState
from app.agents.planner import planner_node
from app.agents.research import research_node
from app.agents.synthesis import synthesis_node
from app.agents.critique import critique_node, route_after_critique
from app.agents.config import MAX_ITERATIONS

def build_graph():
    graph = StateGraph(RuneState)
    graph.add_node("planner", planner_node)
    graph.add_node("research", research_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("critique", critique_node)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "research")
    graph.add_edge("research", "synthesis")
    graph.add_edge("synthesis", "critique")
    graph.add_conditional_edges(
        "critique",
        route_after_critique,
        {"research": "research", "end": END},
    )
    return graph.compile()

def run_query(query: str, session_id: str, depth: str = "deep") -> RuneState:
    """Runs a query through the full graph and returns the final state.
    Kept for cases where you just want the final result (e.g. eval script)."""
    app = build_graph()
    initial_state = _initial_state(query, session_id, depth)
    return app.invoke(initial_state)

def stream_query(query: str, session_id: str, depth: str = "deep"):
    """
    Streams the graph execution node-by-node. Yields the updated state after
    each node completes, so the caller (FastAPI's SSE endpoint) can push
    trace steps to the frontend live instead of waiting for the whole
    pipeline to finish.
    """
    app = build_graph()
    initial_state = _initial_state(query, session_id, depth)
    last_state = initial_state
    for update in app.stream(initial_state):
        for node_name, node_state in update.items():
            last_state = {**last_state, **node_state}
            yield node_name, last_state

def _initial_state(query: str, session_id: str, depth: str = "deep") -> RuneState:
    return {
        "original_query": query,
        "session_id": session_id,
        "depth": depth,
        "sub_tasks": [],
        "research_findings": [],
        "draft_answer": "",
        "citations": [],
        "critique_notes": [],
        "critique_passed": False,
        "iteration_count": 0,
        "max_iterations": MAX_ITERATIONS,
        "final_answer": "",
        "trace": [],
        "total_tokens": 0,
    }