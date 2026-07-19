"""
Runs the eval query set against Rune and logs pass/fail + reasoning.
No UI - just a log file, per project scope decision. Run with:

    python -m eval.run_eval

Outputs eval/results.json - paste this directly in interviews if asked
"how did you validate correctness".
"""

import json
import time
from app.graph import run_query

QUERIES_PATH = "eval/eval_queries.json"
RESULTS_PATH = "eval/results.json"


def load_queries():
    with open(QUERIES_PATH) as f:
        return json.load(f)


def check_ambiguous_handling(final_answer: str) -> bool:
    """
    Rough heuristic: for ambiguous/false-premise queries, a 'good' response
    either asks a question (contains '?') or explicitly flags uncertainty/
    the false premise, rather than confidently answering as if it had
    enough context. This is intentionally simple - refine with manual
    review for anything borderline.
    """
    lowered = final_answer.lower()
    signals = ["?", "clarify", "could you specify", "which", "unclear", "assum"]
    return any(s in lowered for s in signals)


def run_all():
    queries = load_queries()
    results = []

    for q in queries:
        start = time.time()
        try:
            state = run_query(q["query"], session_id=f"eval-{q['id']}")
            latency = time.time() - start

            if q["category"] in ("ambiguous", "false_premise"):
                passed = check_ambiguous_handling(state["final_answer"])
                reason = "handled ambiguity/false premise appropriately" if passed else "answered confidently without flagging ambiguity"
            else:
                min_citations = int(q["expects"].split(">=")[1].split(" ")[0])
                passed = len(state.get("citations", [])) >= min_citations
                reason = f"got {len(state.get('citations', []))} citations, needed {min_citations}"

            results.append({
                "id": q["id"],
                "category": q["category"],
                "query": q["query"],
                "passed": passed,
                "reason": reason,
                "latency_s": round(latency, 2),
                "tokens_used": state.get("total_tokens", 0),
            })
        except Exception as e:
            results.append({
                "id": q["id"],
                "category": q["category"],
                "query": q["query"],
                "passed": False,
                "reason": f"error: {str(e)}",
                "latency_s": round(time.time() - start, 2),
                "tokens_used": 0,
            })

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    passed_count = sum(1 for r in results if r["passed"])
    print(f"\n{passed_count}/{len(results)} passed")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] #{r['id']} ({r['category']}) - {r['reason']}")


if __name__ == "__main__":
    run_all()
