"""HTML rendering for the Gradio app: cards, charts and CSS animations (no JavaScript needed).

Colour code used everywhere:
  amber  = naive AI (the tool companies use today)     indigo = FairTrace
  red    = bias / risk                                   green  = fixed / fair
"""

from __future__ import annotations

import html
import json
import re

from . import llm, trace
from .rubric import lexicon_flags

NAIVE, FAIR, BAD, GOOD, WARN, NEUTRAL = "#d97706", "#4f46e5", "#dc2626", "#16a34a", "#d97706", "#64748b"

CSS = """
<style>
.ft{font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:#0f172a;line-height:1.45;font-size:15px}
.ft *{box-sizing:border-box}
.ft .card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px 20px;margin:10px 0;
  box-shadow:0 1px 2px rgba(15,23,42,.04)}
.ft h3{margin:0 0 10px;font-size:1.05rem;font-weight:700;color:#0f172a}
.ft .sub{color:#475569;font-size:.88rem}
.ft .tiny{color:#475569;font-size:.8rem}
.ft .row{display:flex;gap:12px;flex-wrap:wrap}
.ft .two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:900px){.ft .two{grid-template-columns:1fr}}
.ft .kpi{flex:1;min-width:170px;border-radius:14px;padding:14px 16px;background:#fff;border:1px solid #e2e8f0;
  animation:rise .6s ease-out both}
.ft .kpi .v{font-size:1.9rem;font-weight:800;letter-spacing:-.02em;line-height:1.1}
.ft .kpi .l{font-size:.82rem;color:#475569;margin-bottom:4px}
.ft .from{color:#d97706}.ft .to{color:#4f46e5}
.ft .chip{display:inline-block;border-radius:999px;padding:2px 10px;font-size:.78rem;font-weight:700;white-space:nowrap}
.ft .c-bad{background:#fee2e2;color:#991b1b}.ft .c-ok{background:#dcfce7;color:#166534}
.ft .c-warn{background:#fef3c7;color:#92400e}.ft .c-n{background:#e2e8f0;color:#1e293b}
.ft .c-naive{background:#fef3c7;color:#92400e}.ft .c-fair{background:#e0e7ff;color:#3730a3}
.ft .bars{display:grid;grid-template-columns:var(--lab,210px) 1fr 52px;gap:7px 10px;align-items:center}
.ft .bars .lab{font-size:.88rem;color:#1e293b;overflow:hidden;text-overflow:ellipsis}
.ft .bars .val{font-weight:800;font-size:.9rem;text-align:right}
.ft .track{position:relative;height:16px;background:#f1f5f9;border-radius:8px;overflow:hidden}
.ft .fill{position:absolute;left:0;top:0;bottom:0;border-radius:8px;transform-origin:left;animation:grow .9s cubic-bezier(.2,.8,.2,1) both}
.ft .axis{display:grid;grid-template-columns:var(--lab,210px) 1fr 52px;gap:0 10px;margin-top:2px}
.ft .ticks{position:relative;height:16px;font-size:.72rem;color:#64748b}
.ft .ticks span{position:absolute;transform:translateX(-50%)}
.ft .grid-head{font-size:.75rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.04em}
.ft .cmp{display:grid;grid-template-columns:200px repeat(var(--n,3),1fr);gap:6px 14px;align-items:center}
.ft .cell{display:flex;align-items:center;gap:8px}
.ft .cell .track{flex:1}
.ft .cell b{min-width:34px;text-align:right;font-size:.88rem}
.ft .tl{position:relative;margin-left:14px;border-left:2px solid #e2e8f0;padding-left:20px}
.ft .st{position:relative;margin:0 0 12px;animation:rise .45s ease-out both}
.ft .st .dot{position:absolute;left:-32px;top:1px;width:22px;height:22px;border-radius:50%;display:flex;
  align-items:center;justify-content:center;font-size:.72rem;font-weight:800;color:#fff}
.ft .st .t{font-weight:700}
.ft .st .why{color:#64748b;font-size:.8rem}
.ft .st .obs{margin-top:2px;font-size:.9rem;color:#1e293b}
.ft .thinking{color:#4f46e5;font-weight:700;animation:pulse 1s ease-in-out infinite}
.ft .ad{white-space:pre-wrap;font-size:.92rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px}
.ft mark.risk{background:#fee2e2;color:#991b1b;border-radius:4px;padding:0 3px;font-weight:700}
.ft mark.gone{background:#fee2e2;color:#991b1b;text-decoration:line-through;border-radius:4px;padding:0 2px}
.ft mark.tok{background:#dcfce7;color:#166534;border-radius:4px;padding:0 2px;font-weight:600}
.ft mark.kw{background:#fde68a;color:#78350f;border-radius:3px;padding:0 2px}
.ft .swap{display:grid;grid-template-columns:1fr 24px 1fr;gap:8px;align-items:center;padding:8px 0;border-bottom:1px solid #f1f5f9}
.ft .swap .old{color:#991b1b;text-decoration:line-through;font-weight:600}
.ft .swap .new{color:#166534;font-weight:600}
.ft .cv{white-space:pre-wrap;font-family:ui-monospace,Consolas,monospace;font-size:.8rem;background:#f8fafc;
  border:1px solid #e2e8f0;border-radius:10px;padding:10px 12px;line-height:1.5}
.ft details{margin-top:8px}.ft summary{cursor:pointer;color:#4338ca;font-weight:700;font-size:.85rem}
.ft pre.raw{white-space:pre-wrap;font-size:.75rem;background:#0f172a;color:#e2e8f0;border-radius:8px;padding:10px;max-height:260px;overflow:auto}
.ft .call{display:grid;grid-template-columns:64px 150px 110px 1fr 76px;gap:10px;padding:10px 0;border-bottom:1px solid #f1f5f9;align-items:start}
.ft .banner{border-radius:14px;padding:14px 18px;font-weight:700}
.ft .b-warn{background:#fffbeb;border:1px solid #fcd34d;color:#78350f}.ft .b-ok{background:#f0fdf4;border:1px solid #86efac;color:#14532d}
.ft .b-bad{background:#fef2f2;border:1px solid #fca5a5;color:#7f1d1d}
.ft .legend{display:flex;gap:14px;flex-wrap:wrap;font-size:.8rem;color:#334155;margin:4px 0 8px}
.ft .legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.ft svg text{font-family:Inter,ui-sans-serif,system-ui,sans-serif}
.ft .pop{animation:pop .6s cubic-bezier(.2,.9,.3,1.3) both}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:scale(1)}}
@keyframes pulse{50%{opacity:.35}}
</style>
"""


