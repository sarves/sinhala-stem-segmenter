#!/usr/bin/env python3
"""Train and evaluate the segmenter on local train/test text files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sinhala_stem_segmenter import SinhalaStemSegmenter, split_sinhala_clusters
from sinhala_stem_segmenter.tokenize import iter_sinhala_words


def iter_lines(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            yield line


def evaluate_model(model: SinhalaStemSegmenter, texts) -> tuple[dict[str, object], list[dict[str, object]]]:
    test_words: list[str] = []
    for text in texts:
        test_words.extend(iter_sinhala_words(text))

    results = [model.segment(word) for word in test_words]
    split_results = [result for result in results if result.split]

    reconstruction_ok = sum(
        1 for result in results if result.stem + result.rest == result.normalized
    )
    valid_boundary_ok = sum(
        1
        for result in results
        if split_sinhala_clusters(result.stem) + split_sinhala_clusters(result.rest)
        == split_sinhala_clusters(result.normalized)
    )
    family_supported = sum(
        1 for result in split_results if result.family_size >= model.min_family_size
    )

    avg_confidence = (
        statistics.fmean(result.confidence for result in split_results)
        if split_results
        else 0.0
    )
    avg_rest_clusters = (
        statistics.fmean(result.rest_clusters for result in split_results)
        if split_results
        else 0.0
    )

    unique_examples = {}
    for result in split_results:
        existing = unique_examples.get(result.normalized)
        if existing is None or result.score > existing.score:
            unique_examples[result.normalized] = result
    ranked_examples = sorted(
        unique_examples.values(),
        key=lambda item: (item.confidence, item.family_size, item.rest_frequency),
        reverse=True,
    )
    diverse_examples = []
    seen_stems = set()
    for result in ranked_examples:
        if result.stem in seen_stems:
            continue
        diverse_examples.append(result.to_dict())
        seen_stems.add(result.stem)
        if len(diverse_examples) >= 12:
            break

    metrics: dict[str, object] = {
        "test_tokens": len(test_words),
        "reconstruction_accuracy": round(reconstruction_ok / len(results), 6)
        if results
        else 0.0,
        "valid_boundary_accuracy": round(valid_boundary_ok / len(results), 6)
        if results
        else 0.0,
        "split_coverage": round(len(split_results) / len(results), 6) if results else 0.0,
        "family_supported_split_rate": round(family_supported / len(split_results), 6)
        if split_results
        else 0.0,
        "average_split_confidence": round(avg_confidence, 6),
        "average_rest_clusters": round(avg_rest_clusters, 6),
        "note": "Unsupervised local-corpus validation; not gold linguistic accuracy.",
    }
    return metrics, diverse_examples


def train_and_validate(args: argparse.Namespace) -> dict[str, object]:
    model = SinhalaStemSegmenter(
        min_stem_clusters=args.min_stem_clusters,
        min_rest_clusters=args.min_rest_clusters,
        min_family_size=args.min_family_size,
        min_rest_frequency=args.min_rest_frequency,
        min_score=args.min_score,
    )
    model.fit_texts(iter_lines(args.train))

    metrics, examples = evaluate_model(model, iter_lines(args.test))
    metrics.update(
        {
            "train": args.train,
            "test": args.test,
            "train_tokens": model.total_tokens,
            "train_word_types": len(model.word_counts),
            "prefixes": len(model.prefix_rests),
            "rests": len(model.rest_counts),
            "model_out": args.model_out,
            "examples": examples,
        }
    )

    if args.model_out:
        model.save(args.model_out)

    if args.metrics_out:
        Path(args.metrics_out).write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    return metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True)
    parser.add_argument("--test", required=True)
    parser.add_argument("--model-out")
    parser.add_argument("--metrics-out")
    parser.add_argument("--min-stem-clusters", type=int, default=2)
    parser.add_argument("--min-rest-clusters", type=int, default=1)
    parser.add_argument("--min-family-size", type=int, default=3)
    parser.add_argument("--min-rest-frequency", type=int, default=2)
    parser.add_argument("--min-score", type=float, default=4.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    metrics = train_and_validate(args)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
