# Recruitment FairTrace AI - User guide

Live demo: https://huggingface.co/spaces/edwardwww/recruitment-fairtrace-ai
All CVs and data are synthetic. Every page opens with a saved real run, so it works without internet credits.

## The idea in one line

Rubric → Blind → Trace → Audit: the AI helps HR screen CVs fast, but every point it gives must be
backed by the CV, personal details are hidden from it, every call is recorded, and an AI agent keeps
testing the screener for bias. A human approves every important step.

## ① Fair Rubric

1. Read the job ad HR wrote. Red words are risky ("young and energetic", "no career gaps", "native English speaker").
2. The table explains each phrase: the protected ground, why it is risky, a fairer wording and the Hong Kong rule.
3. Press **✅ HR accepts the rewrite → build the rubric**. You see the cleaned ad and the five job-related criteria
   with weights. This rubric is used to score every CV.

## ② Blind & Score

1. The top row shows the headline numbers: score spread among five equally qualified CVs (naive AI vs FairTrace),
   share of points with verified evidence, cost and model time per CV.
2. The table shows the same six applicants scored by both screeners. A1-A5 have the same qualifications; only one
   personal detail differs. A6 is less qualified.
3. Choose an applicant in the drop-down. Left: the original CV with the removed details crossed out. Right: what the
   FairTrace scorer sees. Below: every criterion, the quote the AI used as evidence and whether Python found the quote
   in the CV (no quote, no points). At the bottom: the naive AI's score and reasons.
4. **Try your own CV** (owner only): paste a synthetic CV to score it live.

## ③ FairTrace Auditor

1. Press **▶ Replay saved audit**. The agent works step by step: it tests name, age, career break and disability with
   counterfactual CVs, inspects the reasons when it finds a gap, tries a fix and re-tests.
2. Each step shows the tool, the reason and whether the step was chosen by the AI planner or by the rule fallback.
3. The result table shows each gap, the noise, the verdict (computed by statistics: gap ≥ 3 points and more than twice
   the noise) and the gap after the fix.
4. Press **✅ Approve** or **❌ Reject**. The decision is recorded and a Markdown audit report is ready to download.
5. **Run live audit** (owner only) runs the agent again with real model calls (about 3 minutes).

## ④ Decision Trace

Choose an applicant to see every recorded model call (time, component, model, temperature, prompt version, input hash,
raw output, tokens, seconds) and the AI-drafted explanation letter. Download the full trace as JSONL.

## 📊 Model choice

Three models, two methods, same applicants. Lower spread and SD are fairer and steadier; separation shows the screener
still tells a strong CV from a weak one. The chosen setup is highlighted.

## For the owner: live mode

In the Space settings add two secrets: `HF_TOKEN` (a Hugging Face token allowed to call Inference Providers) and
`APP_PASSWORD`. Type the password in the box at the top to use the live buttons. To refresh the saved run locally:
`HF_TOKEN=... python build_cache.py` and `python benchmark.py`.

## Limits

Illustrative prototype on synthetic data: one job, six applicants, a few runs per CV. Model answers vary between runs;
that is why FairTrace measures noise and keeps auditing. Not a scientific or legal audit.