def wrap(body: str) -> str:
    return CSS + f'<div class="ft">{body}</div>'


def esc(s) -> str:
    return html.escape(str(s))


def chip(text, kind="n") -> str:
    return f'<span class="chip c-{kind}">{esc(text)}</span>'


def how(text: str, title: str = "How it works") -> str:
    return f"<details><summary>{esc(title)}</summary><div class='sub' style='margin-top:6px'>{text}</div></details>"


def pct(v, lo, hi) -> float:
    return max(0.0, min(100.0, (float(v) - lo) / (hi - lo) * 100))


def track(v, lo, hi, color, delay=0.0) -> str:
    return (f"<div class='track'><div class='fill' style='width:{pct(v, lo, hi):.1f}%;background:{color};"
            f"animation-delay:{delay:.2f}s'></div></div>")


def axis(lo, hi, step, lab="210px") -> str:
    ticks = "".join(f"<span style='left:{pct(t, lo, hi):.1f}%'>{t:g}</span>" for t in range(int(lo), int(hi) + 1, step))
    return f"<div class='axis' style='--lab:{lab}'><div></div><div class='ticks'>{ticks}</div><div></div></div>"


def bars(items, lo=0, hi=100, step=20, lab="210px") -> str:
    """items: (label, value, colour). All rows share one scale, so the bars line up."""
    rows = "".join(f"<div class='lab' title='{esc(l)}'>{esc(l)}</div>{track(v, lo, hi, c, i * .06)}"
                   f"<div class='val' style='color:{c}'>{v:g}</div>" for i, (l, v, c) in enumerate(items))
    return f"<div class='bars' style='--lab:{lab}'>{rows}</div>{axis(lo, hi, step, lab)}"


def level_chip(level: str) -> str:
    if level.startswith("BIAS"):
        return chip(level, "bad")
    if level.startswith("POSSIBLE"):
        return chip("⚠ " + level, "warn")
    return chip(level, "ok")


# ================================================================== ① Fair Rubric

def _highlight(ad: str, phrases) -> str:
    out = esc(ad)
    for p in sorted({p for p in phrases if p}, key=len, reverse=True):
        words = [re.escape(esc(w)) for w in p.split()]
        out = re.sub(r"\s+".join(words), lambda m: f"<mark class='risk'>{m.group(0)}</mark>", out, flags=re.I)
    return out


GROUND_ICON = {"age": "🎂", "race": "🌏", "national": "🌏", "family": "👶", "sex": "⚧", "disab": "♿", "marital": "💍"}


def _icon(ground: str) -> str:
    g = (ground or "").lower()
    return next((v for k, v in GROUND_ICON.items() if k in g), "⚠")


def _new(rewrite: str) -> str:
    """The AI's suggested wording, checked again by the fixed word list (the AI can miss its own bias)."""
    still = lexicon_flags(rewrite)
    if not still:
        return f"<div class='new'>{esc(rewrite)}</div>"
    return (f"<div><span style='color:#b45309;font-weight:600'>{_highlight(rewrite, [x['phrase'] for x in still])}</span>"
            f"<div style='margin-top:3px'>{chip('⚠ still risky: HR must edit', 'warn')}</div></div>")


