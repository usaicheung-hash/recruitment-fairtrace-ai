"""Header (logo + animated banner) and the one-page Summary of the whole test."""

from __future__ import annotations

from . import llm, trace
from .rubric import lexicon_flags
from .ui import (BAD, CSS, FAIR, FIX_NAME, GOOD, NAIVE, NEUTRAL, WARN, audit_level, esc, level_chip, spread,
                 track, wrap)

# ================================================================== header and logo

LOGO_SVG = """<svg viewBox='0 0 64 64' width='{size}' height='{size}' role='img' aria-label='FairTrace logo'>
<defs><linearGradient id='ftg' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#6366f1'/>
<stop offset='1' stop-color='#14b8a6'/></linearGradient></defs>
<rect width='64' height='64' rx='16' fill='url(#ftg)'/>
<path d='M19 12h17l9 9v29a3 3 0 0 1-3 3H19a3 3 0 0 1-3-3V15a3 3 0 0 1 3-3z' fill='#fff'/>
<path d='M36 12v9h9' fill='#e0e7ff'/>
<line x1='21' y1='22' x2='32' y2='22' stroke='#94a3b8' stroke-width='2.4' stroke-linecap='round'/>
<line x1='21' y1='28' x2='29' y2='28' stroke='#94a3b8' stroke-width='2.4' stroke-linecap='round'/>
<polyline points='21,39 26,39 29,32 33,45 36,36 40,36' fill='none' stroke='#4f46e5' stroke-width='2.8'
 stroke-linecap='round' stroke-linejoin='round'/>
<circle cx='46' cy='46' r='10' fill='#16a34a' stroke='#fff' stroke-width='3'/>
<path d='M41.5 46.2l3.2 3.2 5.8-6.4' fill='none' stroke='#fff' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'/>
</svg>"""

HERO_CSS = """
<style>
.ft .hero{position:relative;overflow:hidden;border-radius:20px;padding:24px 26px 20px;color:#fff;
  background:linear-gradient(120deg,#1e1b4b 0%,#3730a3 45%,#0f766e 100%)}
.ft .hero svg.bg{position:absolute;inset:0;width:100%;height:100%;opacity:.55}
.ft .hero .wave{stroke-dasharray:1400;stroke-dashoffset:1400;animation:draw 3s ease-out .2s forwards}
.ft .hero .top{position:relative;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.ft .hero h1{margin:0;font-size:2rem;font-weight:800;letter-spacing:-.02em;color:#fff}
.ft .hero .tag{color:#c7d2fe;font-size:1.02rem;margin-top:2px}
.ft .hero .tag b{color:#fff}
.ft .hero .meta{margin-left:auto;font-size:.8rem;color:#c7d2fe;text-align:right}
.ft .hero .steps{position:relative;display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:16px}
.ft .hero .stp{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);border-radius:999px;
  padding:5px 11px;font-size:.82rem;color:#e0e7ff;white-space:nowrap;animation:rise .5s ease-out both}
.ft .hero .stp i{font-style:normal;display:inline-flex;width:19px;height:19px;border-radius:50%;background:#fff;color:#3730a3;align-items:center;justify-content:center;font-size:.72rem;font-weight:800;margin-right:5px}
.ft .hero .stp b{color:#fff}
.ft .hero .arr{color:#a5b4fc;font-weight:800}
@keyframes draw{to{stroke-dashoffset:0}}
</style>
"""


def logo(size: int = 58) -> str:
    return LOGO_SVG.format(size=size)


