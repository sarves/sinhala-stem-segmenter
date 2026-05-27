# Sinhala Stem Segmenter

A ready-to-use Python library and command-line tool for Sinhala stem/rest
segmentation.

This package is designed for modern written Sinhala. It is **not** a
lemmatizer, and it does **not** delete suffixes. Instead, it segments a word
into:

```text
stem + rest == normalized_word
```

The package includes a bundled pretrained model, so most users can install it
and start segmenting Sinhala words immediately.

## Features

- Built-in pretrained Sinhala segmenter.
- Command-line interface.
- Python API.
- Unicode NFC normalization.
- Sinhala orthographic-cluster boundary handling.
- ZWJ/ZWNJ-aware Sinhala splitting.
- No required third-party runtime dependencies.

## Install

Requires Python 3.10 or newer.

Install from GitHub:

```bash
python3 -m pip install "git+https://github.com/YOUR-USER/sinhala-stem-segmenter.git"
```

For local development:

```bash
git clone https://github.com/YOUR-USER/sinhala-stem-segmenter.git
cd sinhala-stem-segmenter
python3 -m pip install -e .
```

Replace `YOUR-USER` with your GitHub username or organization.

## Command-Line Usage

Segment Sinhala words using the bundled model:

```bash
echo "ජනාධිපතිවරයාය ආණ්ඩුවට කරනවා" | sinhala-segment segment
```

Output:

```text
ජනාධිපතිවරයාය    ජනාධිපතිවරයා    ය    1.000
ආණ්ඩුවට          ආණ්ඩුව          ට    1.000
කරනවා            කරන            වා   1.000
```

JSON output:

```bash
echo "ජනාධිපතිවරයාය" | sinhala-segment segment --json
```

Tokenize Sinhala text from stdin before segmenting:

```bash
cat article.txt | sinhala-segment segment --tokens --json
```

Use a custom model file:

```bash
echo "ජනාධිපතිවරයාය" | sinhala-segment segment -m my-model.json.gz
```

## Python Usage

Load the bundled model:

```python
from sinhala_stem_segmenter import SinhalaStemSegmenter

segmenter = SinhalaStemSegmenter.load_default()
result = segmenter.segment("ජනාධිපතිවරයාය")

print(result.stem)
print(result.rest)
print(result.stem + result.rest == result.normalized)
```

Output:

```text
ජනාධිපතිවරයා
ය
True
```

Convert a result to a dictionary:

```python
result.to_dict()
```

Example dictionary:

```python
{
    "word": "ජනාධිපතිවරයාය",
    "normalized": "ජනාධිපතිවරයාය",
    "stem": "ජනාධිපතිවරයා",
    "rest": "ය",
    "boundary": 12,
    "stem_clusters": 8,
    "rest_clusters": 1,
    "confidence": 1.0,
    "score": 42.895175,
    "family_size": 76,
    "family_tokens": 22839,
    "rest_frequency": 7212294,
    "split": True,
}
```

## Train A Custom Model

You can train a model from any UTF-8 Sinhala plain-text corpus:

```bash
sinhala-segment train corpus.txt -o my-model.json.gz
```

Then use it:

```bash
echo "ආණ්ඩුවට" | sinhala-segment segment -m my-model.json.gz
```

Training from Python:

```python
from sinhala_stem_segmenter import SinhalaStemSegmenter

texts = [
    "දැන් මෙරට ජනාධිපතිවරයාය",
    "ජනාධිපතිවරයා අද කතා කළේය",
    "ආණ්ඩුවට සහ ආණ්ඩුවේ තීරණයට විරෝධය",
]

segmenter = SinhalaStemSegmenter()
segmenter.fit_texts(texts)
segmenter.save("my-model.json.gz")
```

## How It Works

The segmenter learns repeated left-side and right-side patterns from Sinhala
word forms. At segmentation time, it tries legal Sinhala orthographic-cluster
split points and chooses the most strongly supported split.

It never intentionally removes text:

```text
stem + rest == normalized_word
```

If the model cannot find a confident split, it returns the full word as the
stem and an empty `rest`.

## Output Fields

`segmenter.segment(word)` returns a `SegmentResult`.

Important fields:

- `word`: original input word.
- `normalized`: NFC-normalized word.
- `stem`: left segment.
- `rest`: right-side remaining segment.
- `split`: `False` means no confident split was found.
- `confidence`: model confidence from corpus evidence.
- `stem_clusters`: Sinhala orthographic clusters in the stem.
- `rest_clusters`: Sinhala orthographic clusters in the rest.

## Repository Contents

Recommended public repository contents:

```text
README.md
LICENSE
pyproject.toml
src/
tests/
.gitignore
```

The bundled model is stored at:

```text
src/sinhala_stem_segmenter/resources/default.model.json.gz
```

## Publish On GitHub

From this project directory:

```bash
git init
git add README.md LICENSE pyproject.toml src tests .gitignore
git commit -m "Initial Sinhala stem segmenter"
git branch -M main
git remote add origin https://github.com/YOUR-USER/sinhala-stem-segmenter.git
git push -u origin main
```

Because the bundled model is compressed to a GitHub-friendly size, it can live
inside the repository as a normal package resource.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Run the CLI without installing:

```bash
printf 'ජනාධිපතිවරයාය ආණ්ඩුවට කරනවා\n' \
  | PYTHONPATH=src python3 -m sinhala_stem_segmenter.cli segment --json
```

## License

MIT License.
