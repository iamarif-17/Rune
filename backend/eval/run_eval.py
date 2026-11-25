from dotenv import load_dotenv
load_dotenv()
"""
Runs the eval query set against Rune and logs pass/fail + reasoning.
No UI - just a log file, per project scope decision. Run with:

    python -m eval.run_eval --label baseline

Rescore a saved run with the current checker (no API calls, no quota):

    python -m eval.run_eval --rescore ambiguity_fix

Outputs eval/results_<label>.json - paste this directly in interviews if asked
"how did you validate correctness".
"""

import argparse
import json
import time
from collections import defaultdict
from app.graph import run_query

QUERIES_PATH = "eval/eval_queries.json"
PAUSE_BETWEEN_QUERIES_S = 2


def load_queries():
    with open(QUERIES_PATH) as f:
        return json.load(f)


def check_ambiguous_handling(final_answer: str, category: str = "ambiguous") -> bool:
    """
    ambiguous: Rune must state an assumption or ask for clarification.
    false_premise: Rune must say the premise is wrong.
    Still keyword-based; an LLM judge would be the next upgrade.

    NOTE: the first two runs (12/18 and 15/18) used a looser checker
    (signals: "?", "clarify", "could you specify", "which", "unclear", "assum").
    This stricter version was written after reading the saved answers.
    """
    lowered = final_answer.lower()
    if category == "false_premise":
        signals = ["premise", "incorrect", "inaccurate", "not accurate", "unsupported",
                   "no evidence", "has not", "hasn't", "misconception", "false"]
    else:
        signals = ["i'm assuming", "i am assuming", "assuming you", "clarify", "unclear",
                   "could you specify", "do you mean", "did you mean", "if you meant",
                   "if you had a different", "depends on what you"]
    return any(s in lowered for s in signals)


def is_quota_error(e: Exception) -> bool:
    text = str(e).lower()
    return "resourceexhausted" in text or "429" in text or "quota" in text


def print_summary(results, total, results_path, stopped_early=False):
    passed_count = sum(1 for r in results if r["passed"])
    suffix = f" (stopped early, {total - len(results)} not run)" if stopped_early else ""
    print(f"\n{passed_count}/{total} passed{suffix}")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] #{r['id']} ({r['category']}) - {r['reason']}")

    by_cat = defaultdict(lambda: [0, 0])
    for r in results:
        by_cat[r["category"]][1] += 1
        by_cat[r["category"]][0] += int(r["passed"])
    print("\nBy category:")
    for cat, (p, t) in by_cat.items():
        print(f"  {cat}: {p}/{t}")

    avg_latency = sum(r["latency_s"] for r in results) / max(len(results), 1)
    print(f"\nAvg latency: {avg_latency:.1f}s | results saved to {results_path}")


def rescore(label: str):
    """Re-apply the current checker to a saved run. Free: makes no LLM calls."""
    src = f"eval/results_{label}.json"
    dst = f"eval/results_{label}_rescored.json"
    with open(src) as f:
        results = json.load(f)

    for r in results:
        if r["category"] in ("ambiguous", "false_premise") and r.get("answer"):
            passed = check_ambiguous_handling(r["answer"], r["category"])
            r["passed"] = passed
            r["reason"] = ("handled ambiguity/false premise appropriately" if passed
                           else "answered confidently without flagging ambiguity")

    with open(dst, "w") as f:
        json.dump(results, f, indent=2)
    print_summary(results, len(results), dst)


def run_all(label: str):
    results_path = f"eval/results_{label}.json"
    queries = load_queries()
    results = []
    stopped_early = False

    for q in queries:
        start = time.time()
        try:
            state = run_query(q["query"], session_id=f"eval-{q['id']}")
            latency = time.time() - start
            answer = state.get("final_answer", "")

            if q["category"] in ("ambiguous", "false_premise"):
                passed = check_ambiguous_handling(answer, q["category"])
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
                "answer": answer,
            })
        except Exception as e:
            results.append({
                "id": q["id"],
                "category": q["category"],
                "query": q["query"],
                "passed": False,
                "reason": f"error: {str(e)[:200]}",
                "latency_s": round(time.time() - start, 2),
                "tokens_used": 0,
                "answer": "",
            })
            if is_quota_error(e):
                print(f"\nQuota error at query #{q['id']}. Stopping early; "
                      f"results so far are saved. Rerun later or switch model.")
                stopped_early = True
                break

        # save after every query so a crash never loses finished work
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        time.sleep(PAUSE_BETWEEN_QUERIES_S)

    print_summary(results, len(queries), results_path, stopped_early)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run", help="name for this run, e.g. baseline")
    parser.add_argument("--rescore", metavar="LABEL",
                        help="re-apply the current checker to eval/results_<LABEL>.json (no API calls)")
    args = parser.parse_args()
    if args.rescore:
        rescore(args.rescore)
    else:
        run_all(args.label)