def hero_html(steps) -> str:
    dots = "".join(f"<circle cx='{x}' cy='{y}' r='1.3' fill='#c7d2fe' opacity='.35'/>"
                   for x in range(10, 1200, 28) for y in range(10, 200, 28))
    bg = ("<svg class='bg' viewBox='0 0 1200 200' preserveAspectRatio='none'>" + dots +
          "<path class='wave' d='M0,150 L180,150 L220,110 L260,175 L300,95 L340,150 L620,150 L650,128 L690,168 "
          "L720,140 L1200,140' fill='none' stroke='#5eead4' stroke-width='2.5' opacity='.8'/></svg>")
    pills = "<span class='arr'>→</span>".join(
        f"<span class='stp' style='animation-delay:{.15 + i * .12:.2f}s'><i>{i + 1}</i><b>{esc(n.split(' ', 1)[-1])}</b> {esc(t)}</span>"
        for i, (n, t, _c) in enumerate(steps))
    return CSS + HERO_CSS + (
        "<div class='ft'><div class='hero'>" + bg +
        "<div class='top'>" + logo(58) +
        "<div><h1>Recruitment FairTrace AI</h1><div class='tag'>Screen CVs fast, fairly and <b>with proof</b>.</div></div>"
        "<div class='meta'>GenAI prototype · all data synthetic<br>IS5542 GenAI in Business · CityU</div></div>"
        f"<div class='steps'>{pills}</div></div></div>")


# ================================================================== 🏁 Summary

def _diverging(rows, ref="A1") -> str:
    """Score difference from the reference CV, naive vs FairTrace. 0 = treated the same."""
    base = next(r for r in rows if r["id"] == ref)
    others = [r for r in rows if r["qualified"] and r["id"] != ref]
    diffs = [r[k]["score"] - base[k]["score"] for r in others for k in ("naive", "fair")]
    lim = max(4, int(max(abs(d) for d in diffs)) + 1)
    out = ""
    for i, r in enumerate(others):
        cells = ""
        for k, col in (("naive", NAIVE), ("fair", FAIR)):
            d = round(r[k]["score"] - base[k]["score"], 1)
            w = abs(d) / lim * 50
            left = 50 if d >= 0 else 50 - w
            cells += (f"<div style='position:relative;height:15px;margin:3px 0;background:#f8fafc;border-radius:6px'>"
                      f"<div style='position:absolute;left:50%;top:-2px;bottom:-2px;width:2px;background:#94a3b8'></div>"
                      f"<div class='fill' style='left:{left:.1f}%;width:{max(w, .6):.1f}%;background:{col};"
                      f"animation-delay:{i * .1 + (.3 if k == 'fair' else 0):.2f}s'></div></div>")
        vals = " / ".join(f"<b style='color:{c}'>{r[k]['score'] - base[k]['score']:+.1f}</b>"
                          for k, c in (("naive", NAIVE), ("fair", FAIR)))
        out += (f"<div class='lab'><b>{r['id']}</b> {esc(r['difference'])}</div><div>{cells}</div>"
                f"<div class='val' style='font-weight:400'>{vals}</div>")
    return (f"<div class='bars' style='grid-template-columns:200px 1fr 92px'>{out}</div>"
            f"<div class='axis' style='grid-template-columns:200px 1fr 92px'><div></div><div class='ticks'>"
            f"<span style='left:3%'>-{lim}</span><span style='left:50%'>0 = same as A1</span>"
            f"<span style='left:97%'>+{lim}</span></div><div></div></div>")


def _audit_bars(a) -> str:
    fixes = list(a["fixes"])
    hi = max([r["gap"] for r in a["results"].values()] + [6])
    out = ""
    for i, (k, r) in enumerate(a["results"].items()):
        series = [(r["gap"], BAD if r["bias"] else NEUTRAL)]
        for f in fixes:
            if k in a["fixes"][f]:
                series.append((a["fixes"][f][k]["gap"], GOOD if f == "fairtrace" else "#86efac"))
        cells = "".join(f"<div class='cell' style='margin:2px 0'>{track(v, 0, hi, c, i * .1 + j * .2)}"
                        f"<b style='color:{GOOD if c == '#86efac' else c}'>{v:g}</b></div>" for j, (v, c) in enumerate(series))
        out += (f"<div><b>{esc(k.replace('_', ' ').title())}</b><div style='margin-top:2px'>{level_chip(audit_level(r))}</div></div>"
                f"<div>{cells}</div>")
    legend = (f"<div class='legend'><span><i style='background:{BAD}'></i>gap before (flagged)</span>"
              f"<span><i style='background:#86efac'></i>{FIX_NAME['prompt_rule']}</span>"
              f"<span><i style='background:{GOOD}'></i>{FIX_NAME['fairtrace']}</span></div>")
    return legend + f"<div class='cmp' style='grid-template-columns:150px 1fr'>{out}</div>"


