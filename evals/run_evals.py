"""Evaluation harness for DocsRAG.

Measures two things that matter for a RAG system:

1. Retrieval quality (no LLM needed) — context precision@k, recall, and MRR,
   judged against the `relevant_sources` labels in eval_set.jsonl.
2. Answer quality — an LLM-as-judge scores faithfulness (is the answer grounded
   in the retrieved context?) and fact recall (did it state the expected facts?),
   plus abstention accuracy on the deliberately unanswerable questions.

Run from the project root:  python -m evals.run_evals
Writes evals/results.json and a human-readable evals/results.md.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import llm                       # noqa: E402
from app.rag import RagEngine             # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_SET = os.path.join(HERE, "eval_set.jsonl")

JUDGE_SYSTEM = (
    "You are a strict evaluator. Respond with a single JSON object and nothing "
    "else."
)


def load_eval_set() -> list[dict]:
    with open(EVAL_SET, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# --- retrieval metrics ---------------------------------------------------
def retrieval_metrics(retrieved_sources: list[str], relevant: list[str]) -> dict:
    if not relevant:                       # unanswerable question, skip
        return {}
    rel = set(relevant)
    hits = [s in rel for s in retrieved_sources]
    precision = sum(hits) / len(hits) if hits else 0.0
    recall = len({s for s in retrieved_sources if s in rel}) / len(rel)
    mrr = 0.0
    for i, h in enumerate(hits, start=1):
        if h:
            mrr = 1.0 / i
            break
    return {"precision": precision, "recall": recall, "mrr": mrr}


# --- LLM judge -----------------------------------------------------------
def judge_answer(question: str, context: str, answer: str, expected_facts: list[str]) -> dict:
    prompt = f"""Evaluate an assistant's answer.

Question: {question}

Retrieved context:
{context}

Assistant answer:
{answer}

Expected facts the answer should contain:
{json.dumps(expected_facts)}

Score with this JSON schema:
{{"faithful": 0 or 1,   // 1 if every claim is supported by the context
  "facts_covered": float between 0 and 1,  // fraction of expected facts stated
  "reason": "one short sentence"}}"""
    raw = llm.generate(JUDGE_SYSTEM, prompt)
    return _parse_json(raw, default={"faithful": 0, "facts_covered": 0.0, "reason": "parse_error"})


def judged_abstention(answer: str) -> bool:
    """Heuristic: did the model correctly decline to answer?"""
    markers = ["don't have", "do not have", "not contain", "no information",
               "cannot find", "not mention", "not stated", "don't know"]
    low = answer.lower()
    return any(m in low for m in markers)


def _parse_json(text: str, default: dict) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return default
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return default


# --- main ----------------------------------------------------------------
def main() -> None:
    engine = RagEngine.load()
    cases = load_eval_set()

    latencies, precisions, recalls, mrrs = [], [], [], []
    faithfuls, fact_coverages = [], []
    abstentions_correct, abstention_total = 0, 0
    rows = []

    for case in cases:
        q = case["question"]
        t0 = time.perf_counter()
        result = engine.answer(q)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        latencies.append(latency_ms)

        retrieved_sources = [c.source for c in result.contexts]
        context_text = "\n\n".join(f"({c.label()}) {c.text}" for c in result.contexts)

        if case["answerable"]:
            rm = retrieval_metrics(retrieved_sources, case["relevant_sources"])
            precisions.append(rm["precision"])
            recalls.append(rm["recall"])
            mrrs.append(rm["mrr"])
            judged = judge_answer(q, context_text, result.answer, case["expected_facts"])
            faithfuls.append(int(judged.get("faithful", 0)))
            fact_coverages.append(float(judged.get("facts_covered", 0.0)))
            rows.append({"question": q, "latency_ms": latency_ms, **rm, **judged})
        else:
            abstention_total += 1
            correct = judged_abstention(result.answer)
            abstentions_correct += int(correct)
            rows.append({"question": q, "latency_ms": latency_ms,
                         "abstained": correct, "answer": result.answer})

    summary = {
        "n_cases": len(cases),
        "context_precision": round(statistics.mean(precisions), 3) if precisions else None,
        "context_recall": round(statistics.mean(recalls), 3) if recalls else None,
        "mrr": round(statistics.mean(mrrs), 3) if mrrs else None,
        "faithfulness": round(statistics.mean(faithfuls), 3) if faithfuls else None,
        "fact_coverage": round(statistics.mean(fact_coverages), 3) if fact_coverages else None,
        "abstention_accuracy": round(abstentions_correct / abstention_total, 3)
        if abstention_total else None,
        "latency_p50_ms": int(statistics.median(latencies)),
        "latency_p95_ms": int(sorted(latencies)[int(0.95 * (len(latencies) - 1))]),
    }

    _write_results(summary, rows)
    print(json.dumps(summary, indent=2))


def _write_results(summary: dict, rows: list[dict]) -> None:
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cases": rows}, f, indent=2)

    lines = ["# DocsRAG — Evaluation Results", "",
             f"_{summary['n_cases']} questions · generated by `python -m evals.run_evals`_", "",
             "| Metric | Value |", "|--------|-------|"]
    pretty = {
        "context_precision": "Context precision@k",
        "context_recall": "Context recall",
        "mrr": "Mean reciprocal rank",
        "faithfulness": "Faithfulness (grounded answers)",
        "fact_coverage": "Fact coverage",
        "abstention_accuracy": "Abstention accuracy (unanswerable Qs)",
        "latency_p50_ms": "Latency p50 (ms)",
        "latency_p95_ms": "Latency p95 (ms)",
    }
    for key, label in pretty.items():
        val = summary.get(key)
        if val is not None:
            lines.append(f"| {label} | {val} |")
    with open(os.path.join(HERE, "results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
