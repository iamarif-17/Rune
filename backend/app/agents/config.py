"""
Model + temperature config per agent node.

Reasoning:
- planner / research / critique: low temperature (0.1-0.3) since these are
  logic/evaluation tasks that should be consistent, not "creative".
- synthesis: mid temperature (0.4-0.6) since it's the user-facing writing step,
  needs natural phrasing without drifting too far from grounded facts.
"""

import os

NODE_CONFIG = {
    "planner": {
        "model": os.getenv("PLANNER_MODEL", "gemini-1.5-flash"),
        "temperature": 0.25,
    },
    "research": {
        "model": os.getenv("RESEARCH_MODEL", "gemini-1.5-flash"),
        "temperature": 0.15,
    },
    "synthesis": {
        "model": os.getenv("SYNTHESIS_MODEL", "gemini-1.5-pro"),
        "temperature": 0.5,
    },
    "critique": {
        "model": os.getenv("CRITIQUE_MODEL", "gemini-1.5-flash"),
        "temperature": 0.15,
    },
}

MAX_ITERATIONS = int(os.getenv("MAX_CRITIQUE_ITERATIONS", "2"))

# Hard ceiling on total tokens per query, across all nodes combined. A real
# single query observed ~4,100 tokens in normal operation (shallow depth) -
# this cap exists as a safety net against a runaway critique-loop burning
# tokens indefinitely on a single query, independent of MAX_ITERATIONS.
MAX_TOKENS_PER_QUERY = int(os.getenv("MAX_TOKENS_PER_QUERY", "15000"))