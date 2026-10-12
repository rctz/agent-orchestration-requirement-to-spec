"""English-only heuristic for artifact-destined content (design §11/D11).

Talk to the user in the user's language; every output FILE is English.
This check flags non-Latin script (Thai, CJK, Korean, Arabic, etc.) in the
canonical documents — questions/notifications (user-language by design)
never pass through here.
"""
from __future__ import annotations

import re
from typing import Any

# Unicode blocks that should never appear in English artifacts. Latin
# (incl. accented characters), digits and punctuation are allowed.
_NON_LATIN_RANGES = re.compile(
    "["
    "\u0e00-\u0e7f"    # Thai
    "\u0600-\u06ff"    # Arabic
    "\u0900-\u097f"    # Devanagari
    "\u4e00-\u9fff"    # CJK unified
    "\u3040-\u30ff"    # Hiragana + Katakana
    "\uac00-\ud7af"    # Hangul
    "]"
)


def _flagged(text: str) -> list[str]:
    return sorted(set(_NON_LATIN_RANGES.findall(text)[:3]))


def english_only_violations(doc: Any, path: str = "$") -> list[str]:
    """Walk a document and report string fields containing non-Latin script."""
    violations: list[str] = []
    if isinstance(doc, dict):
        for key, value in doc.items():
            violations.extend(english_only_violations(value, f"{path}.{key}"))
    elif isinstance(doc, list):
        for index, value in enumerate(doc):
            violations.extend(english_only_violations(value, f"{path}[{index}]"))
    elif isinstance(doc, str):
        found = _flagged(doc)
        if found:
            violations.append(f"{path}: contains non-Latin script {found}")
    return violations
