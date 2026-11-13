"""HTML rendering for the Gradio app (kept apart from the logic)."""

from __future__ import annotations

import html
import re

from . import llm, trace

CSS = """
<style>
.ft{font-family:Inter,system-ui,sans-serif;color:#1f2937;line-height:1.5}
.ft .card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px 18px;margin:8px 0}
.ft h3{margin:0 0 8px 0;font-size:1.05rem}
.ft .muted{color:#6b7280;font-size:.9rem}
.ft table{border-collapse:collapse;width:100%;font-size:.92rem}
.ft th{background:#f3f4f6;text-align:left;padding:7px 8px;border-bottom:1px solid #e5e7eb}
.ft td{padding:7px 8px;border-bottom:1px solid #f1f5f9;vertical-align:top}
.ft mark.risk{background:#fee2e2;color:#991b1b;border-radius:4px;padding:0 3px;font-weight:600}
.ft mark.gone{background:#e5e7eb;color:#6b7280;text-decoration:line-through;border-radius:4px;padding:0 3px}
.ft pre{white-space:pre-wrap;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:10px;font-size:.85rem;margin:0}
.ft .pill{display:inline-block;border-radius:999px;padding:1px 9px;font-size:.8rem;font-weight:600}
.ft .ok{background:#dcfce7;color:#166534}.ft .bad{background:#fee2e2;color:#991b1b}.ft .warn{background:#fef3c7;color:#92400e}
.ft .grey{background:#f3f4f6;color:#374151}
.ft .bar{height:14px;border-radius:7px;display:inline-block;vertical-align:middle}
.ft .kpis{display:flex;gap:10px;flex-wrap:wrap}
.ft .kpi{flex:1;min-width:150px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px}
.ft .kpi b{display:block;font-size:1.5rem}
.ft .step{border-left:3px solid #6366f1;padding:6px 12px;margin:6px 0;background:#f8fafc;border-radius:0 8px 8px 0}
.ft .step.bias{border-color:#dc2626;background:#fef2f2}.ft .step.fix{border-color:#16a34a;background:#f0fdf4}
.ft .two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:800px){.ft .two{grid-template-columns:1fr}}
</style>
"""


def wrap(body: str) -> str:
    return CSS + f'<div class="ft">{body}</div>'


def esc(s) -> str:
    return html.escape(str(s))


def pill(text, kind="grey") -> str:
    return f'<span class="pill {kind}">{esc(text)}</span>'


# ------------------------------------------------------------------ tab 1: Fair Rubric

def highlight(ad: str, phrases: list[str]) -> str:
    out = esc(ad)
    for p in sorted({p for p in phrases if p}, key=len, reverse=True):
        out = re.sub(re.escape(esc(p)), lambda m: f'<mark class="risk">{m.group(0)}</mark>', out, flags=re.I)
    return f"<pre>{out}</pre>"


def rubric_lint_html(r: dict) -> str:
    flags = r["lint"]["flags"]
    rows = "".join(
        f"<tr><td><b>{esc(f.get('phrase'))}</b></td><td>{esc(f.get('ground'))}</td><td>{esc(f.get('why'))}</td>"
        f"<td>{esc(f.get('rewrite'))}</td><td class='muted'>{esc(f.get('law') or '-')}</td></tr>" for f in flags)
    return wrap(
        f"<div class='card'><h3>① The job ad HR wrote</h3>{highlight(r['risky_ad'], [f.get('phrase') for f in flags])}"
        f"<p class='muted'>Red = wording that can screen people out for who they are, not what they can do.</p></div>"
        f"<div class='card'><h3>⚠️ {len(flags)} risky phrases found</h3>"
        f"<table><tr><th>Phrase</th><th>Protected ground</th><th>Why it is risky</th><th>Fairer wording</th>"
        f"<th>Hong Kong rule</th></tr>{rows}</table>"
        f"<p class='muted'>Found by the LLM reviewer and double-checked by a fixed word list "
        f"({r['lint']['word_list_hits']} word-list hits), so a missed phrase is still caught.</p></div>")


def rubric_approved_html(r: dict) -> str:
    rows = "".join(f"<tr><td><b>{esc(c['name'])}</b></td><td>{c['weight']}</td><td>{esc(c.get('evidence_needed', ''))}</td></tr>"
                   for c in r["criteria"])
    return wrap(
        f"<div class='two'><div class='card'><h3>✅ Approved job ad (AI rewrite, accepted by HR)</h3>"
        f"<pre>{esc(r['approved_ad'])}</pre></div>"
        f"<div class='card'><h3>📏 Scoring rubric (job-related only)</h3><table><tr><th>Criterion</th><th>Weight</th>"
        f"<th>Evidence that earns points</th></tr>{rows}</table>"
        f"<p class='muted'>Built by the LLM from the approved ad. No age, gender, family status, nationality, "
        f"disability, name, career gaps or school prestige.</p></div></div>")


