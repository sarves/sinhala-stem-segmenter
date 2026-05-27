# Sinhala Stem Segmenter

A data-driven stem/rest segmenter for modern written Sinhala.

This is **not** a suffix-removal stemmer and **not** a lemmatizer. It preserves
the word by returning:

```text
stem + rest == normalized_word
```

The segmenter only splits at Sinhala orthographic-cluster boundaries. It is
designed to avoid splitting inside dependent vowel signs, al-lakuna, ZWJ/ZWNJ
sequences, and other Sinhala abugida writing units.

## What It Does

Input:

```text
ජනාධිපතිවරයාය
```

Output:

```text
stem: ජනාධිපතිවරයා
rest: ය
```

The original normalized word is still reconstructable:

```text
ජනාධිපතිවරයා + ය == ජනාධිපතිවරයාය
```

## Install

Requires Python 3.10 or newer.

Install from a local checkout:

```bash
git clone https://github.com/YOUR-USER/sinhala-stem-segmenter.git
cd sinhala-stem-segmenter
python3 -m pip install -e .
```

Install directly from GitHub:

```bash
python3 -m pip install "git+https://github.com/YOUR-USER/sinhala-stem-segmenter.git"
```

Replace `YOUR-USER` with your GitHub username or organization.

## Get A Model

You need a trained model JSON file to segment words. You have two choices.

### Option 1: Download The Pretrained NSINA News Model

The full NSINA-trained model is large, so it should be hosted as a GitHub
Release asset, Git LFS file, or Hugging Face file instead of committed directly
to the repository.

Example once you publish a release:

```bash
curl -L \
  https://github.com/YOUR-USER/sinhala-stem-segmenter/releases/download/v0.1.0/nsina-news-segmenter.model.json \
  -o nsina-news-segmenter.model.json
```

### Option 2: Train Your Own Model

Train from any UTF-8 plain text corpus:

```bash
sinhala-segment train corpus.txt -o model.json
```

For better results, use a large modern Sinhala corpus.

## Use From The Command Line

Segment whitespace-separated words:

```bash
echo "ජනාධිපතිවරයාය ආණ්ඩුවට කරනවා" \
  | sinhala-segment segment -m nsina-news-segmenter.model.json
```

Tab-separated output:

```text
ජනාධිපතිවරයාය    ජනාධිපතිවරයා    ය    1.000
ආණ්ඩුවට          ආණ්ඩුව          ට    1.000
කරනවා            කරන            වා   1.000
```

JSON lines output:

```bash
echo "ජනාධිපතිවරයාය" \
  | sinhala-segment segment -m nsina-news-segmenter.model.json --json
```

Tokenize Sinhala text from stdin before segmenting:

```bash
cat article.txt \
  | sinhala-segment segment -m nsina-news-segmenter.model.json --tokens --json
```

## Use From Python

```python
from sinhala_stem_segmenter import SinhalaStemSegmenter

segmenter = SinhalaStemSegmenter.load("nsina-news-segmenter.model.json")
result = segmenter.segment("ජනාධිපතිවරයාය")

print(result.stem)
print(result.rest)
print(result.stem + result.rest == result.normalized)
```

Train and use a small model in Python:

```python
from sinhala_stem_segmenter import SinhalaStemSegmenter

texts = [
    "දැන් මෙරට ජනාධිපතිවරයාය",
    "ජනාධිපතිවරයා අද කතා කළේය",
    "ආණ්ඩුවට සහ ආණ්ඩුවේ තීරණයට විරෝධය",
]

segmenter = SinhalaStemSegmenter()
segmenter.fit_texts(texts)

result = segmenter.segment("ආණ්ඩුවට")
print(result.stem, result.rest)
```

## Output Fields

`segmenter.segment(word)` returns a `SegmentResult`:

```python
SegmentResult(
    word="ජනාධිපතිවරයාය",
    normalized="ජනාධිපතිවරයාය",
    stem="ජනාධිපතිවරයා",
    rest="ය",
    boundary=12,
    stem_clusters=8,
    rest_clusters=1,
    confidence=1.0,
    score=42.895175,
    family_size=76,
    family_tokens=22839,
    rest_frequency=7212294,
    split=True,
)
```

Important fields:

- `stem`: left segment.
- `rest`: remaining right-side segment.
- `normalized`: NFC-normalized input.
- `split`: `False` means the model did not find a confident split.
- `confidence`: model confidence from corpus evidence, not linguistic certainty.

