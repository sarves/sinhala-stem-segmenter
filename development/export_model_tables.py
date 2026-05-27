#!/usr/bin/env python3
"""Export learned stems and rest/suffix frequencies from the bundled model."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sinhala_stem_segmenter import SinhalaStemSegmenter


def write_suffix_frequencies(model: SinhalaStemSegmenter, path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("rest_or_suffix\tfrequency\n")
        for rest, frequency in model.rest_counts.most_common():
            handle.write(f"{rest}\t{frequency}\n")


def write_stems(model: SinhalaStemSegmenter, path: Path) -> None:
    rows = []
    for stem, rests in model.prefix_rests.items():
        rows.append(
            (
                stem,
                len(rests),
                sum(rests.values()),
                model.word_counts.get(stem, 0),
            )
        )

    rows.sort(key=lambda row: (row[2], row[1], row[3], row[0]), reverse=True)

    with path.open("w", encoding="utf-8") as handle:
        handle.write("stem\tfamily_size\tfamily_tokens\tstem_as_word_frequency\n")
        for stem, family_size, family_tokens, stem_frequency in rows:
            handle.write(f"{stem}\t{family_size}\t{family_tokens}\t{stem_frequency}\n")


def main() -> int:
    output_dir = ROOT / "data"
    output_dir.mkdir(exist_ok=True)

    model = SinhalaStemSegmenter.load_default()
    write_suffix_frequencies(model, output_dir / "suffix_frequencies.tsv")
    write_stems(model, output_dir / "stems.tsv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
