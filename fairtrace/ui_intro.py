"""🚀 Introduction page: what FairTrace is, who it is for, and the match against the naive AI (with confetti)."""

from __future__ import annotations

import random

from . import trace
from .ui import BAD, FAIR, GOOD, NAIVE, esc, spread, wrap

INTRO_CSS = """
<style>
.ft .vs{position:relative;overflow:hidden;border-radius:20px;padding:22px 22px 18px;
  background:linear-gradient(135deg,#fff7ed 0%,#ffffff 45%,#eef2ff 100%);border:1px solid #e2e8f0}
.ft .vs-head{display:grid;grid-template-columns:1fr 90px 1fr;align-items:center;text-align:center;margin-bottom:10px}
.ft .vs-team{font-size:1.25rem;font-weight:800}
.ft .vs-badge{width:62px;height:62px;margin:auto;border-radius:50%;background:#0f172a;color:#fff;display:flex;
  align-items:center;justify-content:center;font-weight:900;font-size:1.2rem;animation:pop .6s cubic-bezier(.2,.9,.3,1.4) both}
.ft .round{display:grid;grid-template-columns:1fr 1.1fr 1fr;align-items:center;gap:10px;padding:9px 12px;margin:6px 0;
  background:#fff;border:1px solid #e2e8f0;border-radius:12px;animation:rise .5s ease-out both}
.ft .round .mid{text-align:center;font-weight:700;color:#334155;font-size:.9rem}
.ft .round .l{text-align:right}.ft .round .r{text-align:left}
.ft .round .val{font-size:1.15rem;font-weight:800}
.ft .round.win-r .r .val{color:#4f46e5}.ft .round.win-r .l .val{color:#94a3b8}
.ft .round .tick{display:inline-block;margin-left:6px;animation:pop .5s ease-out both}
.ft .final{margin-top:12px;text-align:center;padding:16px;border-radius:16px;color:#fff;
  background:linear-gradient(120deg,#3730a3,#4f46e5 50%,#0f766e);animation:rise .6s ease-out both}
.ft .final, .ft .final *{color:#fff !important}
.ft .final .big{font-size:2.1rem;font-weight:900;letter-spacing:-.02em}
.ft .trophy{display:inline-block;font-size:2.6rem;animation:bounce 1.2s ease-in-out infinite}
.ft .confetti{position:absolute;inset:0;pointer-events:none;overflow:hidden;z-index:5}
.ft .confetti i{position:absolute;left:50%;top:86%;width:9px;height:14px;border-radius:2px;opacity:0;
  animation:burst var(--t) cubic-bezier(.15,.7,.3,1) var(--d) forwards}
@keyframes burst{0%{opacity:1;transform:translate(0,0) rotate(0)}
  70%{opacity:1}100%{opacity:0;transform:translate(var(--dx),var(--dy)) rotate(var(--r))}}
@keyframes bounce{50%{transform:translateY(-6px) rotate(-6deg)}}
.ft .who{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.ft .icon{font-size:1.7rem}
</style>
"""

COLORS = ["#4f46e5", "#16a34a", "#f59e0b", "#ec4899", "#0ea5e9", "#a855f7", "#ef4444", "#14b8a6"]


def confetti(n: int = 90, seed: int = 7) -> str:
    rnd = random.Random(seed)
    pieces = []
    for _ in range(n):
        dx = rnd.randint(-560, 560)
        dy = rnd.randint(-760, 40)
        pieces.append(
            f"<i style='--dx:{dx}px;--dy:{dy}px;--r:{rnd.randint(-720, 720)}deg;--t:{rnd.uniform(1.6, 2.8):.2f}s;"
            f"--d:{rnd.uniform(.9, 1.6):.2f}s;background:{rnd.choice(COLORS)};"
            f"width:{rnd.randint(6, 11)}px;height:{rnd.randint(8, 16)}px;"
            f"border-radius:{rnd.choice(['2px', '50%'])}'></i>")
    return "<div class='confetti'>" + "".join(pieces) + "</div>"


def _round(i, label, naive, fair, winner="fair", note=""):
    cls = "win-r" if winner == "fair" else ""
    tick = "<span class='tick' style='animation-delay:{:.2f}s'>🏅</span>".format(.3 + i * .12) if winner == "fair" else ""
    draw = " <span class='tiny'>(draw)</span>" if winner == "draw" else ""
    return (f"<div class='round {cls}' style='animation-delay:{.15 + i * .12:.2f}s'>"
            f"<div class='l'><span class='val' style='color:{NAIVE}'>{naive}</span></div>"
            f"<div class='mid'>{esc(label)}{draw}<div class='tiny' style='font-weight:400'>{esc(note)}</div></div>"
            f"<div class='r'><span class='val' style='color:{FAIR}'>{fair}</span>{tick}</div></div>")


