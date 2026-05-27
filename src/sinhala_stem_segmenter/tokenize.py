"""Text tokenization helpers for Sinhala segmentation experiments."""

from __future__ import annotations

import re

from .unicode import is_sinhala_char, normalize_sinhala

TOKEN_RE = re.compile(
    r"[\u0d80-\u0dff\u200c\u200d]+",
    flags=re.UNICODE,
)


def iter_sinhala_words(text: str, *, min_chars: int = 2) -> list[str]:
    """Extract Sinhala-script word tokens from text."""

    normalized = normalize_sinhala(text)
    words: list[str] = []
    for match in TOKEN_RE.finditer(normalized):
        token = match.group(0)
        if sum(1 for char in token if is_sinhala_char(char)) >= min_chars:
            words.append(token)
    return words
