"""One place for every call to a large language model.

All models are called through Hugging Face Inference Providers (needs the HF_TOKEN secret).
Every call is written to the Decision Trace (see trace.py): model, temperature, prompt version,
input hash, raw output, tokens, time and estimated cost.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time

from . import trace

# Model roles. Prices are US$ per 1M tokens (input, output), read from the Hugging Face router
# model list on 2026-11-13 (provider: deepinfra / novita). They are estimates for the cost column only.
MODELS = {
    "Qwen/Qwen2.5-72B-Instruct": {"short": "Qwen2.5-72B", "price": (0.36, 0.40)},
    "Qwen/Qwen3-235B-A22B-Instruct-2507": {"short": "Qwen3-235B", "price": (0.09, 0.55)},
    "meta-llama/Llama-3.3-70B-Instruct": {"short": "Llama-3.3-70B", "price": (0.135, 0.40)},
    "meta-llama/Llama-3.1-8B-Instruct": {"short": "Llama-3.1-8B", "price": (0.02, 0.05)},
}

NAIVE_MODEL = os.environ.get("NAIVE_MODEL", "Qwen/Qwen2.5-72B-Instruct")       # the "vendor tool" (old demo)
SCORER_MODEL = os.environ.get("SCORER_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507")  # FairTrace scorer + agent
REDACT_MODEL = os.environ.get("REDACT_MODEL", "meta-llama/Llama-3.3-70B-Instruct")   # finds sensitive details


def short(model: str) -> str:
    return MODELS.get(model, {}).get("short", model.split("/")[-1])


def cost_usd(model: str, tok_in: int, tok_out: int) -> float:
    p_in, p_out = MODELS.get(model, {}).get("price", (0.5, 0.5))
    return (tok_in * p_in + tok_out * p_out) / 1_000_000


def sha(text: str, n: int = 10) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:n]


def available() -> bool:
    return bool(os.environ.get("HF_TOKEN"))


def _client():
    from huggingface_hub import InferenceClient

    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("No HF_TOKEN found. Add a Hugging Face token as a Space secret named HF_TOKEN.")
    return InferenceClient(token=token, timeout=90)


def chat(prompt: str, *, model: str, component: str, prompt_version: str, temperature: float = 0.2,
         max_tokens: int = 400, subject: str = "", run_id: str = "", system: str | None = None) -> str:
    """Call the model once, record the call in the trace and return the text reply."""
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    last_err = None
    for attempt in range(3):
        t0 = time.time()
        try:
            resp = _client().chat_completion(model=model, messages=messages,
                                             max_tokens=max_tokens, temperature=temperature)
            text = (resp.choices[0].message.content or "").strip()
            usage = getattr(resp, "usage", None)
            tok_in = int(getattr(usage, "prompt_tokens", 0) or 0)
            tok_out = int(getattr(usage, "completion_tokens", 0) or 0)
            trace.record({
                "run_id": run_id, "component": component, "subject": subject,
                "model": model, "temperature": temperature, "prompt_version": prompt_version,
                "input_hash": sha(prompt), "raw_output": text[:2000],
                "tokens_in": tok_in, "tokens_out": tok_out,
                "cost_usd": round(cost_usd(model, tok_in, tok_out), 6),
                "latency_s": round(time.time() - t0, 2),
            })
            return text
        except Exception as e:  # network / provider hiccup: retry with backoff
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"The model {short(model)} did not answer: {last_err}")


def parse_json(text: str):
    """Pull the first JSON object or array out of a model reply (tolerates ```json fences)."""
    text = re.sub(r"```(?:json)?", "", text)
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = text.find(open_c)
        end = text.rfind(close_c)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    return None