## Validation Results

The current NSINA-trained model was trained/evaluated on a deterministic
90/10 split of the NSINA Sinhala news corpus.

Compiled NSINA data:

```text
JSON files: 592,002
usable articles: 579,650
raw Sinhala tokens: 131,330,146
train articles: 521,670
test articles: 57,980
```

NSINA held-out evaluation:

```text
reconstruction accuracy: 100%
valid Sinhala-boundary accuracy: 100%
split coverage: 68.5566%
family-supported split rate: 99.2502%
average split confidence: 0.999983
average rest clusters: 1.252453
```

These are unsupervised metrics. They do not measure gold linguistic accuracy.
They measure whether the model preserves words, splits at legal Sinhala
boundaries, and finds corpus-supported split patterns.

Full comparison files:

- `validation/nsina_news_full.json`
- `validation/nsina_model_on_culturax_1000.json`
- `validation/culturax_5000_1000_holdout.json`
- `validation/comparison_nsina_vs_culturax.json`

## Reproduce The NSINA Model

Download/extract the NSINA repository, then compile the JSON files:

```bash
mkdir -p data/nsina
curl -L https://github.com/Sinhala-NLP/NSINA/archive/refs/heads/main.zip \
  -o data/nsina/NSINA-main.zip
unzip -q data/nsina/NSINA-main.zip 'NSINA-main/data/*' -d data/nsina
```

Compile the news JSON into plain text:

```bash
python3 scripts/compile_nsina.py \
  --data-dir data/nsina/NSINA-main/data \
  --output-dir data/nsina_compiled
```

Train and evaluate:

```bash
python3 scripts/validate_local_corpus.py \
  --train data/nsina_compiled/nsina_train.txt \
  --test data/nsina_compiled/nsina_test.txt \
  --model-out nsina-news-segmenter.model.json \
  --metrics-out validation/nsina_news_full.json
```

## Reproduce CultureX Validation

Train/evaluate on a bounded sample from
`Minuri/sinhala-corpus-culturax`:

```bash
python3 scripts/validate_culturax.py \
  --train-rows 5000 \
  --test-rows 1000 \
  --test-offset 5000 \
  --model-out culturax-sinhala-segmenter.model.json \
  --metrics-out validation/culturax_5000_1000_holdout.json
```

Evaluate the NSINA model on the same CultureX held-out sample:

```bash
python3 scripts/validate_culturax.py \
  --model-in nsina-news-segmenter.model.json \
  --test-rows 1000 \
  --test-offset 5000 \
  --metrics-out validation/nsina_model_on_culturax_1000.json
```

## Publish This Project On GitHub

Do **not** commit the extracted NSINA data, compiled corpora, or the large
`nsina-news-segmenter.model.json` file directly to GitHub. The NSINA-trained
model is about 150 MB, which is too large for normal GitHub repository files.

Recommended repository contents:

```text
README.md
LICENSE
pyproject.toml
src/
scripts/
tests/
validation/
.gitignore
```

Step-by-step:

```bash
cd sinhala-stem-segmenter
git init
git add README.md LICENSE pyproject.toml src scripts tests validation .gitignore
git commit -m "Initial Sinhala stem segmenter"
```

Create an empty repository on GitHub, then connect and push:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USER/sinhala-stem-segmenter.git
git push -u origin main
```

Publish the large trained model as a GitHub Release asset:

```bash
gh release create v0.1.0 \
  nsina-news-segmenter.model.json \
  --title "v0.1.0" \
  --notes "Initial Sinhala stem/rest segmenter with NSINA-trained model."
```

If you do not use the GitHub CLI, open your GitHub repository in the browser,
go to **Releases**, create release `v0.1.0`, and upload
`nsina-news-segmenter.model.json` as an asset.

After publishing the release, update the model download URL in this README.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Run a quick CLI check:

```bash
printf 'ජනාධිපතිවරයාය ආණ්ඩුවට කරනවා\n' \
  | PYTHONPATH=src python3 -m sinhala_stem_segmenter.cli \
      segment -m nsina-news-segmenter.model.json --json
```

## License

MIT License.

## Citation / Data Notes

This package provides the segmenter code. The pretrained NSINA news model is
derived from the public NSINA Sinhala news dataset. Check the dataset/repository
license and attribution requirements before redistributing trained models or
compiled corpora.
