#!/usr/bin/env python3
"""Validate the segmenter on a bounded CultureX Sinhala sample.

This is an unsupervised validation because the dataset has raw text only, not
gold stem/rest labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import ssl
import statistics
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sinhala_stem_segmenter import SinhalaStemSegmenter, split_sinhala_clusters
from sinhala_stem_segmenter.tokenize import iter_sinhala_words

DATASET = "Minuri/sinhala-corpus-culturax"
CONFIG = "default"
SPLIT = "train"
ROWS_URL = "https://datasets-server.huggingface.co/rows"


def fetch_rows_page(offset: int, length: int, *, context: ssl.SSLContext | None) -> list[str]:
    query = urllib.parse.urlencode(
        {
            "dataset": DATASET,
            "config": CONFIG,
            "split": SPLIT,
            "offset": offset,
            "length": length,
        }
    )
    with urllib.request.urlopen(f"{ROWS_URL}?{query}", timeout=60, context=context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [row["row"]["text"] for row in payload["rows"]]


def fetch_rows(offset: int, length: int, *, context: ssl.SSLContext | None) -> list[str]:
    rows: list[str] = []
    page_offset = offset
    remaining = length
    while remaining > 0:
        page_length = min(remaining, 100)
        page = fetch_rows_page(page_offset, page_length, context=context)
        if not page:
            break
        rows.extend(page)
        fetched = len(page)
        page_offset += fetched
        remaining -= fetched
        if fetched < page_length:
            break
    return rows


def evaluate_results(
    model: SinhalaStemSegmenter,
    test_texts: list[str],
    *,
    examples: int,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    test_words: list[str] = []
    for text in test_texts:
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
        "note": "Unsupervised corpus validation; not gold linguistic accuracy.",
    }

    example_rows: list[dict[str, object]] = []
    if examples:
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
        seen_stems = set()
        for result in ranked_examples:
            if result.stem in seen_stems:
                continue
            example_rows.append(result.to_dict())
            seen_stems.add(result.stem)
            if len(example_rows) >= examples:
                break

    return metrics, example_rows


def train_and_validate(args: argparse.Namespace) -> dict[str, object]:
    context = ssl._create_unverified_context() if args.allow_insecure_ssl else None
    test_texts = fetch_rows(args.test_offset, args.test_rows, context=context)

    if args.model_in:
        model = SinhalaStemSegmenter.load(args.model_in)
        train_rows = None
    else:
        train_texts = fetch_rows(args.train_offset, args.train_rows, context=context)
        model = SinhalaStemSegmenter(
            min_stem_clusters=args.min_stem_clusters,
            min_rest_clusters=args.min_rest_clusters,
            min_family_size=args.min_family_size,
            min_rest_frequency=args.min_rest_frequency,
            min_score=args.min_score,
        )
        model.fit_texts(train_texts)
        train_rows = args.train_rows

    metrics, example_rows = evaluate_results(model, test_texts, examples=args.examples)
    metrics.update(
        {
        "dataset": DATASET,
        "train_rows": train_rows,
        "test_rows": args.test_rows,
        "train_tokens": model.total_tokens,
        "train_word_types": len(model.word_counts),
        "model_in": args.model_in,
    })

    if args.model_out:
        model.save(args.model_out)
        metrics["model_out"] = args.model_out

    if args.metrics_out:
        Path(args.metrics_out).write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    if example_rows:
        metrics["examples"] = example_rows

    return metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-rows", type=int, default=1000)
    parser.add_argument("--test-rows", type=int, default=200)
    parser.add_argument("--train-offset", type=int, default=0)
    parser.add_argument("--test-offset", type=int, default=1000)
    parser.add_argument("--min-stem-clusters", type=int, default=2)
    parser.add_argument("--min-rest-clusters", type=int, default=1)
    parser.add_argument("--min-family-size", type=int, default=3)
    parser.add_argument("--min-rest-frequency", type=int, default=2)
    parser.add_argument("--min-score", type=float, default=4.0)
    parser.add_argument("--model-out")
    parser.add_argument("--model-in")
    parser.add_argument("--metrics-out")
    parser.add_argument("--examples", type=int, default=10)
    parser.add_argument(
        "--allow-insecure-ssl",
        action="store_true",
        help="Disable TLS certificate verification for environments with broken local CA setup.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    metrics = train_and_validate(args)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
