"""
lab_parser_service.py — Structured Lab Input Parser & Normalizer

Parses raw lab input dictionaries, text snippets, or JSON structures into a normalized dictionary of numeric analytes.
"""

from __future__ import annotations
import re
from typing import Any, Dict


def parse_lab_values(raw_input: Dict[str, Any] | str | None) -> Dict[str, float]:
    """
    Parses and normalizes raw lab input values into a clean dict of float values keyed by analyte name.
    """
    if not raw_input:
        return {}

    parsed: Dict[str, float] = {}

    if isinstance(raw_input, dict):
        for k, v in raw_input.items():
            val = _extract_float(v)
            if val is not None:
                parsed[k.lower().strip()] = val
        return parsed

    if isinstance(raw_input, str):
        # Line-by-line parsing: e.g. "Troponin: 0.84 ng/mL" or "WBC = 14.5"
        for line in raw_input.splitlines():
            if ":" in line or "=" in line:
                parts = re.split(r"[:=]", line, maxsplit=1)
                k = parts[0].strip().lower()
                val = _extract_float(parts[1])
                if val is not None:
                    parsed[k] = val

    return parsed


def _extract_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        # Match leading numeric pattern (including decimals)
        match = re.search(r"[-+]?\d*\.\d+|\d+", str(val))
        if match:
            return float(match.group(0))
    except (ValueError, TypeError):
        pass
    return None
