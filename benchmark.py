"""Model selection benchmark: the same six applicants, three candidate models, two methods.

    HF_TOKEN=... python benchmark.py      -> cache/benchmark.json

Metrics per (model, method):
  spread      score gap among the five equally qualified CVs (lower = fairer)
  sd          average run-to-run spread for one CV (lower = more consistent)
  separation  mean score of qualified CVs minus the less-qualified CV (higher = still tells good from weak)
  evidence    % of rubric points backed by a verified CV quote (FairTrace only)
  cost / sec  estimated US$ and model seconds per CV
"""

import json
from pathlib import Path
from statistics import mean

from fairtrace import candidates as C, llm, screening, trace
from fairtrace.cv_data import JOBS

ROOT = Path(__file__).parent
REPLAY = json.loads((ROOT / "cache" / "replay.json").read_text(encoding="utf-8"))
MODELS = ["Qwen/Qwen3-235B-A22B-Instruct-2507", "Qwen/Qwen2.5-72B-Instruct", "meta-llama/Llama-3.3-70B-Instruct"]


def metrics(rows, key, recs):
    q = [r[key]["score"] for r in rows if r["qualified"]]
    weak = [r[key]["score"] for r in rows if not r["qualified"]]
    s = trace.summary(recs)
    out = {"spread": round(max(q) - min(q), 1), "sd": round(mean(r[key]["sd"] for r in rows), 1),
           "separation": round(mean(q) - mean(weak), 1),
           "cost_per_cv": round(s["cost_usd"] / len(rows), 5), "sec_per_cv": round(s["seconds"] / len(rows), 1)}
    if key == "fair":
        out["evidence"] = round(mean(r["fair"]["evidence_valid"] for r in rows))
    return out


def main():
    crit = REPLAY["rubric"]["criteria"]
    results = []
    for model in MODELS:
        for method in ("naive", "fair"):
            run = trace.new_run_id(f"bench-{llm.short(model)}-{method}")
            rows = []
            for r in REPLAY["screen"]["rows"]:
                if method == "naive":
                    res = screening.naive_score(JOBS[C.DEMO_JOB], r["cv"], r["id"], run, model=model)
                else:
                    res = screening.evidence_score(r["blind"]["blind_cv"], crit, r["id"], run, model=model)
                rows.append({"qualified": r["qualified"], method: res})
            m = {"model": model, "method": method, **metrics(rows, method, trace.records(run_id=run)),
                 "scores": {r["id"]: x[method]["score"] for r, x in zip(REPLAY["screen"]["rows"], rows)}}
            results.append(m)
            print(m)
    (ROOT / "cache" / "benchmark.json").write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
