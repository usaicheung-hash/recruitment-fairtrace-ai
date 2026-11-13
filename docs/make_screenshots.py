"""Take the screenshots used in README.md and the user guides (docs/img/).

    pip install playwright
    python docs/make_screenshots.py [URL]     # default: the public Space

Uses an installed Microsoft Edge (channel="msedge"); change CHANNEL for Chrome.
"""

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://edwardwww-recruitment-fairtrace-ai.hf.space/"
OUT = Path(__file__).parent / "img"
OUT.mkdir(exist_ok=True)
CHANNEL = "msedge"


def ft_block(page, text):
    """The rendered HTML block (div.ft) that contains `text`."""
    return page.locator("div.ft", has_text=text).last


def card(page, text):
    return page.locator("div.ft .card", has_text=text).last


def shot(loc, name, pad=0):
    loc.scroll_into_view_if_needed()
    time.sleep(1.2)  # let the CSS animations finish
    loc.screenshot(path=str(OUT / name))
    print("saved", name)


with sync_playwright() as p:
    browser = p.chromium.launch(channel=CHANNEL, headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    page.goto(URL, wait_until="load")
    page.get_by_text("Risky phrases found").first.wait_for(timeout=60000)
    time.sleep(3)

    def tab(name):
        page.get_by_role("tab", name=name).first.click()
        time.sleep(1.5)

    # header + tabs
    page.screenshot(path=str(OUT / "00_header.png"), clip={"x": 0, "y": 0, "width": 1280, "height": 330})
    print("saved 00_header.png")

    # owner controls
    page.get_by_text("Owner controls").first.click()
    time.sleep(1)
    page.screenshot(path=str(OUT / "15_owner_controls.png"), clip={"x": 0, "y": 190, "width": 1280, "height": 190})
    page.get_by_text("Owner controls").first.click()
    print("saved 15_owner_controls.png")

    # ① Fair Rubric
    tab("Fair Rubric")
    shot(ft_block(page, "Risky phrases found"), "01_rubric_review.png")
    page.get_by_role("button", name="HR accepts").click()
    time.sleep(2)
    shot(ft_block(page, "Scoring rubric: what earns points"), "02_rubric_approved.png")

    # ② Blind & Score
    tab("Blind & Score")
    shot(card(page, "where each screener puts them"), "03_score_spread.png")
    blk = ft_block(page, "where each screener puts them")
    shot(blk.locator("div.row").first, "03b_score_kpis.png")
    shot(card(page, "All 6 applicants"), "04_score_all.png")
    shot(ft_block(page, "What FairTrace sees").locator("div.two").first, "05_applicant_blind.png")
    shot(card(page, "every point needs a quote"), "06_applicant_evidence.png")

    # ③ Auditor
    tab("FairTrace Auditor")
    page.get_by_role("button", name="Replay saved audit").click()
    page.get_by_text("Agent timeline").first.wait_for()
    time.sleep(14)
    shot(card(page, "Agent timeline"), "07_audit_timeline.png")
    res = ft_block(page, "How the verdict is decided")
    shot(res.locator(".card").nth(1), "08_audit_attribute.png")
    page.get_by_role("button", name="Approve recommended fix").click()
    time.sleep(2)
    shot(res.locator(".banner").first, "09_audit_approved.png")

    # ④ Decision Trace
    tab("Decision Trace")
    tr = ft_block(page, "Model calls recorded")
    shot(tr.locator("div.row").first, "10_trace_kpis.png")
    shot(card(page, "Explanation for the applicant"), "11_trace_letter.png")
    calls = card(page, "Every call, in order")
    calls.locator("summary").nth(3).click()
    time.sleep(1)
    shot(calls.locator(".call").nth(3), "12_trace_call.png")

    # 📊 Model choice
    tab("Model choice")
    shot(card(page, "Unfair spread among 5 equally qualified"), "13_model_choice.png")

    # 🏁 Summary
    tab("Summary")
    sm = ft_block(page, "Same CVs, a fairer result")
    shot(sm.locator("div.row").first, "14_summary_kpis.png")
    shot(sm.locator("div.two").first, "14b_summary_charts.png")
    shot(card(page, "Naive AI vs FairTrace"), "14c_summary_scorecard.png")
    browser.close()