# ------------------------------------------------------------------ tab 2: Screen & Compare

def _bar(score, colour):
    return f'<span class="bar" style="width:{max(2, score) * 1.4:.0f}px;background:{colour}"></span> <b>{score}</b>'


def spread(rows, key):
    q = [r[key]["score"] for r in rows if r["qualified"]]
    return round(max(q) - min(q), 1)


def screen_table_html(s: dict) -> str:
    rows = s["rows"]
    trs = ""
    for r in rows:
        n, f = r["naive"], r["fair"]
        trs += (f"<tr><td><b>{r['id']}</b> {esc(r['name'])}<br><span class='muted'>{esc(r['difference'])}</span></td>"
                f"<td>{_bar(n['score'], '#f59e0b')} <span class='muted'>±{n['sd']}</span><br>"
                f"{pill('Shortlisted', 'ok') if n['shortlist'] else pill('Not shortlisted', 'bad')} #{n['rank']}</td>"
                f"<td>{_bar(f['score'], '#4f46e5')} <span class='muted'>±{f['sd']}</span><br>"
                f"{pill('Shortlisted', 'ok') if f['shortlist'] else pill('Not shortlisted', 'bad')} #{f['rank']}</td>"
                f"<td>{pill(str(f['evidence_valid']) + '% verified', 'ok' if f['evidence_valid'] >= 90 else 'warn')}</td></tr>")
    ns, fs = spread(rows, "naive"), spread(rows, "fair")
    allrec = s["trace"]
    nt = trace.summary([x for x in allrec if x["component"].startswith("naive")])
    ft = trace.summary([x for x in allrec if x["component"].startswith(("blind", "fairtrace"))])
    per = len(rows)
    return wrap(
        "<div class='card'><div class='kpis'>"
        f"<div class='kpi'><span class='muted'>Score spread among the 5 equally qualified CVs</span>"
        f"<b>{ns} → {fs}</b><span class='muted'>Naive AI → FairTrace (points)</span></div>"
        f"<div class='kpi'><span class='muted'>Points backed by a verified CV quote</span>"
        f"<b>{round(sum(r['fair']['evidence_valid'] for r in rows) / per)}%</b><span class='muted'>Naive AI: no evidence at all</span></div>"
        f"<div class='kpi'><span class='muted'>Cost per CV (3 runs each)</span>"
        f"<b>${nt['cost_usd'] / per:.4f} → ${ft['cost_usd'] / per:.4f}</b><span class='muted'>estimated, US$</span></div>"
        f"<div class='kpi'><span class='muted'>Model time per CV</span>"
        f"<b>{nt['seconds'] / per:.0f}s → {ft['seconds'] / per:.0f}s</b><span class='muted'>sum of calls; runs in parallel</span></div>"
        "</div></div>"
        "<div class='card'><h3>Same batch of 6 applicants, two screeners</h3>"
        f"<table><tr><th>Applicant (what is different)</th><th>🟠 Naive AI ({llm.short(llm.NAIVE_MODEL)}, one prompt)</th>"
        f"<th>🟣 FairTrace ({llm.short(llm.SCORER_MODEL)}, blind + rubric + evidence)</th><th>Evidence check</th></tr>{trs}</table>"
        "<p class='muted'>A1-A5 have exactly the same education, experience and skills; only one personal detail differs. "
        "A6 really has less experience. Shortlist rule (same for both): the top 3, plus anyone within 3 points of the 3rd score (smaller gaps are within the AI's own noise). Scores are the mean of 3 runs (± = run-to-run spread).</p></div>")