def intro_html(replay: dict, celebrate: int = 0) -> str:
    rows = replay["screen"]["rows"]
    a = replay["audit"]
    flags = replay["rubric"]["lint"]["flags"]
    ns, fs = spread(rows, "naive"), spread(rows, "fair")
    cut_n = sum(1 for r in rows if r["qualified"] and not r["naive"]["shortlist"])
    cut_f = sum(1 for r in rows if r["qualified"] and not r["fair"]["shortlist"])
    evid = round(sum(r["fair"]["evidence_valid"] for r in rows) / len(rows))
    tr = replay["screen"]["trace"]
    per = len(rows)
    nc = trace.summary([x for x in tr if x["component"].startswith("naive")])["cost_usd"] / per
    fc = trace.summary([x for x in tr if x["component"].startswith(("blind", "fairtrace"))])["cost_usd"] / per
    flagged = sum(1 for r in a["results"].values() if r["bias"])
    rounds = [
        ("Same score for the same skills", f"spread {ns:g}", f"spread {fs:g}", "fair", "5 equally qualified CVs"),
        ("Qualified people wrongly cut", str(cut_n), str(cut_f), "fair", "from the shortlist"),
        ("Points backed by CV evidence", "0%", f"{evid}%", "fair", "every quote checked by Python"),
        ("Job ad checked for bias", "✗", f"✓ {len(flags)}", "fair", "risky phrases flagged"),
        ("Tests itself for bias", "✗", f"✓ {flagged} flags", "fair", "AI agent + statistics"),
        ("Every decision recorded", "✗", "✓ trace", "fair", "model, prompt, output, cost"),
        ("Cost per CV", f"${nc:.4f}", f"${fc:.4f}", "draw", "both under 0.1 US cent"),
    ]
    wins = sum(1 for r in rounds if r[3] == "fair")
    draws = sum(1 for r in rounds if r[3] == "draw")
    # a different seed each time "celebrate again" is pressed, so the browser replays the animation
    burst = confetti(seed=7 + celebrate)
    match = (
        f"<div class='vs'>{burst}"
        "<div class='vs-head'>"
        f"<div class='vs-team' style='color:{NAIVE}'>🤖 Naive AI<div class='tiny' style='font-weight:400'>“rate this CV 0–100”</div></div>"
        "<div class='vs-badge'>VS</div>"
        f"<div class='vs-team' style='color:{FAIR}'>🛡️ FairTrace<div class='tiny' style='font-weight:400'>rubric · blind · evidence · audit · trace</div></div>"
        "</div>"
        + "".join(_round(i, *r) for i, r in enumerate(rounds))
        + f"<div class='final' style='animation-delay:{.2 + len(rounds) * .12:.2f}s'><span class='trophy'>🏆</span>"
        f"<div class='big'>FairTrace wins {wins} – 0</div>"
        f"<div style='opacity:.9'>{draws} draw on cost · same CVs, fairer result, proof for every point</div></div></div>")

    cards = "".join(
        f"<div class='kpi' style='animation-delay:{i * .1:.2f}s'><div class='icon'>{ic}</div>"
        f"<div style='font-weight:800;margin:4px 0;font-size:1.05rem'>{esc(t)}</div><div class='sub'>{d}</div></div>"
        for i, (ic, t, d) in enumerate([
            ("⚠️", "The problem: CV bias",
             "AI CV screeners are fast, but they can give <b>the same skills different scores</b>. In our test a "
             "parental break, a 1996 graduation year or a name changed the score, and the AI could not show why."),
            ("🛡️", "Our solution: Recruitment FairTrace AI",
             "A GenAI screening assistant for HR: a <b>fair job ad and rubric</b>, <b>personal details hidden</b>, "
             "<b>a CV quote behind every point</b>, an <b>AI agent that audits for bias</b> and a <b>record of every "
             "decision</b>."),
            ("👥", "Who uses it",
             "<b>HR and recruiters</b> screen faster with evidence they can defend. <b>Hiring managers</b> get a fairer "
             "shortlist. <b>Compliance</b> gets an audit trail for Hong Kong's anti-discrimination ordinances and "
             "PCPD guidance."),
        ]))
    steps = "".join(
        f"<div class='kpi' style='animation-delay:{.2 + i * .08:.2f}s;padding:10px 12px'>"
        f"<b style='color:{c}'>{n}</b><div class='tiny'>{esc(t)}</div></div>"
        for i, (n, t, c) in enumerate([("① Fair Rubric", "check the job ad, build the rubric", "#0284c7"),
                                       ("② Blind & Score", "naive AI vs FairTrace on 6 applicants", FAIR),
                                       ("③ Auditor", "watch the AI agent test for bias", "#d97706"),
                                       ("④ Decision Trace", "open the record of any decision", GOOD),
                                       ("🏁 Summary", "the whole test on one page", BAD)]))
    return INTRO_CSS + wrap(
        f"<div class='row'>{cards}</div>"
        f"<div class='card' style='padding:16px'><h3>🥊 The match: Naive AI vs FairTrace</h3>{match}"
        f"<div class='tiny' style='margin-top:8px'>From one saved run on synthetic data (one job, six applicants). "
        f"Illustrative prototype, not a scientific audit.</div></div>"
        f"<div class='card'><h3>How to explore</h3><div class='row'>{steps}</div>"
        f"<div class='tiny' style='margin-top:8px'>Every page opens with a saved real run: no password and no AI credits needed.</div></div>")
