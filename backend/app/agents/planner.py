import time
import json
from datetime import date
from langchain_google_genai import ChatGoogleGenerativeAI
from app.state import RuneState
from app.agents.config import NODE_CONFIG
from app.agents.llm_utils import invoke_with_retry

PLANNER_PROMPT = """You are the planning agent in a multi-agent research system.
Break the user's query into {task_range} concrete sub-tasks that, together, fully answer it.

IMPORTANT: Today's real-world date is {current_date}. This system has a live web
search tool that returns current, up-to-date information beyond your training
data cutoff. Do NOT refuse, hedge, or claim you "can't predict the future" for
queries about {current_date} or any other date, past or present — treat every
query as answerable via search and produce concrete, searchable sub-tasks for it.

Rules:
- If the query is ambiguous or under-specified, output a single sub-task that is
  a clarifying question instead of guessing what the user meant.
- If the query contains a false premise, output a single sub-task that flags and
  corrects the premise instead of building on it.
- Otherwise, output {task_range} sub-tasks as a JSON list of strings.
- Output ONLY the raw JSON list. No markdown code fences, no explanation, no other text.

Query: {query}
Output (JSON list only):"""

def planner_node(state: RuneState) -> RuneState:
    print(f"[DEBUG] planner_node called — session={state['session_id']}")
    start = time.time()
    cfg = NODE_CONFIG["planner"]
    llm = ChatGoogleGenerativeAI(model=cfg["model"], temperature=cfg["temperature"])

    depth = state.get("depth", "deep")
    task_range = "1-2" if depth == "shallow" else "2-4"

    prompt = PLANNER_PROMPT.format(
        query=state["original_query"],
        current_date=date.today().isoformat(),
        task_range=task_range,
    )
    response = invoke_with_retry(llm, prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        sub_tasks = json.loads(raw)
        if not isinstance(sub_tasks, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        sub_tasks = [raw]

    latency_ms = int((time.time() - start) * 1000)
    tokens = getattr(response, "usage_metadata", {}).get("total_tokens", 0)

    state["sub_tasks"] = sub_tasks
    state["trace"].append({
        "node": "planner",
        "summary": f"split into: {', '.join(sub_tasks)}",
        "tokens_used": tokens,
        "latency_ms": latency_ms,
    })
    state["total_tokens"] = state.get("total_tokens", 0) + tokens
    return state