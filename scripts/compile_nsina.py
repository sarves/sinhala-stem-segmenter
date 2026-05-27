#!/usr/bin/env python3
"""Compile NSINA article JSON files into plain-text corpora."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sinhala_stem_segmenter.tokenize import iter_sinhala_words

WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return WHITESPACE_RE.sub(" ", value).strip()


def article_text(payload: dict[str, object]) -> str:
    fields = [
        clean_text(payload.get("Headline")),
        clean_text(payload.get("News Content")),
    ]
    return " ".join(field for field in fields if field)


def source_from_path(path: Path, data_dir: Path) -> str:
    relative = path.relative_to(data_dir)
    return relative.parts[0] if relative.parts else "unknown"


def compile_nsina(args: argparse.Namespace) -> dict[str, object]:
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_path = output_dir / "nsina_news.txt"
    train_path = output_dir / "nsina_train.txt"
    test_path = output_dir / "nsina_test.txt"
    manifest_path = output_dir / "manifest.jsonl"
    metadata_path = output_dir / "metadata.json"

    files = sorted(data_dir.rglob("*.json"))
    source_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    skipped = 0
    article_count = 0
    train_count = 0
    test_count = 0
    token_count = 0
    train_tokens = 0
    test_tokens = 0

    with (
        all_path.open("w", encoding="utf-8") as all_out,
        train_path.open("w", encoding="utf-8") as train_out,
        test_path.open("w", encoding="utf-8") as test_out,
        manifest_path.open("w", encoding="utf-8") as manifest_out,
    ):
        for index, file_path in enumerate(files):
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                skipped += 1
                continue

            if not isinstance(payload, dict):
                skipped += 1
                continue

            text = article_text(payload)
            if not text:
                skipped += 1
                continue

            tokens = iter_sinhala_words(text)
            if len(tokens) < args.min_tokens:
                skipped += 1
                continue

            source = clean_text(payload.get("Source")) or source_from_path(file_path, data_dir)
            category = clean_text(payload.get("Category")) or "unknown"
            source_counts[source] += 1
            category_counts[category] += 1

            all_out.write(text + "\n")
            is_test = index % args.test_modulo == 0
            if is_test:
                test_out.write(text + "\n")
                test_count += 1
                test_tokens += len(tokens)
            else:
                train_out.write(text + "\n")
                train_count += 1
                train_tokens += len(tokens)

            article_count += 1
            token_count += len(tokens)
            manifest_out.write(
                json.dumps(
                    {
                        "path": str(file_path.relative_to(data_dir)),
                        "source": source,
                        "category": category,
                        "split": "test" if is_test else "train",
                        "tokens": len(tokens),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    metadata: dict[str, object] = {
        "data_dir": str(data_dir),
        "output_dir": str(output_dir),
        "json_files": len(files),
        "articles": article_count,
        "skipped": skipped,
        "train_articles": train_count,
        "test_articles": test_count,
        "tokens": token_count,
        "train_tokens": train_tokens,
        "test_tokens": test_tokens,
        "test_modulo": args.test_modulo,
        "min_tokens": args.min_tokens,
        "source_counts": dict(source_counts.most_common()),
        "top_categories": dict(category_counts.most_common(50)),
        "outputs": {
            "all": str(all_path),
            "train": str(train_path),
            "test": str(test_path),
            "manifest": str(manifest_path),
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        default="data/nsina/NSINA-main/data",
        help="Extracted NSINA data directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/nsina_compiled",
        help="Output directory for compiled corpora.",
    )
    parser.add_argument(
        "--test-modulo",
        type=int,
        default=10,
        help="Deterministic holdout: every Nth article goes to test.",
    )
    parser.add_argument("--min-tokens", type=int, default=3)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    metadata = compile_nsina(args)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
