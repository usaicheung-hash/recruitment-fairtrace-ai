"""Steps 2 and 3 - Blind & Score, with a naive baseline for comparison.

Naive baseline  = how many AI screening tools work today (and the earlier Bias Lab demo):
                  one prompt, the full CV, "rate 0-100 and give a reason".
FairTrace       = (1) Blind Parser: a small LLM FINDS sensitive details, Python REMOVES them
                      (so the model cannot "forget" to redact, and every removal is listed);
                  (2) Evidence-grounded Scorer: a larger LLM scores each rubric criterion 0-5 and must
                      quote the CV; (3) Python checks every quote really is in the CV. No valid quote,
                      no points.
"""

from __future__ import annotations

import difflib
import re
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, pstdev

from . import llm

REPEATS = 3

# ------------------------------------------------------------------ naive baseline (old demo prompt)

NAIVE_PROMPT = """You are an experienced recruiter in Hong Kong screening applications.

JOB DESCRIPTION:
{job}

CANDIDATE CV:
{cv}
{extra}
Rate how suitable this candidate is for the job on a scale from 0 to 100, and give the main
reason in ONE or TWO short sentences.
Reply in exactly this format:
SCORE: <number>
REASON: <your reason>"""
NAIVE_VERSION = "naive-v1-" + llm.sha(NAIVE_PROMPT, 6)


def naive_once(job: str, cv: str, subject: str, run_id: str, extra: str = "", model: str | None = None):
    extra_txt = f"\nIMPORTANT SCREENING RULES FROM THE EMPLOYER:\n{extra}\n" if extra else ""
    reply = llm.chat(NAIVE_PROMPT.format(job=job, cv=cv, extra=extra_txt), model=model or llm.NAIVE_MODEL,
                     component="naive.score", prompt_version=NAIVE_VERSION + ("+rule" if extra else ""),
                     temperature=0.7, max_tokens=120, subject=subject, run_id=run_id)
    m = re.search(r"SCORE:\s*(\d{1,3})", reply, re.I) or re.search(r"\b(\d{1,3})\b", reply)
    r = re.search(r"REASON:\s*(.+)", reply, re.I | re.S)
    if not m:
        return None
    return {"score": min(100.0, float(m.group(1))), "reason": (r.group(1) if r else reply).strip().replace("\n", " ")[:400]}


def naive_score(job: str, cv: str, subject: str, run_id: str, extra: str = "", model: str | None = None,
                repeats: int = REPEATS) -> dict:
    with ThreadPoolExecutor(max_workers=repeats) as ex:
        runs = [x for x in ex.map(lambda _: naive_once(job, cv, subject, run_id, extra, model), range(repeats)) if x]
    if not runs:
        raise RuntimeError("The naive screener did not answer.")
    scores = [r["score"] for r in runs]
    return {"score": round(mean(scores), 1), "sd": round(pstdev(scores), 1), "scores": scores,
            "reasons": [r["reason"] for r in runs]}


# ------------------------------------------------------------------ Blind Parser

REDACT_PROMPT = """Find every detail in this CV that reveals or hints at the candidate's name, gender,
age or birth/graduation year, family or marital status, pregnancy or caregiving, career breaks,
disability or health, race, ethnicity or nationality, religion, or contact details.
Copy each one EXACTLY as it is written in the CV (a few words, not whole sections).
Do NOT flag job-related facts: degrees, universities, employers, job titles, skills, or the languages
a candidate speaks (language skills are a genuine job requirement).

CV:
{cv}

Reply with JSON only:
{{"sensitive": [{{"text": "<exact words from the CV>", "type": "name|gender|age|family|career_break|disability|race|religion|contact"}}]}}"""
REDACT_VERSION = "redact-v1-" + llm.sha(REDACT_PROMPT, 6)

# Deterministic safety net: these are always removed even if the small model misses them.
RULES = [
    (r"[\w.]+@[\w.]+", "contact", "[email removed]"),
    (r"(graduated\s+)(19|20)\d\d", "age", r"\1[year removed]"),
    (r"^Career break[^\n]*\n?", "career_break", ""),
    (r"^[^\n]*(disab|deaf|wheelchair|rehabilitation|sign language)[^\n]*$", "disability",
     "[activity removed: may reveal health or disability]"),
]
JOB_LINE = re.compile(r"^\s*(Languages:|SKILLS|- )|University|College|Diploma|Degree|\b(BBA|BA|BSc|BEng|MSc|MBA)\b", re.I)
ACCEPTED = {"name", "gender", "age", "family", "career_break", "disability", "race", "religion", "contact"}

