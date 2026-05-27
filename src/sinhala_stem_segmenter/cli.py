"""Command-line interface for Sinhala stem/rest segmentation."""

from __future__ import annotations

import argparse
import json
import sys

from .model import SinhalaStemSegmenter
from .tokenize import iter_sinhala_words


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sinhala-segment")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train", help="Train a segmenter from UTF-8 text files.")
    train.add_argument("files", nargs="+", help="Plain UTF-8 text files.")
    train.add_argument("-o", "--output", required=True, help="Output model JSON path.")
    train.add_argument("--min-stem-clusters", type=int, default=2)
    train.add_argument("--min-rest-clusters", type=int, default=1)
    train.add_argument("--min-family-size", type=int, default=3)
    train.add_argument("--min-rest-frequency", type=int, default=2)
    train.add_argument("--min-score", type=float, default=4.0)

    segment = subparsers.add_parser("segment", help="Segment stdin text or words.")
    segment.add_argument("-m", "--model", required=True, help="Model JSON path.")
    segment.add_argument("--json", action="store_true", help="Emit JSON lines.")
    segment.add_argument("--tokens", action="store_true", help="Tokenize stdin as text.")

    return parser


def train_command(args: argparse.Namespace) -> int:
    model = SinhalaStemSegmenter(
        min_stem_clusters=args.min_stem_clusters,
        min_rest_clusters=args.min_rest_clusters,
        min_family_size=args.min_family_size,
        min_rest_frequency=args.min_rest_frequency,
        min_score=args.min_score,
    )
    for file_path in args.files:
        with open(file_path, "r", encoding="utf-8") as handle:
            model.fit_texts(handle)
    model.save(args.output)
    print(
        json.dumps(
            {
                "output": args.output,
                "word_types": len(model.word_counts),
                "tokens": model.total_tokens,
                "prefixes": len(model.prefix_rests),
                "rests": len(model.rest_counts),
            },
            ensure_ascii=False,
        )
    )
    return 0


def segment_command(args: argparse.Namespace) -> int:
    model = SinhalaStemSegmenter.load(args.model)
    raw_text = sys.stdin.read()
    words = iter_sinhala_words(raw_text) if args.tokens else raw_text.split()
    for word in words:
        result = model.segment(word)
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False))
        else:
            print(f"{result.word}\t{result.stem}\t{result.rest}\t{result.confidence:.3f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "train":
        return train_command(args)
    if args.command == "segment":
        return segment_command(args)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
