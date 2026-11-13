"""Run the whole FairTrace pipeline once with real model calls and save it for replay.

    HF_TOKEN=... python build_cache.py            # everything
    HF_TOKEN=... python build_cache.py screen     # only one part: rubric | screen | audit

The presentation uses this saved run (cache/replay.json), so it shows the same numbers every time.
"""

import json
import sys
from pathlib import Path

from fairtrace import auditor, candidates as C, rubric, screening, trace
from fairtrace.cv_data import JOBS

OUT = Path(__file__).with_name("cache") / "replay.json"


def load() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}


def save(d: dict):
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def do_rubric(d):
    run = trace.new_run_id("rubric")
    lint = rubric.lint(C.RISKY_AD, run_id=run)
    approved_ad = lint["rewritten_ad"] or JOBS[C.DEMO_JOB]
    crit = rubric.build_rubric(approved_ad, run_id=run)
    d["rubric"] = {"run_id": run, "risky_ad": C.RISKY_AD, "lint": lint, "approved_ad": approved_ad,
                   "criteria": crit, "trace": trace.records(run_id=run)}
    print("rubric:", [c["name"] for c in crit])


def do_screen(d):
    crit = d["rubric"]["criteria"]
    run = trace.new_run_id("screen")
    rows = []
    for a in C.applicants():
        naive = screening.naive_score(JOBS[C.DEMO_JOB], a["cv"], a["id"], run)
        b = screening.blind(a["cv"], a["id"], run, candidate_label=f"Candidate {a['id']}")
        fair = screening.evidence_score(b["blind_cv"], crit, a["id"], run)
        rows.append({**a, "naive": naive, "blind": b, "fair": fair})
        print(a["id"], a["difference"], "naive", naive["score"], "fair", fair["score"], "evidence", fair["evidence_valid"])
    # top-3 shortlist by each method, then a candidate letter from the FairTrace result
    for key in ("naive", "fair"):
        order = sorted(rows, key=lambda r: -r[key]["score"])
        for rank, r in enumerate(order, 1):
            r[key]["rank"] = rank
            r[key]["shortlist"] = rank <= 3
    for r in rows:
        decision = "invited to interview" if r["fair"]["score"] >= 70 else "not shortlisted this time"
        r["letter"] = screening.letter(C.DEMO_JOB, r["fair"], decision, r["id"], run)
    d["screen"] = {"run_id": run, "job": C.DEMO_JOB, "rows": rows, "trace": trace.records(run_id=run)}


def do_audit(d):
    a = auditor.Audit(C.DEMO_JOB, screener="naive", rubric=d["rubric"]["criteria"])
    for step in a.run():
        print(step["n"], step["tool"], step["args"], "->", step["observation"][:150])
    d["audit"] = a.to_dict()


if __name__ == "__main__":
    parts = sys.argv[1:] or ["rubric", "screen", "audit"]
    data = load()
    for p in parts:
        {"rubric": do_rubric, "screen": do_screen, "audit": do_audit}[p](data)
        save(data)
    print("saved", OUT)
