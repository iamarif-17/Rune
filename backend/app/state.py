"""
Shared state object that flows through every node in the LangGraph graph.
Each node reads from this state and writes its output back into it.
"""

from typing import TypedDict, List, Optional


class ResearchFinding(TypedDict):
    source: str          # e.g. "web_search" or "faiss_retrieve"
    content: str          # the raw text/snippet returned
    url: Optional[str]    # source URL if applicable


class CritiqueNote(TypedDict):
    issue: str             # what's wrong (e.g. "unsupported claim")
    detail: str             # specifics
    severity: str           # "minor" | "major"


class AgentStep(TypedDict):
    """One entry in the trace log - what the UI's trace panel renders."""
    node: str               # "planner" | "research" | "synthesis" | "critique"
    summary: str             # short human-readable description of what happened
    tokens_used: int
    latency_ms: int


class RuneState(TypedDict):
    # input
    original_query: str
    session_id: str
    depth: str      

    # planner output
    sub_tasks: List[str]

    # research output
    research_findings: List[ResearchFinding]

    # synthesis output
    draft_answer: str
    citations: List[str]

    # critique output
    critique_notes: List[CritiqueNote]
    critique_passed: bool

    # control flow
    iteration_count: int
    max_iterations: int

    # final output
    final_answer: str

    # observability
    trace: List[AgentStep]
    total_tokens: int