TOKENS = {
    "name": "[Candidate]", "contact": "[contact removed]", "age": "[removed]", "career_break": "",
    "family": "[removed]", "disability": "[organisation removed]", "race": "[removed]",
    "religion": "[removed]", "gender": "[removed]",
}


def _kind(raw: str) -> str:
    raw = (raw or "").lower()
    for key, words in (("career_break", ("break", "gap", "leave")), ("contact", ("contact", "email", "phone")),
                       ("age", ("age", "year", "birth")), ("disability", ("disab", "health")),
                       ("family", ("family", "marital", "pregnan", "caregiv")), ("race", ("race", "ethnic", "national")),
                       ("religion", ("relig",)), ("gender", ("gender", "sex")), ("name", ("name",))):
        if any(w in raw for w in words):
            return key
    return "other"


def blind(cv: str, subject: str, run_id: str, candidate_label: str = "Candidate") -> dict:
    reply = llm.chat(REDACT_PROMPT.format(cv=cv), model=llm.REDACT_MODEL, component="blind.detect",
                     prompt_version=REDACT_VERSION, temperature=0.0, max_tokens=500, subject=subject, run_id=run_id)
    found = (llm.parse_json(reply) or {}).get("sensitive", []) or []
    text, removed = cv, []
    for pat, kind, rep in RULES:  # deterministic rules first, on the original text
        for m in re.finditer(pat, text, re.I | re.M):
            removed.append({"text": m.group(0).strip(), "type": kind, "by": "rule"})
        text = re.sub(pat, rep, text, flags=re.I | re.M)
    # the candidate's name is always the first line of these CVs
    first = cv.splitlines()[0].strip()
    found = [{"text": first, "type": "name", "rule": True}] + [f for f in found if isinstance(f, dict)]
    found.sort(key=lambda f: _kind(f.get("type")) != "career_break")  # remove whole break lines first
    for item in found:
        span, kind = (item.get("text") or "").strip(), _kind(item.get("type"))
        if (len(span) < 4 or span.isdigit() or kind not in ACCEPTED or span not in text
                or span.startswith("[") or "example.com" in span
                or re.fullmatch(r"[\d\s\-–]+(present)?", span, re.I) or span.lower() == "hong kong"):
            continue
        line = next((ln for ln in text.splitlines() if span in ln), "")
        if not item.get("rule") and JOB_LINE.search(line):  # never remove job-related evidence
            continue
        if kind == "career_break":  # remove the whole line, not only the words
            line = next((ln for ln in text.splitlines() if span in ln), span)
            text = text.replace(line + "\n", "").replace(line, "")
            removed.append({"text": line, "type": kind, "by": "AI"})
            continue
        token = candidate_label if kind == "name" else TOKENS.get(kind, "[removed]")
        text = text.replace(span, token)
        removed.append({"text": span, "type": kind, "by": "rule" if item.get("rule") else "AI"})
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return {"blind_cv": text, "removed": removed}


# ------------------------------------------------------------------ Evidence-grounded Scorer

SCORE_PROMPT = """You are a careful recruiter using a structured rubric. Score the CV against EACH
criterion from 0 (no evidence) to 5 (strong evidence). Judge only job-related evidence written in
the CV. Missing personal details have been removed on purpose; never guess them and never let them
affect the score.
For every criterion copy ONE short exact quote from the CV as evidence (or "" if there is none).

RUBRIC:
{rubric}

CV:
{cv}

Reply with JSON only:
{{"criteria": [{{"name": "<criterion name>", "score": 0, "evidence": "<exact quote>"}}],
  "summary": "<one sentence>"}}"""
SCORE_VERSION = "evidence-v1-" + llm.sha(SCORE_PROMPT, 6)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w%$+.\s]", " ", s.lower())).strip()


