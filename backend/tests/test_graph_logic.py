import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.critique import route_after_critique
from app.agents.synthesis import synthesis_node
from app.agents.critique import critique_node


def make_state(**overrides):
    """Helper: builds a minimal fake RuneState dict, with overrides for
    whatever fields a specific test cares about."""
    base = {
        "original_query": "test query",
        "session_id": "test-session",
        "depth": "deep",
        "sub_tasks": [],
        "research_findings": [],
        "draft_answer": "",
        "citations": [],
        "critique_notes": [],
        "critique_passed": False,
        "iteration_count": 0,
        "max_iterations": 2,
        "final_answer": "",
        "trace": [],
        "total_tokens": 0,
    }
    base.update(overrides)
    return base


# --- route_after_critique ---

def test_route_ends_when_critique_passed():
    state = make_state(critique_passed=True, iteration_count=1, max_iterations=2)
    assert route_after_critique(state) == "end"


def test_route_loops_back_when_failed_and_under_max():
    state = make_state(critique_passed=False, iteration_count=1, max_iterations=2)
    assert route_after_critique(state) == "research"


def test_route_ends_when_failed_but_max_iterations_hit():
    state = make_state(critique_passed=False, iteration_count=2, max_iterations=2)
    assert route_after_critique(state) == "end"


def test_route_ends_when_token_ceiling_hit():
    state = make_state(
        critique_passed=False,
        iteration_count=1,
        max_iterations=5,   # nowhere near max_iterations
        total_tokens=20000,  # over MAX_TOKENS_PER_QUERY (15000)
    )
    assert route_after_critique(state) == "end"


# --- synthesis_node empty-findings guard ---

def test_synthesis_skips_llm_when_no_findings():
    state = make_state(research_findings=[])
    result = synthesis_node(state)
    assert "wasn't able to find any information" in result["draft_answer"]
    assert result["citations"] == []
    assert result["trace"][-1]["tokens_used"] == 0


# --- critique_node empty-findings guard ---

def test_critique_auto_passes_when_no_findings():
    state = make_state(research_findings=[], draft_answer="fallback answer")
    result = critique_node(state)
    assert result["critique_passed"] is True
    assert result["final_answer"] == "fallback answer"
    assert result["trace"][-1]["tokens_used"] == 0