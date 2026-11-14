"""Recruitment FairTrace AI - an auditable GenAI CV screening assistant (IS5542 GenAI in Business, CityU).

Four steps: ① Fair Rubric  ② Blind & Score  ③ FairTrace Auditor  ④ Decision Trace.
The presentation uses a saved real run (cache/replay.json). Running the models again needs the owner
password (Space secret APP_PASSWORD) and HF_TOKEN. All CVs and data are synthetic.
"""

import base64
import copy
import hmac
import json
import os
import tempfile
import time
from pathlib import Path

import gradio as gr

from fairtrace import auditor, llm, screening, trace, ui, ui_extra, ui_intro
from fairtrace import candidates as C

INTRO_VIDEO = Path(__file__).parent / "assets" / "intro.mp4"
REPLAY = json.loads((Path(__file__).parent / "cache" / "replay.json").read_text(encoding="utf-8"))
_bench = Path(__file__).parent / "cache" / "benchmark.json"
BENCH = json.loads(_bench.read_text(encoding="utf-8")) if _bench.exists() else []
for part in ("rubric", "screen", "audit"):
    trace.load(REPLAY[part]["trace"])
TIE_BAND = 3  # points: smaller differences are within the screeners' own run-to-run noise
for _key in ("naive", "fair"):  # same rule for both: top 3, plus anyone within TIE_BAND of the 3rd score
    _rows = REPLAY["screen"]["rows"]
    _third = sorted((o[_key]["score"] for o in _rows), reverse=True)[2]
    for _r in _rows:
        _r[_key]["rank"] = 1 + sum(o[_key]["score"] > _r[_key]["score"] for o in _rows)
        _r[_key]["shortlist"] = _r[_key]["score"] >= _third - TIE_BAND
ROWS = {r["id"]: r for r in REPLAY["screen"]["rows"]}
CHOICES = [f"{r['id']} · {r['name']} ({r['difference']})" for r in REPLAY["screen"]["rows"]]

LOCKED = "🔒 Running the AI again uses the owner's paid credits: enter the owner password at the top. Saved results are free to view."


def password_ok(pw: str) -> bool:
    secret = os.environ.get("APP_PASSWORD", "")
    return bool(secret and pw) and hmac.compare_digest(pw.strip().encode(), secret.encode())


def _file(name: str, text: str) -> str:
    path = Path(tempfile.gettempdir()) / name
    path.write_text(text, encoding="utf-8")
    return str(path)


# ------------------------------------------------------------------ tab 1
def show_rubric():
    return gr.update(value=ui.rubric_approved_html(REPLAY["rubric"]), visible=True)


# ------------------------------------------------------------------ tab 2
def show_candidate(choice: str):
    return ui.candidate_html(ROWS[choice.split(" · ")[0]])


def live_cv(cv: str, pw: str):
    if not password_ok(pw):
        return ui.wrap(f"<div class='card'>{LOCKED}</div>")
    if len((cv or "").strip()) < 80:
        return ui.wrap("<div class='card'>Please paste a CV (at least a few lines).</div>")
    run = trace.new_run_id("live")
    b = screening.blind(cv, "live", run, "Candidate")
    f = screening.evidence_score(b["blind_cv"], REPLAY["rubric"]["criteria"], "live", run)
    return ui.live_cv_html(b, f)


# ------------------------------------------------------------------ tab 3
def replay_audit(state):
    a = REPLAY["audit"]
    shown = []
    for st in a["steps"]:
        yield ui.timeline_html(shown, running=True), gr.update(), None
        time.sleep(0.8)
        shown.append(st)
        yield ui.timeline_html(shown), gr.update(), None
    yield ui.timeline_html(shown), ui.audit_results_html(a), copy.deepcopy(a)


def live_audit(pw: str):
    if not password_ok(pw):
        yield ui.wrap(f"<div class='card'>{LOCKED}</div>"), gr.update(), None
        return
    a = auditor.Audit(C.DEMO_JOB, screener="naive", rubric=REPLAY["rubric"]["criteria"])
    shown = []
    yield ui.timeline_html(shown, running=True), gr.update(), None
    for st in a.run():
        shown.append(st)
        yield ui.timeline_html(shown, running=st["tool"] != "finish"), gr.update(), None
    d = a.to_dict()
    yield ui.timeline_html(shown), ui.audit_results_html(d), d


def decide(a, decision: str):
    if not a:
        return ui.wrap("<div class='card'>Run or replay the audit first.</div>"), gr.update(visible=False)
    note = f"{decision} at {time.strftime('%Y-%m-%d %H:%M')}"
    trace.record({"run_id": a["run_id"], "component": "human.approval", "subject": "fix", "observation": note})
    a["trace"] = trace.records(run_id=a["run_id"])
    return ui.audit_results_html(a, note), gr.update(value=_file("fairtrace_audit_report.md", auditor.report_md(a, note)), visible=True)