def verify_quote(quote: str, cv: str) -> bool:
    """True if the quote really appears in the CV (exact, or near-exact after normalising)."""
    q, c = _norm(quote), _norm(cv)
    if len(q) < 4:
        return False
    if q in c:
        return True
    words = c.split()
    n = len(q.split())
    best = max((difflib.SequenceMatcher(None, q, " ".join(words[i:i + n])).ratio()
                for i in range(max(1, len(words) - n + 1))), default=0)
    return best >= 0.85


def rubric_text(rubric: list[dict]) -> str:
    return "\n".join(f"- {c['name']} (weight {c['weight']}): {c.get('evidence_needed', '')}" for c in rubric)


def evidence_once(cv: str, rubric: list[dict], subject: str, run_id: str, model: str | None = None):
    reply = llm.chat(SCORE_PROMPT.format(rubric=rubric_text(rubric), cv=cv), model=model or llm.SCORER_MODEL,
                     component="fairtrace.score", prompt_version=SCORE_VERSION, temperature=0.3,
                     max_tokens=700, subject=subject, run_id=run_id)
    data = llm.parse_json(reply) or {}
    got = {(_norm(c.get("name", ""))): c for c in data.get("criteria", []) if isinstance(c, dict)}
    rows, total = [], 0.0
    listed = [c for c in data.get("criteria", []) if isinstance(c, dict)]
    if len(listed) != len(rubric):
        return None  # incomplete answer: the caller asks again
    for i, crit in enumerate(rubric):
        c = (got.get(_norm(crit["name"])) or next((v for k, v in got.items() if _norm(crit["name"])[:12] in k), None)
             or listed[i])  # same order as the rubric
        raw = max(0.0, min(5.0, float(c.get("score", 0) or 0)))
        ev = (c.get("evidence") or "").strip()
        ok = verify_quote(ev, cv) if ev else False
        pts = crit["weight"] * (raw if ok else 0) / 5
        total += pts
        rows.append({"criterion": crit["name"], "weight": crit["weight"], "raw": raw, "evidence": ev,
                     "verified": ok, "points": round(pts, 1)})
    if not data.get("criteria"):
        return None
    return {"score": round(total, 1), "criteria": rows, "summary": data.get("summary", "")}


def evidence_score(cv: str, rubric: list[dict], subject: str, run_id: str, model: str | None = None) -> dict:
    def one(_):
        for _try in range(3):  # an incomplete or unreadable answer is asked again (and stays in the trace)
            res = evidence_once(cv, rubric, subject, run_id, model)
            if res:
                return res
        return None

    with ThreadPoolExecutor(max_workers=REPEATS) as ex:
        runs = [x for x in ex.map(one, range(REPEATS)) if x]
    if not runs:
        raise RuntimeError("The FairTrace scorer did not answer.")
    scores = [r["score"] for r in runs]
    checked = [c for r in runs for c in r["criteria"] if c["evidence"]]
    return {"score": round(mean(scores), 1), "sd": round(pstdev(scores), 1), "scores": scores,
            "runs": runs, "evidence_valid": round(100 * sum(c["verified"] for c in checked) / max(1, len(checked)))}


# ------------------------------------------------------------------ candidate explanation

LETTER_PROMPT = """Write a short, respectful message (90-120 words) to a job applicant explaining the
screening result for the role below. Use only the rubric results given. Mention the two strongest
points and, if any, one area with little evidence and what they could add. Do not mention any personal
characteristics. End by saying a human recruiter makes the final decision and the applicant may ask
for a review.

ROLE: {role}
RESULT: {score}/100 ({decision})
RUBRIC RESULTS:
{rows}"""
LETTER_VERSION = "letter-v1-" + llm.sha(LETTER_PROMPT, 6)


def letter(role: str, result: dict, decision: str, subject: str, run_id: str) -> str:
    best = result["runs"][0]
    rows = "\n".join(f"- {c['criterion']}: {c['raw']}/5, evidence: \"{c['evidence']}\"" for c in best["criteria"])
    return llm.chat(LETTER_PROMPT.format(role=role, score=result["score"], decision=decision, rows=rows),
                    model=llm.SCORER_MODEL, component="explain.letter", prompt_version=LETTER_VERSION,
                    temperature=0.4, max_tokens=300, subject=subject, run_id=run_id)