def rubric_lint_html(r: dict) -> str:
    flags = r["lint"]["flags"]
    by_ground = {}
    for f in flags:
        key = _icon(f.get("ground", ""))
        by_ground[key] = by_ground.get(key, 0) + 1
    summary = " ".join(f"<span class='chip c-bad' style='font-size:.9rem'>{k} {n}</span>" for k, n in by_ground.items())
    swaps = "".join(
        f"<div class='swap' style='animation:rise .4s ease-out {i * .08:.2f}s both'>"
        f"<div><span class='old'>{esc(f.get('phrase'))}</span><div class='tiny'>{_icon(f.get('ground', ''))} "
        f"{esc(f.get('ground'))}{' · ' + esc(f.get('law')) if f.get('law') else ''}</div></div>"
        f"<div style='text-align:center;color:#94a3b8;font-weight:800'>→</div>"
        f"{_new(f.get('rewrite') or 'remove')}</div>" for i, f in enumerate(flags))
    why = "<ul>" + "".join(f"<li><b>{esc(f.get('phrase'))}</b>: {esc(f.get('why'))}</li>" for f in flags) + "</ul>"
    return wrap(
        "<div class='row'>"
        f"<div class='kpi'><div class='l'>Risky phrases found</div><div class='v' style='color:{BAD}'>{len(flags)}</div>"
        f"<div style='margin-top:6px'>{summary}</div></div>"
        f"<div class='kpi'><div class='l'>Checked by</div><div style='margin-top:8px'>"
        f"{chip('LLM reviewer', 'fair')} + {chip('fixed word list', 'n')}</div>"
        f"<div class='tiny' style='margin-top:6px'>{r['lint']['word_list_hits']} word-list hits as a safety net</div></div></div>"
        f"<div class='two'><div class='card'><h3>The job ad HR wrote</h3>"
        f"<div class='ad'>{_highlight(r['risky_ad'], [f.get('phrase') for f in flags])}</div></div>"
        f"<div class='card'><h3>AI suggestions</h3>{swaps}{how(why, 'Why each phrase is risky')}</div></div>")


RUBRIC_COLORS = ["#4f46e5", "#0ea5e9", "#14b8a6", "#f59e0b", "#ec4899", "#8b5cf6"]


def rubric_approved_html(r: dict) -> str:
    crit = r["criteria"]
    seg = "".join(f"<div title='{esc(c['name'])}' style='width:{c['weight']}%;background:{RUBRIC_COLORS[i % 6]};"
                  f"display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:.85rem;"
                  f"animation:grow .8s ease-out {i * .12:.2f}s both;transform-origin:left'>{c['weight']}%</div>"
                  for i, c in enumerate(crit))
    legend = "".join(f"<div style='display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #f1f5f9'>"
                     f"<i style='flex:0 0 12px;height:12px;margin-top:4px;border-radius:3px;background:{RUBRIC_COLORS[i % 6]}'></i>"
                     f"<div><b>{esc(c['name'])}</b> <span class='tiny'>· {c['weight']}%</span>"
                     f"<div class='tiny'>{esc(c.get('evidence_needed', ''))}</div></div></div>" for i, c in enumerate(crit))
    still = lexicon_flags(r["approved_ad"])
    ad = "<div class='ad'>" + _highlight(r["approved_ad"], [x["phrase"] for x in still]) + "</div>"
    second = (f"<div class='banner b-warn' style='margin-top:10px'>⚠ Second check: the word list still finds "
              f"“{esc(', '.join(x['phrase'] for x in still))}” in the AI's rewrite. HR must remove it before the ad is "
              f"published. The rubric below does not use it.</div>") if still else ""
    return wrap(
        "<div class='banner b-ok'>✅ HR accepted the fairer ad. The AI built a job-related scoring rubric from it.</div>"
        + second
        + f"<div class='card'><h3>Scoring rubric: what earns points</h3>"
        f"<div style='display:flex;height:34px;border-radius:10px;overflow:hidden;margin-bottom:10px'>{seg}</div>{legend}"
        f"<div class='tiny' style='margin-top:8px'>Never scored: age, gender, family status, nationality, disability, "
        f"name, career gaps, school prestige, “culture fit”.</div>{how(ad, 'Show the approved job ad')}</div>")


# ================================================================== ② Blind & Score

def spread(rows, key):
    q = [r[key]["score"] for r in rows if r["qualified"]]
    return round(max(q) - min(q), 1)


