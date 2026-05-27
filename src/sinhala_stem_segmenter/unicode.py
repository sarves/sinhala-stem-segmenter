"""Unicode helpers for Sinhala orthographic-cluster segmentation.

The goal here is not full grapheme-cluster conformance. It is a conservative
Sinhala boundary detector for stem/rest segmentation: never split inside a
Sinhala written unit, especially around al-lakuna and ZWJ/ZWNJ sequences.
"""

from __future__ import annotations

from dataclasses import dataclass
import unicodedata

ZWJ = "\u200d"
ZWNJ = "\u200c"
AL_LAKUNA = "\u0dca"

SINHALA_START = 0x0D80
SINHALA_END = 0x0DFF

SINHALA_INDEPENDENT_VOWELS = frozenset(chr(cp) for cp in range(0x0D85, 0x0D97))
SINHALA_CONSONANTS = frozenset(chr(cp) for cp in range(0x0D9A, 0x0DC7))
SINHALA_VOWEL_SIGNS = frozenset(
    [
        "\u0dca",
        "\u0dcf",
        "\u0dd0",
        "\u0dd1",
        "\u0dd2",
        "\u0dd3",
        "\u0dd4",
        "\u0dd6",
        "\u0dd8",
        "\u0dd9",
        "\u0dda",
        "\u0ddb",
        "\u0ddc",
        "\u0ddd",
        "\u0dde",
        "\u0ddf",
    ]
)
SINHALA_SIGNS = frozenset(["\u0d82", "\u0d83"])
SINHALA_MARKS = SINHALA_VOWEL_SIGNS | SINHALA_SIGNS
JOINERS = frozenset([ZWJ, ZWNJ])


@dataclass(frozen=True)
class SinhalaCluster:
    """One conservative Sinhala orthographic cluster."""

    text: str
    start: int
    end: int


def normalize_sinhala(text: str) -> str:
    """Normalize text to NFC while preserving joiners and Sinhala content."""

    return unicodedata.normalize("NFC", text)


def is_sinhala_char(char: str) -> bool:
    """Return True when a character is in the Sinhala Unicode block."""

    return bool(char) and SINHALA_START <= ord(char) <= SINHALA_END


def is_sinhala_base(char: str) -> bool:
    """Return True for Sinhala letters that can start an orthographic unit."""

    return char in SINHALA_CONSONANTS or char in SINHALA_INDEPENDENT_VOWELS


def is_sinhala_mark(char: str) -> bool:
    """Return True for Sinhala dependent signs that attach to a base."""

    return char in SINHALA_MARKS or unicodedata.combining(char) != 0


def _should_attach_to_previous(current: str, previous: str | None, cluster: str) -> bool:
    if not cluster:
        return False

    if current in JOINERS:
        return True

    if current in SINHALA_MARKS:
        return True

    if unicodedata.combining(current) != 0:
        return True

    if is_sinhala_base(current) and previous in JOINERS:
        return True

    if is_sinhala_base(current) and previous == AL_LAKUNA:
        return True

    if is_sinhala_base(current) and cluster.endswith(AL_LAKUNA + ZWJ):
        return True

    if is_sinhala_base(current) and cluster.endswith(AL_LAKUNA + ZWNJ):
        return True

    return False


def iter_sinhala_clusters(text: str) -> list[SinhalaCluster]:
    """Split text into conservative orthographic clusters.

    This function returns clusters for all characters, not only Sinhala. Sinhala
    clusters keep dependent marks and joiner-mediated forms together. Non-Sinhala
    combining marks attach to their previous character.
    """

    normalized = normalize_sinhala(text)
    clusters: list[SinhalaCluster] = []
    current = ""
    start = 0
    previous: str | None = None

    for index, char in enumerate(normalized):
        if not current:
            current = char
            start = index
            previous = char
            continue

        if _should_attach_to_previous(char, previous, current):
            current += char
        else:
            clusters.append(SinhalaCluster(current, start, index))
            current = char
            start = index

        previous = char

    if current:
        clusters.append(SinhalaCluster(current, start, len(normalized)))

    return clusters


def split_sinhala_clusters(text: str) -> list[str]:
    """Return only cluster strings."""

    return [cluster.text for cluster in iter_sinhala_clusters(text)]


def legal_split_offsets(text: str) -> list[int]:
    """Return string offsets where stem/rest splits are cluster-safe."""

    return [cluster.end for cluster in iter_sinhala_clusters(text)[:-1]]
