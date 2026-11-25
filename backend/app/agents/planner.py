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
- Decide whether the query is clear, ambiguous/under-specified, or built on a false premise.
- Mark "ambiguous" if ANY of these is true:
  * it uses vague references ("the two things everyone's using", "that tool", "it") with no clear referent
  * it is time-relative with no stated period ("this year", "recently", "now", "latest", "still")
  * it asks for a judgment with no criteria ("is X good", "is X still good", "which is best", "is X worth it")
  * it could reasonably mean two or more different things
- Mark "false_premise" if the query assumes something untrue or unverifiable.
- Otherwise mark "none". Do not mark clear, specific questions as ambiguous.
- Always output {task_range} searchable sub-tasks for the most reasonable interpretation. Do not replace them with a question.
- In "note", write one sentence naming the interpretation you chose (for ambiguous) or the wrong premise (for false_premise); leave it empty if issue is "none".
- Output ONLY a raw JSON object, no markdown fences, in this shape:
{{"issue": "none" | "ambiguous" | "false_premise", "note": "...", "sub_tasks": ["...", "..."]}}

Examples:
Query: is react still worth learning
{{"issue": "ambiguous", "note": "Assuming 'worth learning' means for getting a frontend developer job today.", "sub_tasks": ["React job market demand current year", "React compared with other frontend frameworks"]}}

Query: what's new in databases lately
{{"issue": "ambiguous", "note": "Assuming 'lately' means the past 12 months and 'databases' means mainstream relational and NoSQL systems.", "sub_tasks": ["major database releases past year", "database industry trends current year"]}}

Query: compare the two main cloud providers
{{"issue": "ambiguous", "note": "Assuming the two main providers are AWS and Microsoft Azure.", "sub_tasks": ["AWS vs Azure services and pricing", "AWS vs Azure market share and strengths"]}}

Query: since Python 4 removed the GIL, how do I write threaded code now
{{"issue": "false_premise", "note": "Python 4 has not been released and the GIL was not removed in it.", "sub_tasks": ["Python 4 release status", "Python GIL current status and threading options"]}}

Query: what is the time complexity of binary search
{{"issue": "none", "note": "", "sub_tasks": ["binary search time complexity explained"]}}

Query: {query}
Output (JSON object only):"""


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

    issue, note = "none", ""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            sub_tasks = parsed.get("sub_tasks") or [state["original_query"]]
            issue = parsed.get("issue", "none")
            note = parsed.get("note", "")
        elif isinstance(parsed, list):
            sub_tasks = parsed
        else:
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        sub_tasks = [state["original_query"]]

    sub_tasks = [str(t) for t in sub_tasks]
    if issue not in ("none", "ambiguous", "false_premise"):
        issue = "none"

    latency_ms = int((time.time() - start) * 1000)
    tokens = (getattr(response, "usage_metadata", None) or {}).get("total_tokens", 0)

    state["sub_tasks"] = sub_tasks
    state["planning_issue"] = issue
    state["planning_note"] = note
    state["trace"].append({
        "node": "planner",
        "summary": f"issue={issue}; split into: {', '.join(sub_tasks)}",
        "tokens_used": tokens,
        "latency_ms": latency_ms,
    })
    state["total_tokens"] = state.get("total_tokens", 0) + tokens
    return state