def candidate_html(r: dict) -> str:
    removed = r["blind"]["removed"]
    orig = esc(r["cv"])
    for it in sorted(removed, key=lambda x: -len(x["text"])):
        orig = orig.replace(esc(it["text"]), f'<mark class="gone">{esc(it["text"])}</mark>')
    best = r["fair"]["runs"][0]
    crit = "".join(
        f"<tr><td>{esc(c['criterion'])} <span class='muted'>({c['weight']})</span></td><td>{c['raw']}/5</td>"
        f"<td>“{esc(c['evidence'])}”</td><td>{pill('✓ in CV', 'ok') if c['verified'] else pill('✗ not found - 0 pts', 'bad')}</td>"
        f"<td><b>{c['points']}</b></td></tr>" for c in best["criteria"])
    rem = "".join(f"<li>{pill(it['type'], 'grey')} {esc(it['text'])} <span class='muted'>({it['by']})</span></li>" for it in removed)
    reasons = "".join(f"<li>{esc(x)}</li>" for x in r["naive"]["reasons"])
    return wrap(
        f"<div class='two'><div class='card'><h3>Original CV</h3><pre>{orig}</pre>"
        f"<p class='muted'>Grey = removed by the Blind Parser before scoring:</p><ul>{rem}</ul></div>"
        f"<div class='card'><h3>What the FairTrace scorer sees</h3><pre>{esc(r['blind']['blind_cv'])}</pre></div></div>"
        f"<div class='card'><h3>🟣 FairTrace score {r['fair']['score']} - every point has a quote</h3>"
        f"<table><tr><th>Criterion</th><th>Score</th><th>Evidence quoted by the AI</th><th>Python check</th><th>Points</th></tr>{crit}</table>"
        f"<p class='muted'>Runs: {r['fair']['scores']}</p></div>"
        f"<div class='card'><h3>🟠 Naive AI score {r['naive']['score']} - its reasons</h3><ul>{reasons}</ul>"
        f"<p class='muted'>Runs: {r['naive']['scores']}</p></div>")


def live_cv_html(b: dict, f: dict) -> str:
    fake = {"cv": "", "blind": b, "fair": f, "naive": {"score": "-", "reasons": [], "scores": []}}
    best = f["runs"][0]
    crit = "".join(
        f"<tr><td>{esc(c['criterion'])}</td><td>{c['raw']}/5</td><td>“{esc(c['evidence'])}”</td>"
        f"<td>{pill('✓', 'ok') if c['verified'] else pill('✗ 0 pts', 'bad')}</td><td>{c['points']}</td></tr>" for c in best["criteria"])
    rem = "".join(f"<li>{pill(it['type'])} {esc(it['text'])}</li>" for it in b["removed"]) or "<li>nothing</li>"
    del fake
    return wrap(f"<div class='two'><div class='card'><h3>Removed before scoring</h3><ul>{rem}</ul></div>"
                f"<div class='card'><h3>Blind CV</h3><pre>{esc(b['blind_cv'])}</pre></div></div>"
                f"<div class='card'><h3>FairTrace score {f['score']} (runs {f['scores']})</h3><table><tr><th>Criterion</th>"
                f"<th>Score</th><th>Evidence</th><th>Check</th><th>Points</th></tr>{crit}</table></div>")


# ------------------------------------------------------------------ tab 3: Auditor

TOOL_ICON = {"test_attribute": "🧪", "inspect_reasons": "🔍", "apply_fix": "🛠️", "finish": "🏁"}


def step_html(st: dict) -> str:
    obs = st["observation"]
    cls = "bias" if "BIAS" in obs or "mention" in obs and not obs.startswith("0 of") else ("fix" if st["tool"] in ("apply_fix", "finish") else "")
    args = ", ".join(f"{k}={v}" for k, v in (st.get("args") or {}).items())
    return (f"<div class='step {cls}'><b>{TOOL_ICON.get(st['tool'], '•')} Step {st['n']} · {st['tool']}({esc(args)})</b> "
            f"<span class='muted'>- {esc(st.get('why', ''))} <i>[{esc(st.get('source', ''))}]</i></span><br>{esc(obs)}</div>")


def timeline_html(steps: list[dict], running: bool = False) -> str:
    body = "".join(step_html(s) for s in steps)
    if running:
        body += "<div class='step'>⏳ thinking…</div>"
    return wrap(f"<div class='card'><h3>🛩️ Agent timeline (plan → act → observe)</h3>{body or '<span class=muted>Press ▶ to start.</span>'}</div>")


