"""Export cache/replay.json into simple files for the Hugging Face dataset (dataset/ folder)."""

import json
from pathlib import Path

ROOT = Path(__file__).parent
D = json.loads((ROOT / "cache" / "replay.json").read_text(encoding="utf-8"))
OUT = ROOT / "dataset"
OUT.mkdir(exist_ok=True)


def jsonl(name, rows):
    (OUT / name).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


jsonl("applicants.jsonl", [{
    "id": r["id"], "difference": r["difference"], "truly_qualified": r["qualified"], "cv": r["cv"],
    "blind_cv": r["blind"]["blind_cv"], "removed": r["blind"]["removed"],
    "naive_score": r["naive"]["score"], "naive_runs": r["naive"]["scores"], "naive_reasons": r["naive"]["reasons"],
    "fairtrace_score": r["fair"]["score"], "fairtrace_runs": r["fair"]["scores"],
    "fairtrace_criteria": r["fair"]["runs"][0]["criteria"], "evidence_valid_pct": r["fair"]["evidence_valid"],
    "applicant_letter": r.get("letter", "")} for r in D["screen"]["rows"]])
(OUT / "job_ad_review.json").write_text(json.dumps({k: D["rubric"][k] for k in ("risky_ad", "lint", "approved_ad", "criteria")},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
audit = {k: v for k, v in D["audit"].items() if k != "trace"}
(OUT / "audit_run.json").write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
jsonl("decision_trace.jsonl", D["rubric"]["trace"] + D["screen"]["trace"] + D["audit"]["trace"])

(OUT / "README.md").write_text("""---
license: mit
language: [en]
tags: [synthetic, fairness, hiring, llm-evaluation, audit]
pretty_name: Recruitment FairTrace AI data
size_categories: [n<1K]
---

# Recruitment FairTrace AI - data

Synthetic data and saved model outputs behind the
[Recruitment FairTrace AI](https://huggingface.co/spaces/edwardwww/recruitment-fairtrace-ai) demo
(IS5542 GenAI in Business, City University of Hong Kong). **Every CV, name and job ad is invented.**

| File | Content |
|---|---|
| `applicants.jsonl` | Six synthetic applicants for one Hong Kong Marketing Executive job. A1-A5 have identical qualifications and differ in one personal detail (name, age, parental break, disability signal); A6 is less qualified. Each row has the original CV, the blinded CV, what was removed, the naive AI score and reasons, the FairTrace rubric score with quoted evidence, and the AI-drafted applicant letter. |
| `job_ad_review.json` | A job ad with risky wording, the flagged phrases, the rewritten ad and the scoring rubric. |
| `audit_run.json` | One run of the FairTrace Auditor agent: counterfactual tests, forensics, fixes re-tested, agent steps. |
| `decision_trace.jsonl` | Every model call: component, model, temperature, prompt version, input hash, raw output, tokens, estimated cost, latency. |

Models: Qwen/Qwen3-235B-A22B-Instruct-2507 (FairTrace), meta-llama/Llama-3.3-70B-Instruct (Blind Parser),
Qwen/Qwen2.5-72B-Instruct (naive baseline), via Hugging Face Inference Providers.

Illustrative, small-sample data for teaching. Not a scientific audit. Do not use it to optimise CVs against screeners.
""", encoding="utf-8")
print("exported", sorted(p.name for p in OUT.iterdir()))
