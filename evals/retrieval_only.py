"""Retrieval-only metrics (no LLM key needed).

A convenience entry point that runs just the retrieval half of the eval set, so
you can measure context precision / recall / MRR / latency without spending any
API tokens. The full `run_evals.py` adds LLM-judged faithfulness on top.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag import RagEngine                       # noqa: E402
from evals.run_evals import load_eval_set, retrieval_metrics  # noqa: E402


def main() -> None:
    engine = RagEngine.load()
    cases = [c for c in load_eval_set() if c["answerable"]]

    precisions, recalls, mrrs, latencies = [], [], [], []
    for case in cases:
        t0 = time.perf_counter()
        retrieved = engine.retrieve(case["question"])
        latencies.append((time.perf_counter() - t0) * 1000)
        sources = [c.source for c, _ in retrieved]
        rm = retrieval_metrics(sources, case["relevant_sources"])
        precisions.append(rm["precision"])
        recalls.append(rm["recall"])
        mrrs.append(rm["mrr"])

    summary = {
        "n_answerable": len(cases),
        "context_precision": round(statistics.mean(precisions), 3),
        "context_recall": round(statistics.mean(recalls), 3),
        "mrr": round(statistics.mean(mrrs), 3),
        "retrieval_latency_p50_ms": round(statistics.median(latencies), 1),
        "retrieval_latency_p95_ms": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 1),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
