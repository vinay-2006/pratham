"""PRATHAM Copilot — Groq LLM client (JSON mode, model fallback, bounded latency)."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]


class LLMUnavailable(Exception):
    pass


def _models() -> List[str]:
    configured = os.getenv("GROQ_MODEL", "").strip()
    chain = ([configured] if configured else []) + DEFAULT_MODELS
    seen, out = set(), []
    for m in chain:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _parse_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def chat_json(messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 2500) -> Dict[str, Any]:
    """Call Groq, forcing a JSON-object reply. Tries each configured model in turn."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise LLMUnavailable("GROQ_API_KEY is not configured")
    from groq import Groq

    client = Groq(api_key=key, timeout=45.0, max_retries=1)
    last: Optional[Exception] = None
    for model in _models():
        try:
            res = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            data = _parse_json(res.choices[0].message.content)
            data["_model"] = model
            return data
        except Exception as exc:  # model missing, rate limit, bad JSON … try the next one
            logger.warning("Groq model %s failed: %s", model, exc)
            last = exc
    raise LLMUnavailable(str(last))