def _kpi(label, value, sub, delay=0.0) -> str:
    return (f"<div class='kpi' style='animation-delay:{delay:.2f}s'><div class='l'>{label}</div>"
            f"<div class='v'>{value}</div><div class='tiny'>{sub}</div></div>")


def _yes(t=""):
    return f"<span style='color:{GOOD};font-weight:800'>✓</span> <span class='tiny'>{esc(t)}</span>"


def _no(t=""):
    return f"<span style='color:{BAD};font-weight:800'>✗</span> <span class='tiny'>{esc(t)}</span>"


def summary_html(replay: dict, bench: list[dict]) -> str:
    rows = replay["screen"]["rows"]
    a = replay["audit"]
    flags = replay["rubric"]["lint"]["flags"]
    still = [f for f in flags if lexicon_flags(f.get("rewrite") or "")]
    ns, fs = spread(rows, "naive"), spread(rows, "fair")
    cut_n = [r["id"] for r in rows if r["qualified"] and not r["naive"]["shortlist"]]
    cut_f = [r["id"] for r in rows if r["qualified"] and not r["fair"]["shortlist"]]
    caught = sum(r["fair"].get("quotes_rejected", 0) + r["fair"].get("quotes_trimmed", 0) for r in rows)
    evid = round(sum(r["fair"]["evidence_valid"] for r in rows) / len(rows))
    flagged = [k for k, r in a["results"].items() if r["bias"]]
    after = {f: max((v["gap"] for v in res.values()), default=0) for f, res in a["fixes"].items()}
    tr = replay["screen"]["trace"]
    nt = trace.summary([x for x in tr if x["component"].startswith("naive")])
    ft = trace.summary([x for x in tr if x["component"].startswith(("blind", "fairtrace"))])
    per = len(rows)
    chosen = next((m for m in bench if m["model"] == llm.SCORER_MODEL and m["method"] == "fair"), None)

    kpis = ("<div class='row'>"
            + _kpi("Unfair score spread", f"<span class='from'>{ns:g}</span> → <span class='to'>{fs:g}</span>",
                   "points among 5 equal CVs")
            + _kpi("Qualified people wrongly cut", f"<span class='from'>{len(cut_n)}</span> → <span class='to'>{len(cut_f)}</span>",
                   f"{', '.join(cut_n) or 'none'} → {', '.join(cut_f) or 'none'}", .1)
            + _kpi("Points backed by evidence", f"<span class='from'>0%</span> → <span class='to'>{evid}%</span>",
                   f"{caught} bad quotes caught by Python", .2)
            + _kpi("Attributes flagged by the agent", f"<span style='color:{WARN}'>{len(flagged)}</span> / {len(a['results'])}",
                   f"largest gap after FairTrace: {after.get('fairtrace', '-')}", .3)
            + _kpi("Cost per CV", f"<span class='to'>${ft['cost_usd'] / per:.4f}</span>",
                   f"naive ${nt['cost_usd'] / per:.4f} · both under 0.1 US cent", .4)
            + "</div>")

    score = [("Same score for the same qualifications", _no(f"spread {ns:g}"), _yes(f"spread {fs:g}")),
             ("Explains every point with CV evidence", _no("one-line reason"), _yes(f"{evid}% verified quotes")),
             ("Hides personal details before scoring", _no(), _yes("name, age, breaks, disability, contact")),
             ("Checks the job ad for biased wording", _no(), _yes(f"{len(flags)} phrases flagged")),
             ("Tests itself for bias", _no(), _yes(f"AI agent, {len(a['steps'])} steps")),
             ("Records every AI decision", _no(), _yes("Decision Trace, JSONL")),
             ("Human approves fixes and decisions", _no(), _yes("approve / reject"))]
    cell = "padding:7px 0;border-bottom:1px solid #f1f5f9"
    table = "".join(f"<div style='{cell}'>{esc(t)}</div><div style='{cell}'>{n}</div><div style='{cell}'>{f}</div>"
                    for t, n, f in score)
    scorecard = (f"<div style='display:grid;grid-template-columns:1.4fr 1fr 1.3fr;gap:0 14px;font-size:.9rem'>"
                 f"<div class='grid-head'>Capability</div><div class='grid-head' style='color:{NAIVE}'>Naive AI</div>"
                 f"<div class='grid-head' style='color:{FAIR}'>FairTrace</div>{table}</div>")

    impact = "".join(
        f"<div class='kpi' style='animation-delay:{i * .1:.2f}s'><div style='font-size:1.6rem'>{ic}</div>"
        f"<div style='font-weight:800;margin:4px 0'>{esc(t)}</div><div class='sub'>{esc(d)}</div></div>"
        for i, (ic, t, d) in enumerate([
            ("🎯", "Fairer shortlist", "Equally qualified people get the same score, so the company stops losing good "
                                      "candidates because of a career break, age or a name."),
            ("🛡️", "Defensible decisions", "Every score has evidence and a log, ready for a complaint, an EOC enquiry or a "
                                          "PCPD review under Hong Kong's anti-discrimination ordinances."),
            ("⚡", "Still fast and cheap", "Seconds and well under 0.1 US cent per CV in this prototype, with a human "
                                          "making the final call.")]))
    model_line = (f"Chosen model: <b>{esc(llm.short(llm.SCORER_MODEL))}</b> (spread {chosen['spread']:g}, run SD "
                  f"{chosen['sd']:g}, separation {chosen['separation']:g}). With the naive prompt every model tested showed "
                  f"a 5–6 point gap: <b>the method matters more than the model</b>." if chosen else "")
    still_line = f" {len(still)} AI rewrite still contained risky wording and was flagged for HR." if still else ""
    return wrap(
        "<div class='banner b-ok' style='font-size:1.05rem'>🏁 Same CVs, a fairer result, and proof for every point. "
        "FairTrace narrows the gap the naive AI opened and still tells strong CVs from weak ones.</div>"
        + kpis
        + f"<div class='two'><div class='card'><h3>Score difference from the reference CV (A1)</h3>"
        f"<div class='legend'><span><i style='background:{NAIVE}'></i>Naive AI</span>"
        f"<span><i style='background:{FAIR}'></i>FairTrace</span></div>{_diverging(rows)}"
        f"<div class='tiny' style='margin-top:8px'>Same qualifications, so a fair screener stays on the 0 line.</div></div>"
        f"<div class='card'><h3>Bias audit: gap per attribute</h3>{_audit_bars(a)}</div></div>"
        f"<div class='card'><h3>Naive AI vs FairTrace</h3>{scorecard}</div>"
        f"<div class='row'>{impact}</div>"
        f"<div class='card'><h3>What else we learned</h3><ul class='sub' style='margin:0;padding-left:18px'>"
        f"<li>Job ad: {len(flags)} risky phrases flagged by the LLM and a word list.{esc(still_line)}</li>"
        f"<li>{model_line}</li>"
        f"<li>Hidden bias is real: for some attributes the naive AI never mentions the detail in its reasons, so only "
        f"counterfactual testing finds it.</li>"
        f"<li>LLMs make mistakes even when checking: invented quotes and a risky rewrite were caught by simple Python "
        f"rules. Layered checks plus human approval beat trusting one model.</li></ul>"
        f"<div class='tiny' style='margin-top:10px'>Illustrative prototype on synthetic data: one job, six applicants, "
        f"3–5 runs per CV. Not a scientific or legal audit.</div></div>")
