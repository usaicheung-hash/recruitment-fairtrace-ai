"""Export cache/replay.json into flat tables for the Hugging Face dataset (dataset/ folder).

Every file is JSON Lines with the same columns on every row, and each file is its own config in the
dataset card, so the Hugging Face Dataset Viewer can show all of them.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
D = json.loads((ROOT / "cache" / "replay.json").read_text(encoding="utf-8"))
OUT = ROOT / "dataset"
OUT.mkdir(exist_ok=True)
for old in OUT.glob("*"):
    old.unlink()


def jsonl(name, rows):
    (OUT / name).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def s(x) -> str:
    return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)


# 1. applicants: one row per applicant
jsonl("applicants.jsonl", [{
    "id": r["id"], "name": r["name"], "difference": r["difference"], "truly_qualified": r["qualified"],
    "naive_score": r["naive"]["score"], "fairtrace_score": r["fair"]["score"],
    "naive_runs": [float(x) for x in r["naive"]["scores"]], "fairtrace_runs": [float(x) for x in r["fair"]["scores"]],
    "evidence_valid_pct": r["fair"]["evidence_valid"],
    "removed_details": [f"{x['type']}: {x['text']}" for x in r["blind"]["removed"]],
    "naive_reason": r["naive"]["reasons"][0], "applicant_letter": r.get("letter", ""),
    "cv": r["cv"], "blind_cv": r["blind"]["blind_cv"]} for r in D["screen"]["rows"]])

# 2. evidence: one row per applicant x criterion (first FairTrace run)
jsonl("evidence.jsonl", [{
    "id": r["id"], "criterion": c["criterion"], "weight": c["weight"], "score_0_5": c["raw"],
    "evidence_quote": c["evidence"], "quote_found_in_cv": c["verified"], "points": c["points"]}
    for r in D["screen"]["rows"] for c in r["fair"]["runs"][0]["criteria"]])

# 3. job ad review: one row per flagged phrase
jsonl("job_ad_flags.jsonl", [{
    "phrase": f.get("phrase", ""), "protected_ground": f.get("ground", ""), "why_risky": f.get("why", ""),
    "fairer_wording": f.get("rewrite", ""), "hong_kong_rule": f.get("law", "")} for f in D["rubric"]["lint"]["flags"]])

# 4. rubric
jsonl("rubric.jsonl", [{"criterion": c["name"], "weight": c["weight"], "evidence_needed": c.get("evidence_needed", "")}
                       for c in D["rubric"]["criteria"]])

# 5. audit: one row per attribute x CV copy x screener setting
A = D["audit"]
rows = []
for attr, res in A["results"].items():
    for setting, src in [("naive AI", res)] + [(f, A["fixes"][f][attr]) for f in A["fixes"] if attr in A["fixes"][f]]:
        for v in src["rows"]:
            rows.append({"attribute": attr, "setting": setting, "cv_copy": v["desc"], "mean_score": v["score"],
                         "runs": [float(x) for x in v["scores"]], "gap_for_attribute": src["gap"],
                         "verdict": src.get("level", "BIAS" if src["bias"] else "no bias")})
jsonl("audit_tests.jsonl", rows)

# 6. agent steps
jsonl("audit_steps.jsonl", [{"step": st["n"], "tool": st["tool"], "args": s(st.get("args") or {}),
                             "why": st.get("why", ""), "chosen_by": st.get("source", ""), "observation": st["observation"]}
                            for st in A["steps"]])

# 7. decision trace: every model call, same columns on every row
KEYS = ["id", "time", "run_id", "component", "subject", "model", "temperature", "prompt_version", "input_hash",
        "raw_output", "tokens_in", "tokens_out", "cost_usd", "latency_s"]
trace_rows = []
for r in D["rubric"]["trace"] + D["screen"]["trace"] + D["audit"]["trace"]:
    row = {k: r.get(k) for k in KEYS}
    if not row["raw_output"]:
        row["raw_output"] = s(r.get("observation", ""))
    row["model"] = row["model"] or ""
    row["temperature"] = float(row["temperature"]) if row["temperature"] is not None else None
    for k in ("tokens_in", "tokens_out"):
        row[k] = int(row[k] or 0)
    for k in ("cost_usd", "latency_s"):
        row[k] = float(row[k] or 0)
    trace_rows.append(row)
jsonl("decision_trace.jsonl", trace_rows)

CONFIGS = [("applicants", "Six synthetic applicants: original and blind CV, naive vs FairTrace scores, letter", True),
           ("evidence", "FairTrace rubric scores with the CV quote behind every point", False),
           ("job_ad_flags", "Risky phrases found in the job ad, with fairer wording and the Hong Kong rule", False),
           ("rubric", "The job-related scoring rubric", False),
           ("audit_tests", "Counterfactual bias tests by the FairTrace Auditor, before and after fixes", False),
           ("audit_steps", "Each step of the auditor agent (plan -> act -> observe)", False),
           ("decision_trace", "Every model call: model, temperature, prompt version, output, tokens, cost, time", False)]
yaml = "\n".join(f"- config_name: {n}\n  data_files: {n}.jsonl" + ("\n  default: true" if d else "") for n, _, d in CONFIGS)
table = "\n".join(f"| `{n}` | {desc} |" for n, desc, _ in CONFIGS)

(OUT / "README.md").write_text(f"""---
license: mit
language: [en]
tags: [synthetic, fairness, hiring, llm-evaluation, audit]
pretty_name: Recruitment FairTrace AI data
size_categories: [n<1K]
configs:
{yaml}
---

# Recruitment FairTrace AI - data

Synthetic data and saved model outputs behind the
[Recruitment FairTrace AI](https://huggingface.co/spaces/edwardwww/recruitment-fairtrace-ai) demo
(IS5542 GenAI in Business, City University of Hong Kong). **Every CV, name and job ad is invented.**

Choose a table (config) in the Dataset Viewer above:

| Config | Content |
|---|---|
{table}

Applicants A1-A5 have identical qualifications and differ in one personal detail (name, age, parental break,
disability signal); A6 is less qualified. A fair screener should give A1-A5 the same score.

Models: Qwen/Qwen3-235B-A22B-Instruct-2507 (FairTrace scorer, job-ad reviewer, agent),
meta-llama/Llama-3.3-70B-Instruct (Blind Parser), Qwen/Qwen2.5-72B-Instruct (naive baseline),
via Hugging Face Inference Providers.

Illustrative, small-sample data for teaching. Not a scientific audit. Do not use it to optimise CVs against screeners.
""", encoding="utf-8")
print("exported", sorted(p.name for p in OUT.iterdir()))
