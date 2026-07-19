import time
from app.state import RuneState
from app.tools.web_search import web_search
from app.tools.faiss_retrieve import faiss_retrieve
from app.agents.cache import get_cached, set_cached


def research_node(state: RuneState) -> RuneState:
    """
    For each sub-task, gather info via tools (web search + FAISS long-term memory).

    Note: this node calls faiss_retrieve() directly as a Python function for
    simplicity in the main app. The MCP server (see mcp_server/server.py)
    exposes the same faiss_retrieve capability as a standalone MCP-compliant
    service that any MCP client could call independently - it demonstrates
    the protocol integration without being on this node's critical path.
    A production version could swap this direct call for an MCP client call
    to unify the two paths.
    """
    start = time.time()
    findings = []
    cache_hits = 0

    for task in state["sub_tasks"]:
        cached = get_cached(task)
        if cached is not None:
            findings.extend(cached)
            cache_hits += 1
            continue

        task_findings = []
        web_results = web_search(task)
        for r in web_results:
            task_findings.append({"source": "web_search", "content": r["snippet"], "url": r.get("url")})

        memory_results = faiss_retrieve(task)
        for r in memory_results:
            task_findings.append({"source": "faiss_retrieve", "content": r["content"], "url": None})

        set_cached(task, task_findings)
        findings.extend(task_findings)

    latency_ms = int((time.time() - start) * 1000)

    state["research_findings"] = state.get("research_findings", []) + findings
    state["trace"].append({
        "node": "research",
        "summary": (
            f"called web_search, faiss_retrieve across {len(state['sub_tasks'])} sub-tasks, "
            f"found {len(findings)} results"
            + (f" ({cache_hits} from cache)" if cache_hits else "")
        ),
        "tokens_used": 0,
        "latency_ms": latency_ms,
    })
    return state