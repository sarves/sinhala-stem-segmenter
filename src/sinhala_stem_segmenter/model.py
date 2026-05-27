"""Data-driven Sinhala stem/rest segmenter."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Iterable

from .tokenize import iter_sinhala_words
from .unicode import normalize_sinhala, split_sinhala_clusters


@dataclass(frozen=True)
class SegmentResult:
    """A stem/rest segmentation result."""

    word: str
    normalized: str
    stem: str
    rest: str
    boundary: int
    stem_clusters: int
    rest_clusters: int
    confidence: float
    score: float
    family_size: int
    family_tokens: int
    rest_frequency: int
    split: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class SinhalaStemSegmenter:
    """Unsupervised Sinhala-aware stem/rest segmenter.

    The model learns from repeated left segments and right-side continuations in
    a corpus. It preserves text: result.stem + result.rest == result.normalized.
    """

    def __init__(
        self,
        *,
        min_stem_clusters: int = 2,
        min_rest_clusters: int = 1,
        min_family_size: int = 3,
        min_rest_frequency: int = 2,
        min_score: float = 4.0,
    ) -> None:
        self.min_stem_clusters = min_stem_clusters
        self.min_rest_clusters = min_rest_clusters
        self.min_family_size = min_family_size
        self.min_rest_frequency = min_rest_frequency
        self.min_score = min_score
        self.word_counts: Counter[str] = Counter()
        self.prefix_rests: dict[str, Counter[str]] = defaultdict(Counter)
        self.rest_counts: Counter[str] = Counter()
        self.total_tokens = 0

    def fit_texts(self, texts: Iterable[str]) -> "SinhalaStemSegmenter":
        """Train from raw text strings."""

        counts: Counter[str] = Counter()
        for text in texts:
            for word in iter_sinhala_words(text):
                counts[normalize_sinhala(word)] += 1

        for word, count in counts.items():
            self.add_word(word, count)
        return self

    def add_word(self, word: str, count: int = 1) -> None:
        """Add a word type/token count to the model."""

        normalized = normalize_sinhala(word)
        clusters = split_sinhala_clusters(normalized)
        if len(clusters) < self.min_stem_clusters + self.min_rest_clusters:
            return

        self.word_counts[normalized] += count
        self.total_tokens += count

        for index in range(self.min_stem_clusters, len(clusters) - self.min_rest_clusters + 1):
            stem = "".join(clusters[:index])
            rest = "".join(clusters[index:])
            self.prefix_rests[stem][rest] += count
            self.rest_counts[rest] += count

    def segment(self, word: str) -> SegmentResult:
        """Return the best stem/rest split for a word."""

        normalized = normalize_sinhala(word)
        clusters = split_sinhala_clusters(normalized)
        if len(clusters) < self.min_stem_clusters + self.min_rest_clusters:
            return self._no_split(word, normalized, clusters)

        best: tuple[float, int, str, str, int, int, int] | None = None
        for index in range(self.min_stem_clusters, len(clusters) - self.min_rest_clusters + 1):
            stem = "".join(clusters[:index])
            rest = "".join(clusters[index:])
            family = self.prefix_rests.get(stem)
            if not family:
                continue

            family_size = len(family)
            family_tokens = sum(family.values())
            rest_frequency = self.rest_counts.get(rest, 0)
            if family_size < self.min_family_size and rest_frequency < self.min_rest_frequency:
                continue

            score = self._score_candidate(
                stem_clusters=index,
                rest_clusters=len(clusters) - index,
                family_size=family_size,
                family_tokens=family_tokens,
                rest_frequency=rest_frequency,
                stem_as_word_frequency=self.word_counts.get(stem, 0),
            )
            if best is None or score > best[0]:
                best = (score, index, stem, rest, family_size, family_tokens, rest_frequency)

        if best is None or best[0] < self.min_score:
            return self._no_split(word, normalized, clusters)

        score, index, stem, rest, family_size, family_tokens, rest_frequency = best
        confidence = 1.0 / (1.0 + math.exp(-(score - self.min_score)))
        boundary = len(stem)
        return SegmentResult(
            word=word,
            normalized=normalized,
            stem=stem,
            rest=rest,
            boundary=boundary,
            stem_clusters=index,
            rest_clusters=len(clusters) - index,
            confidence=round(confidence, 6),
            score=round(score, 6),
            family_size=family_size,
            family_tokens=family_tokens,
            rest_frequency=rest_frequency,
            split=True,
        )

    def _score_candidate(
        self,
        *,
        stem_clusters: int,
        rest_clusters: int,
        family_size: int,
        family_tokens: int,
        rest_frequency: int,
        stem_as_word_frequency: int,
    ) -> float:
        family_signal = 2.2 * math.log1p(family_size)
        token_signal = 0.65 * math.log1p(family_tokens)
        rest_signal = 1.15 * math.log1p(rest_frequency)
        stem_word_signal = 0.7 * math.log1p(stem_as_word_frequency)
        stem_length_signal = 0.12 * stem_clusters
        long_rest_penalty = 0.45 * max(0, rest_clusters - 4)
        tiny_stem_penalty = 0.7 if stem_clusters <= self.min_stem_clusters else 0.0
        return (
            family_signal
            + token_signal
            + rest_signal
            + stem_word_signal
            + stem_length_signal
            - long_rest_penalty
            - tiny_stem_penalty
        )

    def _no_split(self, word: str, normalized: str, clusters: list[str]) -> SegmentResult:
        return SegmentResult(
            word=word,
            normalized=normalized,
            stem=normalized,
            rest="",
            boundary=len(normalized),
            stem_clusters=len(clusters),
            rest_clusters=0,
            confidence=1.0,
            score=0.0,
            family_size=0,
            family_tokens=0,
            rest_frequency=0,
            split=False,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize model state."""

        return {
            "version": 1,
            "params": {
                "min_stem_clusters": self.min_stem_clusters,
                "min_rest_clusters": self.min_rest_clusters,
                "min_family_size": self.min_family_size,
                "min_rest_frequency": self.min_rest_frequency,
                "min_score": self.min_score,
            },
            "word_counts": dict(self.word_counts),
            "prefix_rests": {
                prefix: dict(rests) for prefix, rests in self.prefix_rests.items()
            },
            "rest_counts": dict(self.rest_counts),
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SinhalaStemSegmenter":
        params = data.get("params", {})
        if not isinstance(params, dict):
            params = {}

        model = cls(**params)
        model.word_counts = Counter(data.get("word_counts", {}))

        prefix_rests: dict[str, Counter[str]] = defaultdict(Counter)
        raw_prefix_rests = data.get("prefix_rests", {})
        if isinstance(raw_prefix_rests, dict):
            for prefix, rests in raw_prefix_rests.items():
                if isinstance(rests, dict):
                    prefix_rests[str(prefix)] = Counter(rests)
        model.prefix_rests = prefix_rests
        model.rest_counts = Counter(data.get("rest_counts", {}))
        model.total_tokens = int(data.get("total_tokens", 0))
        return model

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "SinhalaStemSegmenter":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)
