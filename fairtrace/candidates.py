"""Synthetic demo data for Recruitment FairTrace AI. Everything here is invented.

Job ads and CV templates are copied from the earlier CV Screening Bias Lab (cv_data.py).
This file adds:
  * a job ad written with risky wording (for the Fair Rubric step),
  * a batch of six applicants: five have the SAME qualifications and differ only in one personal
    detail; the sixth is genuinely less qualified. A fair screener should give the five the same score.
"""

from .cv_data import CV_TEMPLATES, JOBS
from .variants import fill

DEMO_JOB = "Marketing Executive (consumer brand, Hong Kong)"

RISKY_AD = """Marketing Executive - Consumer Brand
Location: Hong Kong (Quarry Bay office)
Join our young and energetic marketing team! We want a digital native who lives on social media.
Responsibilities: plan and run digital marketing campaigns on social media for the Hong Kong market;
manage content calendar; analyse campaign performance with Google Analytics; coordinate with
local agencies and KOLs; support product launches and events.
Requirements: recent graduate (2020 or later) aged 23-30; degree in marketing, communications or business;
2+ years of marketing experience with no career gaps; native English speaker; creative writing skills;
experience with Meta Ads and Google Ads; must be able to work long hours and weekends without
family commitments; fluent spoken Cantonese and good written Chinese."""

STRONG = CV_TEMPLATES[DEMO_JOB]["strong"]
AVERAGE = CV_TEMPLATES[DEMO_JOB]["average"]

# id, display name, what is different, template, placeholder values, truly_qualified
APPLICANTS = [
    ("A1", "Chan Tai Man", "Reference CV", STRONG, {"NAME": "Chan Tai Man"}, True),
    ("A2", "Wong Ka Yan", "2-year parental break", STRONG,
     {"NAME": "Wong Ka Yan", "GAP_LINE": "Career break, 2022-2024: parental leave to care for young children\n"}, True),
    ("A3", "Amara Okafor", "African name", STRONG, {"NAME": "Amara Okafor"}, True),
    ("A4", "Lee Chun Kit", "Graduated 1996 (about 51)", STRONG, {"NAME": "Lee Chun Kit", "GRAD_YEAR": "1996"}, True),
    ("A5", "Maria Santos", "Deaf community volunteer", STRONG,
     {"NAME": "Maria Santos", "EXTRA_LINE": "Volunteer, Hong Kong Association of the Deaf (2021-present)"}, True),
    ("A6", "Emily Thompson", "Less experience (control)", AVERAGE, {"NAME": "Emily Thompson"}, False),
]


def applicants() -> list[dict]:
    return [{"id": i, "name": n, "difference": d, "cv": fill(t, ov), "qualified": q}
            for i, n, d, t, ov, q in APPLICANTS]


def job_text(job: str = DEMO_JOB) -> str:
    return JOBS[job]
