# Recruitment FairTrace AI: step-by-step user guide

Open the demo: **https://huggingface.co/spaces/edwardwww/recruitment-fairtrace-ai**

All CVs and data are synthetic. Every page opens with a saved real run, so you can use it without a password
and without spending any AI credits. (中文版： [USER_GUIDE_ZH.md](USER_GUIDE_ZH.md))

---

## 0. Before you start: the screen

![Header](img/00_header.png)

1. **Header**: the five steps of FairTrace: ① Rubric → ② Blind → ③ Score → ④ Audit → ⑤ Trace.
2. **Owner controls**: only for the owner, to run the AI live. You can skip it.
3. **Tabs**: go from left to right: *Fair Rubric → Blind & Score → FairTrace Auditor → Decision Trace →
   Model choice → Summary*. *About & Ethics* explains the models and limits.

**Colour code (same on every page)**

| Colour | Meaning |
|---|---|
| 🟠 orange | the **naive AI** (one prompt: "rate this CV 0-100"), the tool many companies use today |
| 🟣 purple | **FairTrace** |
| 🔴 red | bias or risk |
| 🟢 green | fixed, fair, approved |

Anything with ▶ (for example *How it works*, *Show raw*) can be clicked to open more detail.

---

## Step 1. ① Fair Rubric: check the job ad

![Job ad review](img/01_rubric_review.png)

1. Top left: **Risky phrases found**, with the type of risk (🎂 age, 👶 family, 🌏 race or nationality).
2. Left card: **the job ad HR wrote**. Red words are risky (for example "young and energetic", "no career gaps",
   "native English speaker").
3. Right card: **AI suggestions**. Each line shows the risky phrase (crossed out), the protected ground and the
   Hong Kong rule, and a fairer wording (green).
4. Look for the yellow tag **⚠ still risky: HR must edit**. The fixed word list checked the AI's own suggestion
   and found it still says "2020 or later". This shows why a human must review the AI.
5. Click **▶ Why each phrase is risky** for a one-line reason per phrase.
6. Click the purple button **✅ HR accepts the rewrite → build the rubric**.

![Rubric](img/02_rubric_approved.png)

7. The coloured bar shows the **scoring rubric**: five job-related criteria and their weights. Below it, what
   evidence earns points. Age, gender, family status, nationality, disability, name and career gaps are never scored.

---

## Step 2. ② Blind & Score: compare the two screeners

![Key numbers](img/03b_score_kpis.png)

1. Read the four numbers at the top (orange = naive AI → purple = FairTrace):
   - **Score spread** among five equally qualified CVs (lower = fairer).
   - **Qualified people wrongly cut** from the shortlist.
   - **Points backed by a verified quote**, and how many bad quotes Python caught.
   - **Cost per CV**.

![Score spread](img/03_score_spread.png)

2. The **dot chart**: each dot is one of the five equally qualified applicants (A1–A5). A fair screener puts them on
   top of each other. The orange band (naive AI) is wider than the purple band (FairTrace).

![All applicants](img/04_score_all.png)

3. **All 6 applicants**: orange bar = naive AI, purple bar = FairTrace, with *shortlisted* or *cut*. A6 really has
   less experience, so both screeners should score it lower.
4. Below the chart, use **Open an applicant** to choose a person (default: A2, the 2-year parental break).

![Original vs blind CV](img/05_applicant_blind.png)

5. Left: the **original CV**. Red, crossed-out text was removed before scoring (name, email, graduation year,
   career break, disability signals). Right: **what FairTrace sees**; green tags mark what was replaced.

![Evidence](img/06_applicant_evidence.png)

6. **FairTrace score**: each criterion, its score out of 5 and the exact CV quote used as evidence. Python checks
   that every quote is really in the CV; a quote that is not found earns 0 points.
7. At the bottom, **Naive AI: its reasons**. For A2 the naive AI says the career break "may affect recent industry
   knowledge": that is the bias.
8. (Owner only) **Try your own CV**: paste a synthetic CV and score it live.

---

## Step 3. ③ FairTrace Auditor: watch the AI agent audit the screener