def _dotplot(rows) -> str:
    """Two lanes (naive / FairTrace) on one zoomed axis: the five equally qualified CVs."""
    q = [r for r in rows if r["qualified"]]
    vals = [r[k]["score"] for r in q for k in ("naive", "fair")]
    lo, hi = int(min(vals) // 2 * 2 - 2), int(-(-max(vals) // 2) * 2 + 2)
    W, L, R = 760, 110, 30

    def x(v):
        return L + (v - lo) / (hi - lo) * (W - L - R)

    out = [f"<svg viewBox='0 0 {W} 215' width='100%' role='img' aria-label='score spread chart'>"]
    for t in range(lo, hi + 1, 2):
        out.append(f"<line x1='{x(t):.1f}' x2='{x(t):.1f}' y1='22' y2='180' stroke='#e2e8f0'/>"
                   f"<text x='{x(t):.1f}' y='200' font-size='12' fill='#64748b' text-anchor='middle'>{t}</text>")
    for lane, (key, name, col, y) in enumerate((("naive", "Naive AI", NAIVE, 66), ("fair", "FairTrace", FAIR, 142))):
        s = sorted(q, key=lambda r: r[key]["score"])
        a, b = x(s[0][key]["score"]), x(s[-1][key]["score"])
        out.append(f"<text x='8' y='{y + 5}' font-size='14' font-weight='700' fill='{col}'>{name}</text>"
                   f"<rect x='{a - 14:.1f}' y='{y - 22}' width='{b - a + 28:.1f}' height='44' rx='22' fill='{col}' opacity='.12'/>"
                   f"<text x='{(a + b) / 2:.1f}' y='{y - 28}' font-size='12' font-weight='700' fill='{col}' text-anchor='middle'>"
                   f"spread {spread(rows, key):g} points</text>")
        seen: dict = {}
        for i, r in enumerate(s):
            v = r[key]["score"]
            off = seen.get(round(v, 1), 0)
            seen[round(v, 1)] = off + 1
            cy = y if off == 0 else y + (15 if off % 2 else -15) * ((off + 1) // 2)
            out.append(f"<g class='pop' style='animation-delay:{.2 + lane * .6 + i * .1:.2f}s;transform-box:fill-box;transform-origin:center'>"
                       f"<circle cx='{x(v):.1f}' cy='{cy}' r='12' fill='{col}' stroke='#fff' stroke-width='2'/>"
                       f"<text x='{x(v):.1f}' y='{cy + 4}' font-size='10' font-weight='800' fill='#fff' text-anchor='middle'>{r['id']}</text></g>")
    out.append("</svg>")
    return "".join(out)


def _cut(x) -> str:
    return chip("shortlisted", "ok") if x["shortlist"] else chip("cut", "bad")


def screen_table_html(s: dict) -> str:
    rows = s["rows"]
    ns, fs = spread(rows, "naive"), spread(rows, "fair")
    allrec = s["trace"]
    nt = trace.summary([x for x in allrec if x["component"].startswith("naive")])
    ft = trace.summary([x for x in allrec if x["component"].startswith(("blind", "fairtrace"))])
    per = len(rows)
    caught = sum(r["fair"].get("quotes_rejected", 0) + r["fair"].get("quotes_trimmed", 0) for r in rows)
    out_naive = [r["id"] for r in rows if r["qualified"] and not r["naive"]["shortlist"]]
    out_fair = [r["id"] for r in rows if r["qualified"] and not r["fair"]["shortlist"]]
    kpis = (
        "<div class='row'>"
        f"<div class='kpi'><div class='l'>Score spread, 5 equally qualified CVs</div>"
        f"<div class='v'><span class='from'>{ns:g}</span> → <span class='to'>{fs:g}</span></div><div class='tiny'>points, naive → FairTrace</div></div>"
        f"<div class='kpi' style='animation-delay:.1s'><div class='l'>Qualified people wrongly cut</div>"
        f"<div class='v'><span class='from'>{len(out_naive)}</span> → <span class='to'>{len(out_fair)}</span></div>"
        f"<div class='tiny'>{', '.join(out_naive) or 'none'} → {', '.join(out_fair) or 'none'}</div></div>"
        f"<div class='kpi' style='animation-delay:.2s'><div class='l'>Points backed by a verified quote</div>"
        f"<div class='v to'>{round(sum(r['fair']['evidence_valid'] for r in rows) / per)}%</div>"
        f"<div class='tiny'>{caught} made-up or garbled quotes caught by Python</div></div>"
        f"<div class='kpi' style='animation-delay:.3s'><div class='l'>Cost per CV (3 runs)</div>"
        f"<div class='v'><span class='from'>${nt['cost_usd'] / per:.4f}</span> → <span class='to'>${ft['cost_usd'] / per:.4f}</span></div>"
        f"<div class='tiny'>US$, estimated from tokens</div></div></div>")
    legend = (f"<div class='legend'><span><i style='background:{NAIVE}'></i>Naive AI ({esc(llm.short(llm.NAIVE_MODEL))}, one prompt)</span>"
              f"<span><i style='background:{FAIR}'></i>FairTrace ({esc(llm.short(llm.SCORER_MODEL))}, blind + rubric + evidence)</span></div>")
    grid = ""
    for i, r in enumerate(rows):
        n, f = r["naive"], r["fair"]
        grid += (f"<div><b>{r['id']}</b> {esc(r['name'])}<div class='tiny'>{esc(r['difference'])}</div></div>"
                 f"<div><div class='cell'>{track(n['score'], 0, 100, NAIVE, i * .08)}<b style='color:{NAIVE}'>{n['score']:g}</b> {_cut(n)}</div>"
                 f"<div class='cell' style='margin-top:4px'>{track(f['score'], 0, 100, FAIR, i * .08 + .3)}"
                 f"<b style='color:{FAIR}'>{f['score']:g}</b> {_cut(f)}</div></div>")
    note = how("A6 really has less experience, so both screeners should score it lower. Shortlist rule (same for both): "
               "the top 3, plus anyone within 3 points of the 3rd score, because smaller gaps are within the AI's own "
               "run-to-run noise. Each score is the mean of 3 runs.")
    return wrap(
        kpis
        + f"<div class='card'><h3>Same 5 qualified CVs: where each screener puts them</h3>{legend}{_dotplot(rows)}"
        + "<div class='tiny'>Zoomed axis. A1–A5 have identical skills and experience; only one personal detail differs.</div></div>"
        + f"<div class='card'><h3>All 6 applicants</h3>{legend}"
        + f"<div class='cmp' style='grid-template-columns:230px 1fr'>{grid}</div>{note}</div>")


def _criteria_bars(criteria) -> str:
    return "".join(
        f"<div class='lab'><b>{esc(c['criterion'])}</b><div class='tiny'>“{esc(c['evidence'])}”</div></div>"
        f"<div>{track(c['raw'], 0, 5, FAIR if c['verified'] else BAD, i * .08)}</div>"
        f"<div class='val' style='color:{FAIR if c['verified'] else BAD}'>{c['raw']:g}/5</div>"
        for i, c in enumerate(criteria))


def candidate_html(r: dict) -> str:
    removed = r["blind"]["removed"]
    orig = esc(r["cv"])
    for it in sorted(removed, key=lambda x: -len(x["text"])):
        orig = orig.replace(esc(it["text"]), f"<mark class='gone'>{esc(it['text'])}</mark>")
    blind = re.sub(r"(\[[^\]\n]{3,60}\]|Candidate A\d)", r"<mark class='tok'>\1</mark>", esc(r["blind"]["blind_cv"]))
    rej = [q for run in r["fair"]["runs"] for q in run.get("rejected_quotes", [])]
    rej_html = ("<div class='banner b-bad' style='margin-top:10px;font-weight:600'>🛑 Caught: the AI quoted text that is "
                f"not in the CV, so that answer was rejected and asked again: “{esc(rej[0])}”</div>") if rej else ""
    reasons = "".join(f"<li>{esc(x)}</li>" for x in r["naive"]["reasons"][:2])
    types = " ".join(chip(t, "n") for t in sorted({x["type"] for x in removed}))
    note = how("Python checks that every quote really appears in the CV. A quote that is not found earns 0 points, "
               "and an answer with an invented quote is rejected and asked again (up to 3 times).")
    return wrap(
        f"<div class='row'><div class='kpi'><div class='l'>Naive AI</div><div class='v from'>{r['naive']['score']:g}</div>"
        f"<div class='tiny'>no evidence · runs {r['naive']['scores']}</div></div>"
        f"<div class='kpi' style='animation-delay:.1s'><div class='l'>FairTrace</div><div class='v to'>{r['fair']['score']:g}</div>"
        f"<div class='tiny'>every point quoted · runs {r['fair']['scores']}</div></div>"
        f"<div class='kpi' style='animation-delay:.2s'><div class='l'>Details removed before scoring</div>"
        f"<div class='v' style='color:{BAD}'>{len(removed)}</div><div class='tiny'>{types}</div></div></div>"
        f"<div class='two'><div class='card'><h3>Original CV</h3><div class='cv'>{orig}</div></div>"
        f"<div class='card'><h3>What FairTrace sees</h3><div class='cv'>{blind}</div></div></div>"
        f"<div class='card'><h3>FairTrace score: every point needs a quote</h3>"
        f"<div class='bars' style='--lab:360px'>{_criteria_bars(r['fair']['runs'][0]['criteria'])}</div>{rej_html}{note}</div>"
        f"<div class='card'><h3 style='color:{NAIVE}'>Naive AI: its reasons</h3><ul class='sub'>{reasons}</ul></div>")


def live_cv_html(b: dict, f: dict) -> str:
    rem = " ".join(chip(f"{it['type']}: {it['text'][:30]}", "bad") for it in b["removed"]) or "nothing"
    cv = "<div class='cv'>" + esc(b["blind_cv"]) + "</div>"
    return wrap(f"<div class='row'><div class='kpi'><div class='l'>FairTrace score</div><div class='v to'>{f['score']:g}</div>"
                f"<div class='tiny'>runs {f['scores']}</div></div></div>"
                f"<div class='card'><h3>Removed before scoring</h3>{rem}</div>"
                f"<div class='card'><h3>Evidence</h3><div class='bars' style='--lab:360px'>{_criteria_bars(f['runs'][0]['criteria'])}</div></div>"
                f"<div class='card'>{how(cv, 'Show the blind CV')}</div>")


# ================================================================== ③ Auditor

TOOL = {"test_attribute": ("🧪", "Test"), "inspect_reasons": ("🔍", "Inspect reasons"),
        "apply_fix": ("🛠", "Try fix"), "finish": ("🏁", "Finish")}


def _step(st: dict, i: int) -> str:
    icon, name = TOOL.get(st["tool"], ("•", st["tool"]))
    arg = " · ".join(str(v) for v in (st.get("args") or {}).values())
    obs = st["observation"]
    m = re.search(r"-> (POSSIBLE BIAS|BIAS|no bias)", obs)
    lvl = m.group(1) if m else ""
    tag = level_chip(lvl) if lvl else ""
    if lvl == "BIAS":
        col = BAD
    elif lvl.startswith("POSSIBLE"):
        col = WARN
    elif st["tool"] in ("apply_fix", "finish"):
        col = GOOD
    else:
        col = FAIR
    src = "AI planner" if st.get("source", "").startswith("AI") else "rule"
    return (f"<div class='st' style='animation-delay:{i * .04:.2f}s'><div class='dot' style='background:{col}'>{st['n']}</div>"
            f"<div class='t'>{icon} {name}{(': ' + esc(arg)) if arg else ''} {tag}</div>"
            f"<div class='obs'>{esc(obs)}</div><div class='why'>{esc(st.get('why', ''))} · <i>{src}</i></div></div>")


def timeline_html(steps: list[dict], running: bool = False) -> str:
    body = "".join(_step(s, i) for i, s in enumerate(steps))
    if running:
        body += ("<div class='st'><div class='dot' style='background:#a5b4fc'>…</div>"
                 "<div class='thinking'>Agent is planning the next step…</div></div>")
    if not body:
        body = "<div class='sub'>Press ▶ Replay to watch the agent work.</div>"
    note = how("Loop: plan → act → observe. The AI planner chooses the next tool; if its answer is invalid, a fixed rule "
               "chooses instead (shown as <i>rule</i>). Tools: counterfactual test, inspect reasons, try a fix, finish. "
               "Verdicts are computed by statistics, never by the AI.")
    return wrap(f"<div class='card'><h3>Agent timeline</h3><div class='tl'>{body}</div>{note}</div>")


def audit_level(r: dict) -> str:
    return r.get("level", "BIAS" if r["bias"] else "no bias")


auditor_level = audit_level  # old name, kept for compatibility


def _kw_highlight(text: str, attribute: str) -> str:
    from .auditor import MENTION
    return re.sub(MENTION.get(attribute, "$^"), lambda m: f"<mark class='kw'>{m.group(0)}</mark>", esc(text), flags=re.I)


FIX_NAME = {"prompt_rule": "+ fairness rule in prompt", "fairtrace": "FairTrace pipeline"}


def audit_results_html(a: dict, approval: str | None = None) -> str:
    fixes = list(a["fixes"])
    cols = ["Before (naive AI)"] + [FIX_NAME.get(f, f) for f in fixes]
    allv = [x["score"] for r in a["results"].values() for x in r["rows"]] + \
           [x["score"] for res in a["fixes"].values() for r in res.values() for x in r["rows"]]
    lo = max(0, int(min(allv) // 5 * 5 - 5))
    hi = 100
    head = "<div></div>" + "".join(f"<div class='grid-head'>{esc(c)}</div>" for c in cols)
    blocks = ""
    for k, r in a["results"].items():
        gaps = [f"gap {r['gap']:g}"] + [f"gap {a['fixes'][f][k]['gap']:g}" if k in a["fixes"][f] else "not re-tested"
                                        for f in fixes]
        sub = "<div></div>" + "".join(f"<div class='tiny'><b>{g}</b></div>" for g in gaps)
        lines = ""
        for i, x in enumerate(r["rows"]):
            is_low = x["label"] == r["lowest"] and r["bias"]
            cells = f"<div class='cell'>{track(x['score'], lo, hi, BAD if is_low else NEUTRAL, i * .06)}<b>{x['score']:g}</b></div>"
            for f in fixes:
                fx = a["fixes"][f].get(k)
                y = next((z for z in fx["rows"] if z["label"] == x["label"]), None) if fx else None
                cells += (f"<div class='cell'>{track(y['score'], lo, hi, GOOD, .3 + i * .06)}<b>{y['score']:g}</b></div>"
                          if y else "<div class='tiny'>-</div>")
            lines += f"<div class='lab' title='{esc(x['desc'])}' style='font-size:.86rem'>{esc(x['desc'].split(' (')[0])}</div>{cells}"
        f = r.get("forensics")
        quote = ""
        if f and f.get("quotes"):
            quote = (f"<div class='sub' style='margin-top:10px;border-left:3px solid {BAD};padding-left:10px'>"
                     f"<b>{f['mentions']} of {f['of']}</b> AI reasons mention it: “{_kw_highlight(f['quotes'][0], k)}”</div>")
        elif f:
            quote = (f"<div class='tiny' style='margin-top:8px'>0 of {f['of']} AI reasons mention it: a hidden bias, "
                     f"the AI does not say why.</div>")
        blocks += (f"<div class='card' style='animation:rise .5s ease-out both'><h3>{esc(k.replace('_', ' ').title())} "
                   f"{level_chip(audit_level(r))}</h3><div class='cmp' style='--n:{len(cols)}'>{head}{sub}{lines}</div>{quote}</div>")
    s = trace.summary(a["trace"])
    if approval and approval.startswith("Approved"):
        ban = f"<div class='banner b-ok'>✅ Fix approved by a human ({esc(approval)}). Recorded in the Decision Trace.</div>"
    elif approval:
        ban = f"<div class='banner b-bad'>❌ {esc(approval)}. Recorded in the Decision Trace.</div>"
    else:
        ban = f"<div class='banner b-warn'>⏸ {esc(a['summary'])}</div>"
    note = how("<b>BIAS</b> = gap ≥ 3 points and more than twice the screener's own run-to-run noise. "
               "<b>POSSIBLE BIAS</b> = gap ≥ 3 points but within twice the noise: still inspected and re-tested; "
               "more runs needed. Each copy is scored 5 times.", "How the verdict is decided")
    return wrap(
        ban + f"<div class='legend' style='margin-top:10px'><span><i style='background:{NEUTRAL}'></i>score before</span>"
        f"<span><i style='background:{BAD}'></i>lowest copy (flagged)</span><span><i style='background:{GOOD}'></i>after a fix</span>"
        f"<span class='tiny'>axis {lo}–100 · {s['calls']} model calls · about US${s['cost_usd']}</span></div>"
        + blocks + f"<div class='card'>{note}</div>")


# ================================================================== 📊 Model choice

def benchmark_html(results: list[dict]) -> str:
    models = []
    for m in results:
        if m["model"] not in models:
            models.append(m["model"])

    def get(mod, meth):
        return next((x for x in results if x["model"] == mod and x["method"] == meth), None)

    hi = max(6, max(x["spread"] for x in results) + 1)
    rows = ""
    for i, mod in enumerate(models):
        n, f = get(mod, "naive"), get(mod, "fair")
        chosen = chip("chosen", "ok") if mod == llm.SCORER_MODEL else ""
        rows += (f"<div><b>{esc(llm.short(mod))}</b> {chosen}</div>"
                 f"<div><div class='cell'>{track(n['spread'], 0, hi, NAIVE, i * .1)}<b style='color:{NAIVE}'>{n['spread']:g}</b></div>"
                 f"<div class='cell' style='margin-top:4px'>{track(max(f['spread'], .15), 0, hi, FAIR, i * .1 + .3)}"
                 f"<b style='color:{FAIR}'>{f['spread']:g}</b></div></div>")
    trs = "".join(
        f"<tr><td><b>{esc(llm.short(m['model']))}</b></td><td>{'FairTrace' if m['method'] == 'fair' else 'naive'}</td>"
        f"<td>{m['spread']}</td><td>{m['sd']}</td><td>{m['separation']}</td>"
        f"<td>{str(m['evidence']) + '%' if 'evidence' in m else '-'}</td>"
        f"<td>${m['cost_per_cv']:.4f}</td><td>{m['sec_per_cv']}s</td></tr>" for m in results)
    table = ("<table style='width:100%;font-size:.85rem;border-collapse:collapse'><tr><th align=left>Model</th>"
             "<th align=left>Method</th><th align=left>Spread ↓</th><th align=left>Run SD ↓</th><th align=left>Separation ↑</th>"
             "<th align=left>Evidence ✓</th><th align=left>Cost/CV</th><th align=left>Time/CV</th></tr>" + trs + "</table>"
             "<p>Separation = mean score of the qualified CVs minus the weak CV: a fair screener must still tell strong "
             "from weak. Cost is estimated from tokens and Hugging Face router prices (Nov 2026).</p>")
    return wrap(
        f"<div class='card'><h3>Unfair spread among 5 equally qualified CVs (lower is better)</h3>"
        f"<div class='legend'><span><i style='background:{NAIVE}'></i>naive prompt</span>"
        f"<span><i style='background:{FAIR}'></i>FairTrace method</span></div>"
        f"<div class='cmp' style='grid-template-columns:230px 1fr'>{rows}</div>"
        f"<div class='tiny' style='margin-top:10px'>Every model shows a gap with the naive prompt: the method matters more "
        f"than the model.</div>{how(table, 'Show all numbers')}</div>")


# ================================================================== ④ Decision Trace

COMP = {"rubric.lint": ("Job-ad review", "#0284c7"), "rubric.build": ("Rubric builder", "#0284c7"),
        "naive.score": ("Naive AI score", NAIVE), "blind.detect": ("Blind Parser", "#db2777"),
        "fairtrace.score": ("Evidence Scorer", FAIR), "explain.letter": ("Letter writer", "#0d9488"),
        "agent.plan": ("Agent planner", "#7c3aed"), "agent.step": ("Agent step", "#7c3aed"),
        "human.approval": ("Human decision", GOOD)}


def _readable(r: dict) -> str:
    raw = r.get("raw_output") or r.get("observation") or ""
    comp = r.get("component", "")
    data = llm.parse_json(raw) if comp in ("blind.detect", "fairtrace.score") else None
    if comp == "blind.detect" and isinstance(data, dict):
        items = [x for x in (data.get("sensitive") or []) if isinstance(x, dict)]
        return "<span class='tiny'>AI flagged (Python keeps only personal details):</span> " + (" ".join(chip(f"{str(x.get('type', '?')).split('|')[0]}: {str(x.get('text', ''))[:28]}", "bad")
                                    for x in items) or "nothing")
    if comp == "fairtrace.score" and isinstance(data, dict):
        return "".join(f"<div class='tiny'><b>{esc(c.get('name', ''))}</b> {c.get('score', '?')}/5 · “{esc(c.get('evidence', ''))}”</div>"
                       for c in data.get("criteria", []) if isinstance(c, dict))
    if comp == "naive.score":
        m = re.search(r"SCORE:\s*(\d+)", raw)
        rs = re.search(r"REASON:\s*(.+)", raw, re.S)
        return (f"<b style='color:{NAIVE}'>{m.group(1) if m else '?'}</b> · "
                f"<span class='sub'>{esc((rs.group(1) if rs else raw)[:220])}</span>")
    return f"<span class='sub'>{esc(raw[:260])}{'…' if len(raw) > 260 else ''}</span>"


def trace_html(recs: list[dict], letter: str = "") -> str:
    s = trace.summary(recs)
    maxlat = max([r.get("latency_s", 0) or 0 for r in recs] + [1])
    calls = ""
    for i, r in enumerate(recs):
        name, col = COMP.get(r["component"], (r["component"], NEUTRAL))
        lat = r.get("latency_s", 0) or 0
        raw = r.get("raw_output", r.get("observation", ""))
        try:
            raw = json.dumps(json.loads(raw), indent=1, ensure_ascii=False)
        except Exception:
            pass
        calls += (f"<div class='call' style='animation:rise .35s ease-out {min(i, 15) * .03:.2f}s both'>"
                  f"<div class='tiny'>{esc(r['time'][11:])}</div>"
                  f"<div><span class='chip' style='background:{col}1f;color:{col}'>{esc(name)}</span>"
                  f"<div class='tiny' style='margin-top:4px'>{esc(llm.short(r.get('model', '-')))} · t={r.get('temperature', '-')}</div></div>"
                  f"<div><div class='track' style='height:8px'><div class='fill' style='width:{lat / maxlat * 100:.0f}%;background:{col}'></div></div>"
                  f"<div class='tiny'>{lat}s · {r.get('tokens_in', 0) + r.get('tokens_out', 0)} tokens</div></div>"
                  f"<div>{_readable(r)}<details><summary>Show raw</summary><pre class='raw'>{esc(raw)}</pre>"
                  f"<div class='tiny'>prompt {esc(r.get('prompt_version', ''))} · input #{esc(r.get('input_hash', ''))} · "
                  f"record {esc(r['id'])}</div></details></div>"
                  f"<div class='tiny' style='text-align:right'>${r.get('cost_usd', 0):.5f}</div></div>")
    by: dict = {}
    for r in recs:
        by[r["component"]] = by.get(r["component"], 0) + 1
    mx = max(by.values()) if by else 1
    dist = bars([(COMP.get(k, (k, NEUTRAL))[0], v, COMP.get(k, (k, NEUTRAL))[1]) for k, v in by.items()],
                0, mx, max(1, mx // 4), "150px")
    let = (f"<div class='card' style='border-left:4px solid {GOOD}'><h3>✉️ Explanation for the applicant</h3>"
           f"<div style='font-size:.95rem'>{esc(letter)}</div>"
           f"<div class='tiny' style='margin-top:6px'>AI draft, sent only after a recruiter reviews it.</div></div>") if letter else ""
    return wrap(
        f"<div class='row'><div class='kpi'><div class='l'>Model calls recorded</div><div class='v to'>{s['calls']}</div></div>"
        f"<div class='kpi' style='animation-delay:.1s'><div class='l'>Tokens</div><div class='v'>{s['tokens']:,}</div></div>"
        f"<div class='kpi' style='animation-delay:.2s'><div class='l'>Cost</div><div class='v'>${s['cost_usd']}</div></div>"
        f"<div class='kpi' style='animation-delay:.3s'><div class='l'>Model time</div><div class='v'>{s['seconds']}s</div></div></div>"
        f"{let}<div class='two'><div class='card'><h3>Calls by component</h3>{dist}</div>"
        f"<div class='card'><h3>What is recorded for every call</h3><div class='sub'>Time · component · model · temperature · "
        f"prompt version · input hash · raw output · tokens · cost · latency. Human approvals are recorded too. "
        f"Download everything as JSONL below.</div></div></div>"
        f"<div class='card'><h3>Every call, in order</h3>{calls}</div>")
