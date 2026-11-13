"""Decision Trace: the "flight recorder" for AI hiring decisions.

Every model call (and every human approval) becomes one record. Records can be exported as JSONL
so an auditor, a regulator or a rejected candidate's complaint can be checked later.
"""

from __future__ import annotations

import json
import threading
import time
import uuid

_lock = threading.Lock()
_RECORDS: list[dict] = []


def new_run_id(prefix: str) -> str:
    return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"


def record(rec: dict) -> dict:
    rec = {"id": uuid.uuid4().hex[:8], "time": time.strftime("%Y-%m-%d %H:%M:%S"), **rec}
    with _lock:
        _RECORDS.append(rec)
    return rec


def records(run_id: str | None = None, subject: str | None = None) -> list[dict]:
    with _lock:
        out = list(_RECORDS)
    if run_id:
        out = [r for r in out if r.get("run_id") == run_id]
    if subject:
        out = [r for r in out if r.get("subject") == subject]
    return out


def load(recs: list[dict]):
    """Put saved records (from the replay cache) back into the recorder."""
    with _lock:
        known = {r["id"] for r in _RECORDS}
        _RECORDS.extend(r for r in recs if r.get("id") not in known)


def to_jsonl(recs: list[dict]) -> str:
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n"


def summary(recs: list[dict]) -> dict:
    calls = [r for r in recs if r.get("model")]
    return {
        "calls": len(calls),
        "tokens": sum(r.get("tokens_in", 0) + r.get("tokens_out", 0) for r in calls),
        "cost_usd": round(sum(r.get("cost_usd", 0) for r in calls), 4),
        "seconds": round(sum(r.get("latency_s", 0) for r in calls), 1),
    }
