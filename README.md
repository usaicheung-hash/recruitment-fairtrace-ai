---
title: Recruitment FairTrace AI
emoji: 🛩️
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: 6.32.0
python_version: "3.12"
app_file: app.py
pinned: false
license: mit
short_description: Screen CVs fast, fairly and with proof (GenAI prototype)
---

<img src="assets/logo.svg" width="72" align="left" alt="logo">

# Recruitment FairTrace AI

**An auditable GenAI CV screening assistant: screen CVs fast, fairly and with proof.**

▶️ **Live demo:** https://huggingface.co/spaces/edwardwww/recruitment-fairtrace-ai
📖 **Step-by-step user guide:** [English](docs/USER_GUIDE_EN.md) · [中文（繁體）](docs/USER_GUIDE_ZH.md)
📦 **Data:** https://huggingface.co/datasets/edwardwww/recruitment-fairtrace-ai-data

Built for the IS5542 *GenAI in Business* group project at City University of Hong Kong.
**All CVs and data are synthetic.**

![Header](docs/img/00_header.png)

## The problem

AI CV screeners are fast, but they can be unfair and cannot explain themselves. In our earlier
CV Screening Bias Lab, a naive AI recruiter gave an identical CV fewer points when it showed a
2-year parental break, and said the gap was the reason.

## The solution: Rubric → Blind → Score → Audit → Trace

| Page | What it does | GenAI technique |
|---|---|---|
| **🚀 Introduction** | Intro video, the problem, who it is for, and the match: naive AI vs FairTrace (with confetti) | - |
| **① Fair Rubric** | Reviews the job ad for risky wording, suggests fairer wording and builds a job-related scoring rubric for HR to approve | LLM review + fixed word list; structured JSON output |
| **② Blind & Score** | An LLM finds personal details and Python removes them; a second LLM scores each rubric criterion and must quote the CV; Python checks every quote. Compared side by side with a naive AI | Information extraction, rubric prompting, evidence verification |
| **③ FairTrace Auditor** | A bounded AI agent tests the screener with counterfactual CVs, checks its reasons, tries fixes and waits for a human to approve | Agentic AI (plan → act → observe), tool use |
| **④ Decision Trace** | Every model call is recorded; an LLM drafts an explanation for the applicant | Logging + LLM explanation |
| **📊 Model choice** | Three models x two methods on the same applicants | Model benchmark |
| **🏁 Summary** | The whole test on one page | - |

Verdicts ("bias / no bias") are computed by statistics, not by the LLM. The AI never decides alone.

## Screenshot tour

### ① Fair Rubric: bias often starts in the job ad
The AI reviewer and a fixed word list find risky phrases and suggest fairer wording. The word list also re-checks
the AI's own rewrite: here it still contained "2020 or later", so HR must edit it.

![Job ad review](docs/img/01_rubric_review.png)

After HR accepts, the AI builds a job-related rubric with weights.

![Rubric](docs/img/02_rubric_approved.png)

### ② Blind & Score: same applicants, two screeners
Five applicants have identical qualifications and differ in one personal detail. The naive AI spreads them out;
FairTrace keeps them close and every point has evidence.

![Key numbers](docs/img/03b_score_kpis.png)
![Score spread](docs/img/03_score_spread.png)
![All applicants](docs/img/04_score_all.png)

Open one applicant to see what was removed before scoring, and the CV quote behind every point.

![Original vs blind CV](docs/img/05_applicant_blind.png)
![Evidence](docs/img/06_applicant_evidence.png)

### ③ FairTrace Auditor: an AI agent audits the screener
The agent tests each personal detail with counterfactual CVs, reads the screener's reasons, tries a prompt fix and the
FairTrace pipeline, then waits for a human.

![Agent timeline](docs/img/07_audit_timeline.png)
![Audit result for one attribute](docs/img/08_audit_attribute.png)
![Human approval](docs/img/09_audit_approved.png)

### ④ Decision Trace: every AI decision can be traced
![Trace numbers](docs/img/10_trace_kpis.png)
![Letter to the applicant](docs/img/11_trace_letter.png)
![One recorded call](docs/img/12_trace_call.png)

### 📊 Model choice
With the naive prompt every model shows a gap; with the FairTrace method the chosen model is the fairest and steadiest.

![Model choice](docs/img/13_model_choice.png)

### 🏁 Summary
![Summary numbers](docs/img/14_summary_kpis.png)
![Summary charts](docs/img/14b_summary_charts.png)
![Scorecard](docs/img/14c_summary_scorecard.png)

## Models (Hugging Face Inference Providers)

| Role | Model |
|---|---|
| FairTrace scorer, job-ad reviewer, rubric builder, agent planner, letter | `Qwen/Qwen3-235B-A22B-Instruct-2507` |
| Blind Parser (finds personal details) | `meta-llama/Llama-3.3-70B-Instruct` |
| Naive baseline (the earlier demo) | `Qwen/Qwen2.5-72B-Instruct` |

## Run locally

```bash
pip install -r requirements.txt
python app.py                           # shows the saved run in cache/replay.json
HF_TOKEN=hf_... python build_cache.py   # run every model again and save a new replay
HF_TOKEN=hf_... python benchmark.py     # model benchmark
python export_dataset.py                # tables for the Hugging Face dataset
python docs/make_screenshots.py         # screenshots for this README (needs playwright)
```

On the Space, the live buttons need two secrets: `HF_TOKEN` and `APP_PASSWORD` (owner password,
so visitors cannot spend the owner's credits).

## Files

| File | Purpose |
|---|---|
| `app.py` | Gradio interface |
| `build_cache.py` | Runs the whole pipeline with real model calls and saves `cache/replay.json` |
| `benchmark.py` | Model selection test: 3 models x 2 methods (`cache/benchmark.json`) |
| `export_dataset.py` | Flat tables for the Hugging Face dataset |
| `fairtrace/llm.py` | Model calls, cost estimate, JSON parsing |
| `fairtrace/trace.py` | Decision Trace recorder (JSONL) |
| `fairtrace/rubric.py` | Job-ad review and rubric builder |
| `fairtrace/screening.py` | Naive baseline, Blind Parser, Evidence Scorer, applicant letter |
| `fairtrace/auditor.py` | FairTrace Auditor agent and audit report |
| `fairtrace/candidates.py` | The risky job ad and the six synthetic applicants |
| `fairtrace/cv_data.py`, `variants.py` | Synthetic Hong Kong jobs and CV templates (from the earlier Bias Lab) |
| `fairtrace/ui.py`, `ui_extra.py`, `ui_intro.py` | HTML rendering: charts, header with logo, Summary and Introduction pages |
| `docs/` | User guides (English, Chinese), screenshots and the screenshot script |

## Limitations and ethics

Illustrative prototype, not a scientific or legal audit: one job, six applicants, three runs per CV (five in the audit).
Model answers vary between runs, which is why FairTrace measures noise and keeps auditing.
Do not use it to find "best-scoring" names or to optimise a CV against a screener.
AI tools (Claude) helped write the code; the project group designed the solution and checks the results.

Licensed under the [MIT License](LICENSE).