# ------------------------------------------------------------------ tab 4
def show_trace(choice: str):
    cid = choice.split(" · ")[0]
    recs = [r for r in REPLAY["screen"]["trace"] if r.get("subject") == cid]
    return ui.trace_html(recs, ROWS[cid].get("letter", ""))


def download_trace():
    recs = REPLAY["rubric"]["trace"] + REPLAY["screen"]["trace"] + REPLAY["audit"]["trace"]
    return gr.update(value=_file("fairtrace_decision_trace.jsonl", trace.to_jsonl(recs)), visible=True)


ABOUT = f"""
## About Recruitment FairTrace AI

A prototype for the **IS5542 GenAI in Business** group project (City University of Hong Kong).
**Business problem:** AI CV screeners are fast but can be unfair and cannot explain themselves. In our earlier
test, a naive AI recruiter gave an identical CV 5 points less when it showed a 2-year parental break, and said so in its reason.

**FairTrace = Rubric → Blind → Trace → Audit**

| Step | GenAI technique | Model |
|---|---|---|
| ① Fair Rubric | LLM review of the job ad (+ fixed word list) and structured JSON rubric | {llm.short(llm.SCORER_MODEL)} |
| ② Blind Parser | Small LLM finds sensitive details; Python removes them and lists every removal | {llm.short(llm.REDACT_MODEL)} |
| ② Evidence Scorer | Rubric prompt, low temperature, 3 runs; must quote the CV; Python verifies quotes | {llm.short(llm.SCORER_MODEL)} |
| ③ FairTrace Auditor | Bounded agent (plan → act → observe), 4 tools, max {auditor.MAX_STEPS} steps, human approval | {llm.short(llm.SCORER_MODEL)} |
| ④ Decision Trace | Every model call logged (model, temperature, prompt version, input hash, output, tokens, cost); LLM explanation letter | - |
| Baseline | The naive "rate 0-100" prompt from the earlier CV Screening Bias Lab | {llm.short(llm.NAIVE_MODEL)} |

**Why no fine-tuning?** Little data, high cost, and a model fine-tuned on past hiring decisions learns past bias.
A rubric, blinding and verification are cheaper, explainable and easy to update.

**Hong Kong context:** Sex, Disability, Family Status and Race Discrimination Ordinances; PCPD *Artificial Intelligence:
Model Personal Data Protection Framework* (2024): human oversight, data minimisation, testing and monitoring.

### Ethics and limits
- **All CVs and data are synthetic.** No real person's data is used.
- Illustrative prototype, not a scientific or legal audit: one job, six applicants, few runs.
- The AI never decides alone: HR approves the rubric, every fix and every final decision.
- Do not use this tool to find "best-scoring" names or to optimise a CV against a screener.
- AI tools (Claude) helped write the code; the project group designed the solution and checks the results.

Data: [edwardwww/recruitment-fairtrace-ai-data](https://huggingface.co/datasets/edwardwww/recruitment-fairtrace-ai-data) ·
Code: [GitHub](https://github.com/usaicheung-hash/recruitment-fairtrace-ai)
"""

POSTER = Path(__file__).parent / "assets" / "intro_poster.jpg"
POSTER_URI = ("data:image/jpeg;base64," + base64.b64encode(POSTER.read_bytes()).decode()) if POSTER.exists() else ""

# Runs once in the browser: light mode, the video poster (00:02 frame) and the confetti trigger.
# The confetti only plays while the match card is on screen, so it fires when the visitor scrolls to it
# (and again after "Celebrate again"), instead of finishing unseen while the video is on screen.
FORCE_LIGHT = """() => {
  // only touch the class when it is there: removing an absent class still fires the observer (endless loop)
  const light = () => { if (document.body.classList.contains('dark')) document.body.classList.remove('dark');
    document.querySelectorAll('.dark').forEach(e => e.classList.remove('dark')); };
  light(); new MutationObserver(light).observe(document.body, {attributes: true});
  document.body.classList.add('js-ft');
  const poster = "%s";
  setInterval(() => {
    if (poster) document.querySelectorAll('#intro-video video').forEach(v => {
      if (v.getAttribute('poster') !== poster) v.setAttribute('poster', poster); });
    document.querySelectorAll('.ft .vs').forEach(el => {
      const r = el.getBoundingClientRect();
      const seen = r.width > 0 && r.top < window.innerHeight * 0.75 && r.bottom > window.innerHeight * 0.25;
      if (seen && !el.classList.contains('go')) el.classList.add('go');
      if (!seen && r.width > 0 && el.classList.contains('go')) el.classList.remove('go');
    });
  }, 300);
}""" % POSTER_URI

