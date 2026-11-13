---
title: Recruitment FairTrace AI
emoji: 🛩️
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
pinned: false
license: mit
short_description: Screen CVs fast, fairly and with proof (GenAI prototype)
---

# 🛩️ Recruitment FairTrace AI

**An auditable GenAI CV screening assistant: screen CVs fast, fairly and with proof.**

▶️ **Live demo:** https://huggingface.co/spaces/edwardwww/recruitment-fairtrace-ai
📦 **Data:** https://huggingface.co/datasets/edwardwww/recruitment-fairtrace-ai-data

Built for the IS5542 *GenAI in Business* group project at City University of Hong Kong.
**All CVs and data are synthetic.**

## The problem

AI CV screeners are fast, but they can be unfair and cannot explain themselves. In our earlier
CV Screening Bias Lab, a naive AI recruiter gave an identical CV fewer points when it showed a
2-year parental break, and said the gap was the reason.

## The solution: Rubric → Blind → Trace → Audit

| Tab | What it does | GenAI technique |
|---|---|---|
| **① Fair Rubric** | Reviews the job ad for risky wording ("young", "no career gaps", "native English speaker"), suggests a fairer ad and builds a job-related scoring rubric for HR to approve | LLM review + fixed word list; structured JSON output |
| **② Blind & Score** | A small LLM finds sensitive details, Python removes them; a larger LLM scores each rubric criterion and must quote the CV; Python checks every quote. Compared side by side with the naive AI | Information extraction, rubric prompting, evidence verification |
| **③ FairTrace Auditor** | A bounded AI agent tests the screener with counterfactual CVs, checks the reasons, tries fixes and waits for a human to approve | Agentic AI (plan → act → observe), tool use |
| **④ Decision Trace** | Every model call is recorded (model, temperature, prompt version, input hash, raw output, tokens, cost); an LLM drafts an explanation for the applicant | Logging + LLM explanation |

Verdicts ("bias / no bias") are computed by statistics, not by the LLM. The AI never decides alone.

## Models (Hugging Face Inference Providers)

| Role | Model |
|---|---|
| FairTrace scorer, job-ad reviewer, rubric builder, agent planner | `Qwen/Qwen3-235B-A22B-Instruct-2507` |
| Blind Parser (finds sensitive details) | `meta-llama/Llama-3.3-70B-Instruct` |
| Naive baseline (the earlier demo) | `Qwen/Qwen2.5-72B-Instruct` |

## Run locally

```bash
pip install -r requirements.txt
python app.py                     # shows the saved run in cache/replay.json
HF_TOKEN=hf_... python build_cache.py   # run every model again and save a new replay
```

On the Space, the live buttons need two secrets: `HF_TOKEN` and `APP_PASSWORD` (owner password,
so visitors cannot spend the owner's credits).

## Files

| File | Purpose |
|---|---|
| `app.py` | Gradio interface (4 steps + About) |
| `build_cache.py` | Runs the whole pipeline with real model calls and saves `cache/replay.json` |
| `fairtrace/llm.py` | Model calls, cost estimate, JSON parsing |
| `fairtrace/trace.py` | Decision Trace recorder (JSONL) |
| `fairtrace/rubric.py` | Job-ad review and rubric builder |
| `fairtrace/screening.py` | Naive baseline, Blind Parser, Evidence Scorer, applicant letter |
| `fairtrace/auditor.py` | FairTrace Auditor agent and audit report |
| `fairtrace/candidates.py` | The risky job ad and the batch of six synthetic applicants |
| `fairtrace/cv_data.py`, `variants.py` | Synthetic Hong Kong jobs and CV templates (from the earlier Bias Lab) |
| `fairtrace/ui.py` | HTML rendering |

## Limitations and ethics

Illustrative prototype, not a scientific or legal audit: one job, six applicants, three runs per CV (five in the audit).
Do not use it to find "best-scoring" names or to optimise a CV against a screener.
AI tools (Claude) helped write the code; the project group designed the solution and checks the results.

Licensed under the [MIT License](LICENSE).