1. Click **▶ Replay saved audit**. The agent works step by step (about 10 seconds).

![Agent timeline](img/07_audit_timeline.png)

2. Each step shows: the tool (🧪 test, 🔍 inspect reasons, 🛠 try fix, 🏁 finish), the result and a tag:
   **BIAS** (red), **⚠ POSSIBLE BIAS** (yellow) or **no bias** (green). The grey line says why the agent chose the step
   and whether the *AI planner* or a fixed *rule* chose it.

![Audit result](img/08_audit_attribute.png)

3. Below the timeline, one card per personal detail (name, age, career break, disability). Three columns, same scale:
   **Before (naive AI)**, **+ fairness rule in prompt**, **FairTrace pipeline**. Red bar = the copy that was scored
   lowest. The *gap* under each column is the difference between the highest and lowest copy.
4. If the agent inspected the reasons, you see a quote with the detail highlighted, or a note that the AI never
   mentioned it (a hidden bias).
5. Click **▶ How the verdict is decided**: BIAS = gap ≥ 3 points and more than twice the screener's own run-to-run
   noise; POSSIBLE BIAS = gap ≥ 3 points but within that noise.
6. Click **✅ Approve recommended fix** (or **❌ Reject**).

![Human approval](img/09_audit_approved.png)

7. The green banner confirms the human decision, and an **Audit report (Markdown)** appears to download.

---

## Step 4. ④ Decision Trace: check any decision

![Trace numbers](img/10_trace_kpis.png)

1. Choose an applicant. The top shows how many AI calls were recorded, tokens, cost and time.

![Letter](img/11_trace_letter.png)

2. **Explanation for the applicant**: the letter the AI drafted from the rubric results. It is sent only after a
   recruiter reviews it.
3. **Calls by component**: how many calls each part made (naive AI, Blind Parser, Evidence Scorer, Letter writer).

![One call](img/12_trace_call.png)

4. **Every call, in order**: time, component, model, temperature, time taken, a readable summary of the AI's answer
   and the cost. Click **▶ Show raw** to see the exact AI output, the prompt version and the input hash.
5. Click **⬇ Download the full Decision Trace (JSONL)** to save every record.

---

## Step 5. 📊 Model choice: why these models

![Model choice](img/13_model_choice.png)

1. Orange bars: the unfair spread with the naive prompt. Every model shows a gap.
2. Purple bars: the spread with the FairTrace method. The chosen model has the smallest gap.
3. Click **▶ Show all numbers** for run-to-run spread, separation (does it still tell strong from weak CVs?),
   evidence, cost and time per CV.

---

## Step 6. 🏁 Summary: the whole test on one page

![Summary numbers](img/14_summary_kpis.png)
![Summary charts](img/14b_summary_charts.png)
![Scorecard](img/14c_summary_scorecard.png)

1. Five key numbers: score spread, wrongly cut, evidence, bias flags, cost.
2. Left chart: each applicant's difference from the reference CV A1. Fair = on the 0 line.
3. Right chart: the bias gap for each personal detail before and after each fix.
4. **Naive AI vs FairTrace** scorecard, three business benefits and what we learned. Use this page to close a
   presentation.

---

## For the owner: live mode

![Owner controls](img/15_owner_controls.png)

1. In the Space **Settings → Variables and secrets**, add two **secrets** (not variables): `HF_TOKEN` (a Hugging Face
   token allowed to *Make calls to Inference Providers*) and `APP_PASSWORD` (any password you choose).
2. Open **🔒 Owner controls**, type the password, then use **🔄 Run live audit** (about 3 minutes, about US$0.02) or
   **Try your own CV**.
3. Live results change a little each time; that is normal for AI models. Use **Replay** for presentations.

To refresh the saved run on your computer: `HF_TOKEN=... python build_cache.py`, then `python benchmark.py`.

## Limits

Illustrative prototype on synthetic data: one job, six applicants, three to five runs per CV. Not a scientific or
legal audit. Do not use it to find "best-scoring" names or to optimise a CV against a screener.