STEPS = [("① Rubric", "fair job ad", "#0284c7"), ("② Blind", "hide personal data", "#db2777"),
         ("③ Score", "quote every point", "#4f46e5"), ("④ Audit", "agent tests bias", "#d97706"),
         ("⑤ Trace", "log every call", "#16a34a")]
HERO = ui_extra.hero_html(STEPS)

SHELL_CSS = """
.gradio-container{max-width:1180px !important}
button[role=tab]{font-weight:700 !important;font-size:15px !important}
"""

with gr.Blocks(title="Recruitment FairTrace AI") as demo:
    gr.HTML(HERO)
    with gr.Accordion("🔒 Owner controls (only needed to run the AI live; saved results are free)", open=False):
        pw = gr.Textbox(label="Owner password", type="password", max_lines=1)
    P = dict(api_visibility="private")
    with gr.Tabs():
        with gr.Tab("🚀 Introduction"):
            gr.Markdown("### Fair, explainable CV screening for HR, in four minutes")
            if INTRO_VIDEO.exists():
                gr.Video(value=str(INTRO_VIDEO), label="Introduction video (3:55)", autoplay=False, height=520,
                         elem_id="intro-video")
            n0 = gr.State(0)
            h0 = gr.HTML(ui_intro.intro_html(REPLAY))
            b0 = gr.Button("🎉 Celebrate again", size="sm")
            b0.click(lambda n: (ui_intro.intro_html(REPLAY, n + 1), n + 1), n0, [h0, n0], **P)

        with gr.Tab("① Fair Rubric"):
            gr.Markdown("### Bias often starts in the job ad")
            gr.HTML(ui.rubric_lint_html(REPLAY["rubric"]))
            b1 = gr.Button("✅ HR accepts the rewrite → build the rubric", variant="primary")
            r1 = gr.HTML(visible=False)
            b1.click(show_rubric, None, r1, **P)

        with gr.Tab("② Blind & Score"):
            gr.Markdown("### Same applicants, two screeners")
            gr.HTML(ui.screen_table_html(REPLAY["screen"]))
            c2 = gr.Dropdown(CHOICES, value=CHOICES[1], label="Open an applicant")
            h2 = gr.HTML(show_candidate(CHOICES[1]))
            c2.change(show_candidate, c2, h2, **P)
            with gr.Accordion("🧪 Try your own CV (live, needs owner password)", open=False):
                t2 = gr.Textbox(lines=10, label="Paste a CV for the Marketing Executive job (synthetic only, no real personal data)")
                l2 = gr.Button("Score with FairTrace")
                o2 = gr.HTML()
                l2.click(live_cv, [t2, pw], o2, **P)

        with gr.Tab("③ FairTrace Auditor"):
            gr.Markdown("### An AI agent audits the naive screener: test → find the cause → try a fix → a human decides")
            with gr.Row():
                b3 = gr.Button("▶ Replay saved audit", variant="primary")
                b3l = gr.Button("🔄 Run live audit (about 3 minutes, owner only)", size="sm")
            st3 = gr.State()
            tl3 = gr.HTML(ui.timeline_html([]))
            res3 = gr.HTML()
            with gr.Row():
                ok3 = gr.Button("✅ Approve recommended fix")
                no3 = gr.Button("❌ Reject")
            f3 = gr.File(label="Audit report (Markdown)", visible=False)
            b3.click(replay_audit, st3, [tl3, res3, st3], **P)
            b3l.click(live_audit, pw, [tl3, res3, st3], **P)
            ok3.click(lambda a: decide(a, "Approved"), st3, [res3, f3], **P)
            no3.click(lambda a: decide(a, "Rejected"), st3, [res3, f3], **P)

        with gr.Tab("④ Decision Trace"):
            gr.Markdown("### Every AI decision can be traced")
            c4 = gr.Dropdown(CHOICES, value=CHOICES[1], label="Applicant")
            h4 = gr.HTML(show_trace(CHOICES[1]))
            c4.change(show_trace, c4, h4, **P)
            d4 = gr.Button("⬇ Download the full Decision Trace (JSONL)")
            f4 = gr.File(label="Decision Trace", visible=False)
            d4.click(download_trace, None, f4, **P)

        if BENCH:
            with gr.Tab("📊 Model choice"):
                gr.Markdown("### Why these models? Tested on our own data")
                gr.HTML(ui.benchmark_html(BENCH))

        with gr.Tab("🏁 Summary"):
            gr.Markdown("### The whole test in one page")
            gr.HTML(ui_extra.summary_html(REPLAY, BENCH))

        with gr.Tab("ℹ️ About & Ethics"):
            gr.Markdown(ABOUT)

if __name__ == "__main__":
    theme = gr.themes.Base(primary_hue="indigo", neutral_hue="slate",
                           font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"])
    demo.launch(theme=theme, css=SHELL_CSS, js=FORCE_LIGHT, footer_links=["gradio", "settings"])