def audit_results_html(a: dict, approval: str | None = None) -> str:
    rows = ""
    for k, r in a["results"].items():
        after = {fix: res[k]["gap"] for fix, res in a["fixes"].items() if k in res}
        rows += (f"<tr><td><b>{esc(k)}</b></td><td>{r['gap']}</td><td>{r['noise']}</td>"
                 f"<td>{pill('BIAS', 'bad') if r['bias'] else pill('no bias', 'ok')}</td>"
                 f"<td>{esc(r['lowest'])}</td>"
                 f"<td>{' · '.join(f'{fx}: <b>{g}</b>' for fx, g in after.items()) or '-'}</td></tr>")
    detail = ""
    for k, r in a["results"].items():
        bars = "".join(f"<div>{esc(x['desc'])}: {_bar(x['score'], '#dc2626' if x['label'] == r['lowest'] and r['bias'] else '#94a3b8')}</div>"
                       for x in r["rows"])
        f = r.get("forensics")
        q = "".join(f"<blockquote class='muted'>“{esc(t)}”</blockquote>" for t in (f or {}).get("quotes", []))
        detail += f"<div class='card'><h3>{esc(k)}</h3>{bars}{q}</div>" if r["bias"] else ""
    fixes = ""
    for fix, res in a["fixes"].items():
        for k, r in res.items():
            bars = "".join(f"<div>{esc(x['desc'])}: {_bar(x['score'], '#16a34a')}</div>" for x in r["rows"])
            fixes += f"<div class='card'><h3>After fix “{esc(fix)}” - {esc(k)} (gap {r['gap']})</h3>{bars}</div>"
    s = trace.summary(a["trace"])
    status = (pill("✅ Approved by human: " + approval, "ok") if approval and approval.startswith("Approved")
              else pill("❌ " + approval, "bad") if approval else pill("⏸ Waiting for human approval", "warn"))
    return wrap(
        f"<div class='card'><h3>Audit result {status}</h3><p>{esc(a['summary'])}</p>"
        f"<table><tr><th>Attribute</th><th>Gap</th><th>Noise</th><th>Verdict (Python statistics)</th><th>Lowest</th>"
        f"<th>Gap after fix</th></tr>{rows}</table>"
        f"<p class='muted'>Bias = gap ≥ 3 points and more than twice the screener's run-to-run noise. "
        f"{s['calls']} model calls · {s['tokens']:,} tokens · about US${s['cost_usd']}</p></div>"
        f"<div class='two'><div>{detail}</div><div>{fixes}</div></div>")


# ------------------------------------------------------------------ model choice

def benchmark_html(results: list[dict]) -> str:
    def row(m):
        chosen = m["model"] == llm.SCORER_MODEL and m["method"] == "fair"
        return (f"<tr style='{'background:#eef2ff' if chosen else ''}'><td><b>{esc(llm.short(m['model']))}</b>"
                f"{' ' + pill('chosen', 'ok') if chosen else ''}</td>"
                f"<td>{'🟣 FairTrace' if m['method'] == 'fair' else '🟠 Naive prompt'}</td>"
                f"<td><b>{m['spread']}</b></td><td>{m['sd']}</td><td>{m['separation']}</td>"
                f"<td>{str(m['evidence']) + '%' if 'evidence' in m else '-'}</td>"
                f"<td>${m['cost_per_cv']:.4f}</td><td>{m['sec_per_cv']}s</td></tr>")
    trs = "".join(row(m) for m in sorted(results, key=lambda m: (m["method"] != "fair", m["spread"])))
    return wrap(
        "<div class='card'><h3>📊 Model selection: same 6 applicants, 3 models, 2 methods (3 runs per CV)</h3>"
        "<table><tr><th>Model</th><th>Method</th><th>Unfair spread ↓<br><span class='muted'>gap among 5 equal CVs</span></th>"
        "<th>Run-to-run SD ↓</th><th>Separation ↑<br><span class='muted'>qualified minus weak CV</span></th>"
        "<th>Evidence verified ↑</th><th>Cost / CV</th><th>Model time / CV</th></tr>"
        f"{trs}</table><p class='muted'>Cost is estimated from token counts and the provider prices listed on the Hugging Face "
        "router (Nov 2026). Model time is the sum of calls; calls run in parallel. A fair screener needs a small spread "
        "AND a large separation: it must still tell a strong CV from a weak one.</p></div>")


# ------------------------------------------------------------------ tab 4: Decision Trace

def trace_html(recs: list[dict], letter: str = "") -> str:
    trs = "".join(
        f"<tr><td class='muted'>{esc(r['time'][11:])}</td><td>{esc(r['component'])}</td><td>{esc(llm.short(r.get('model', '-')))}</td>"
        f"<td>{r.get('temperature', '-')}</td><td class='muted'>{esc(r.get('prompt_version', ''))}<br>in#{esc(r.get('input_hash', ''))}</td>"
        f"<td><pre>{esc(r.get('raw_output', r.get('observation', ''))[:600])}</pre></td>"
        f"<td>{r.get('tokens_in', 0) + r.get('tokens_out', 0)}</td><td>{r.get('latency_s', '-')}</td></tr>" for r in recs)
    s = trace.summary(recs)
    let = f"<div class='card'><h3>✉️ Explanation for the applicant (AI draft, sent after human review)</h3><p>{esc(letter)}</p></div>" if letter else ""
    return wrap(
        f"{let}<div class='card'><h3>🛩️ Decision Trace - {s['calls']} recorded model calls, {s['tokens']:,} tokens, "
        f"about US${s['cost_usd']}</h3><table><tr><th>Time</th><th>Component</th><th>Model</th><th>Temp</th>"
        f"<th>Prompt version / input</th><th>Raw model output</th><th>Tokens</th><th>Sec</th></tr>{trs}</table></div>")
