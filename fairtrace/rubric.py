"""Step 1 - Fair Rubric.

(a) Proxy lint: find wording in a job ad that screens people out for who they are rather than what
    they can do. A fixed word list (deterministic, explainable) is combined with an LLM that explains
    each risk and suggests a fairer rewrite.
(b) Rubric builder: the LLM turns the (fixed) job ad into 4-6 job-relevant criteria with weights.
    HR reviews and approves the rubric before any CV is scored.
"""

from __future__ import annotations

import re

from . import llm

# phrase pattern -> (protected ground, Hong Kong rule it may conflict with)
PROXY_LEXICON = [
    (r"\byoung\b|\byouthful\b|digital native|recent graduate|aged\s*\d{2}\s*-\s*\d{2}|\b(19|20)\d\d or later\b",
     "Age", "No HK age law, but the Labour Department's Practical Guide on eliminating age discrimination applies"),
    (r"native (english |cantonese )?speaker|mother tongue|local (chinese )?only",
     "Race / national origin", "Race Discrimination Ordinance (Cap. 602)"),
    (r"no career gaps?|continuous employment|no gaps",
     "Sex / family status / disability (proxy)", "Sex Discrimination, Family Status and Disability Discrimination Ordinances"),
    (r"without family commitments|no family commitments|single|unmarried|no children",
     "Family status / marital status", "Family Status Discrimination Ordinance (Cap. 527); Sex Discrimination Ordinance (Cap. 480)"),
    (r"able-bodied|physically fit|no disabilit",
     "Disability", "Disability Discrimination Ordinance (Cap. 487)"),
    (r"\bmale\b|\bfemale\b|\bhe will\b|\bshe will\b",
     "Sex", "Sex Discrimination Ordinance (Cap. 480)"),
]

LINT_PROMPT = """You are an equal-opportunity reviewer for a Hong Kong employer.
Read the job advertisement and list every phrase that could screen people out because of age, sex,
pregnancy, family status, marital status, disability, race or national origin, or that acts as a
proxy for these (for example "no career gaps" or "digital native").
For each phrase give the exact words from the ad, the protected ground, why it is risky
(one sentence) and a fairer job-related rewrite.
Then give the whole advertisement rewritten without these risks, keeping every genuine job requirement.

JOB ADVERTISEMENT:
{ad}

Reply with JSON only:
{{"flags": [{{"phrase": "...", "ground": "...", "why": "...", "rewrite": "..."}}],
  "rewritten_ad": "..."}}"""

RUBRIC_PROMPT = """You are designing a structured, job-related scoring rubric for screening CVs.
Read the job advertisement and create 5 criteria that measure ONLY abilities and experience needed
for the job. Do not include age, gender, family status, nationality, disability, name, career gaps,
school prestige or "culture fit". Weights must add up to 100.
For each criterion describe what evidence in a CV earns a high score.

JOB ADVERTISEMENT:
{ad}

Reply with JSON only:
{{"criteria": [{{"name": "...", "weight": 20, "evidence_needed": "..."}}]}}"""

LINT_VERSION = "lint-v1-" + llm.sha(LINT_PROMPT, 6)
RUBRIC_VERSION = "rubric-v1-" + llm.sha(RUBRIC_PROMPT, 6)


def lexicon_flags(ad: str) -> list[dict]:
    out = []
    for pat, ground, law in PROXY_LEXICON:
        for m in re.finditer(pat, ad, re.I):
            out.append({"phrase": m.group(0), "ground": ground, "law": law})
    return out


def lint(ad: str, run_id: str = "") -> dict:
    reply = llm.chat(LINT_PROMPT.format(ad=ad), model=llm.SCORER_MODEL, component="rubric.lint",
                     prompt_version=LINT_VERSION, temperature=0.1, max_tokens=1500, run_id=run_id, subject="job_ad")
    data = llm.parse_json(reply) or {}
    flags = data.get("flags") or []
    lex = lexicon_flags(ad)
    # attach the HK law from the word list where the LLM flag overlaps a lexicon hit
    for f in flags:
        f["law"] = next((x["law"] for x in lex if x["phrase"].lower() in f.get("phrase", "").lower()
                         or f.get("phrase", "").lower() in x["phrase"].lower()), "")
        f["also_found_by_word_list"] = bool(f["law"])
    missed = [x for x in lex if not any(x["phrase"].lower() in f.get("phrase", "").lower() for f in flags)]
    for x in missed:  # the deterministic list is a safety net if the LLM misses something
        flags.append({"phrase": x["phrase"], "ground": x["ground"], "why": "Found by the fixed word list.",
                      "rewrite": "", "law": x["law"], "also_found_by_word_list": True})
    return {"flags": flags, "rewritten_ad": data.get("rewritten_ad", ""), "word_list_hits": len(lex)}


def build_rubric(ad: str, run_id: str = "") -> list[dict]:
    reply = llm.chat(RUBRIC_PROMPT.format(ad=ad), model=llm.SCORER_MODEL, component="rubric.build",
                     prompt_version=RUBRIC_VERSION, temperature=0.1, max_tokens=900, run_id=run_id, subject="job_ad")
    data = llm.parse_json(reply) or {}
    crit = [c for c in data.get("criteria", []) if c.get("name")]
    if not crit:
        raise RuntimeError("The model did not return a rubric. Please try again.")
    total = sum(float(c.get("weight", 0) or 0) for c in crit) or 1
    for c in crit:  # normalise weights to 100
        c["weight"] = round(100 * float(c.get("weight", 0) or 0) / total)
    return crit
