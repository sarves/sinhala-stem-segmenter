# Sinhala Stem Segmenter

A simple Python library for segmenting modern written Sinhala words into:

```text
stem + rest
```

This is not a lemmatizer and it does not delete suffixes. It preserves the word:

```text
stem + rest == normalized_word
```

The package includes a built-in pretrained model, so you can use it immediately.

## Install

```bash
python3 -m pip install "git+https://github.com/sarves/sinhala-stem-segmenter.git"
```

For local development:

```bash
git clone https://github.com/sarves/sinhala-stem-segmenter.git
cd sinhala-stem-segmenter
python3 -m pip install -e .
```

## Command Line

```bash
echo "ජනාධිපතිවරයාය ආණ්ඩුවට කරනවා" | sinhala-segment segment
```

Example output:

```text
ජනාධිපතිවරයාය    ජනාධිපතිවරයා    ය    1.000
ආණ්ඩුවට          ආණ්ඩුව          ට    1.000
කරනවා            කරන            වා   1.000
```

JSON output:

```bash
echo "ජනාධිපතිවරයාය" | sinhala-segment segment --json
```

Segment all Sinhala tokens from a text file:

```bash
cat article.txt | sinhala-segment segment --tokens --json
```

## Python

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

## Result Format

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

Field meanings:

- `word`: the original input word.
- `normalized`: the Unicode-normalized form used by the segmenter.
- `stem`: the left segment selected by the model.
- `rest`: the remaining right-side segment.
- `boundary`: character offset where `stem` ends and `rest` starts.
- `stem_clusters`: number of Sinhala orthographic clusters in `stem`.
- `rest_clusters`: number of Sinhala orthographic clusters in `rest`.
- `confidence`: confidence score between `0` and `1`.
- `score`: raw internal score for the selected split.
- `family_size`: number of different rest parts seen with this stem pattern.
- `family_tokens`: total corpus frequency supporting this stem pattern.
- `rest_frequency`: frequency of this rest pattern in the model.
- `split`: `True` if a split was found; `False` if the whole word was kept as the stem.

## Train Your Own Model

You can train a custom model from a UTF-8 Sinhala text file:

```bash
sinhala-segment train corpus.txt -o my-model.json.gz
```

Use your custom model:

```bash
echo "ආණ්ඩුවට" | sinhala-segment segment -m my-model.json.gz
```

Train from Python:

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

## Advanced Details

The bundled model was trained in a data-driven way from large modern Sinhala
text collections:

- Sinhala news data from the NSINA project.
- Sinhala web text from the CulturaX-based Sinhala corpus.

The model does not use hand-written grammatical suffix labels. Instead, it
learns repeated word-family patterns by collecting possible Sinhala-safe split
points and counting how often left segments and right-side remainders occur.

More detailed development notes are in:

- `development/logic.md`
- `development/score_formula.md`
- `development/training_and_testing.md`

Exported model tables are in:

- `data/suffix_frequencies.tsv`
- `data/stems.tsv`

In this project, `suffix` means the learned right-side `rest` part. These are
not manually verified grammatical suffixes.

The exported tables contain:

- `461,704` learned rest/suffix candidates with frequencies.
- `811,966` learned stem candidates with support counts.

## Logic

Training logic:

1. Normalize Sinhala text with Unicode NFC normalization.
2. Extract Sinhala-script word tokens.
3. Split each word into Sinhala orthographic clusters.
4. Generate all possible legal `stem + rest` split points.
5. Reject split points that cut inside Sinhala writing units.
6. Count each left-side candidate as a possible stem.
7. Count each right-side candidate as a possible rest/suffix.
8. Count how many different rest parts occur with each stem candidate.
9. Count how often each stem family occurs in the training text.
10. Save the learned counts into the bundled model resource.

Segmentation logic:

1. Normalize the input word.
2. Split it into Sinhala orthographic clusters.
3. Generate legal split candidates.
4. Score each candidate split using corpus evidence.
5. Select the highest-scoring split above the threshold.
6. If no split is strong enough, keep the whole word as the stem.

The segmenter is Sinhala-script aware. It splits only at conservative Sinhala
orthographic-cluster boundaries, so it avoids cutting inside vowel signs,
al-lakuna, ZWJ/ZWNJ sequences, and related abugida writing units.

## Score Formula

For each candidate split, the model calculates:

```python
score =
    2.2  * log(1 + family_size)
  + 0.65 * log(1 + family_tokens)
  + 1.15 * log(1 + rest_frequency)
  + 0.7  * log(1 + stem_as_word_frequency)
  + 0.12 * stem_clusters
  - 0.45 * max(0, rest_clusters - 4)
  - tiny_stem_penalty
```

Where:

```python
tiny_stem_penalty = 0.7 if stem_clusters <= min_stem_clusters else 0.0
```

Meaning:

- `family_size`: number of different rest parts seen with the same stem.
- `family_tokens`: total frequency of all words supporting that stem family.
- `rest_frequency`: total frequency of the selected rest/suffix pattern.
- `stem_as_word_frequency`: how often the stem appeared as a standalone word.
- `stem_clusters`: number of Sinhala orthographic clusters in the stem.
- `rest_clusters`: number of Sinhala orthographic clusters in the rest.

The formula uses `log(1 + value)` so high-frequency evidence helps without
overpowering every other signal.

The score rewards:

- stems that appear with many different rest parts
- stem families that appear frequently
- rest/suffix patterns that are common
- stems that also occur as standalone words
- stems that are not too short

The score penalizes:

- very long rest parts
- very short stems

The score is an internal evidence score. It is not a probability and not a
guarantee of linguistic correctness.

## Training And Testing

The bundled model was trained by merging frequency evidence from the training
collections and compressing the final learned counts into:

```text
src/sinhala_stem_segmenter/resources/default.model.json.gz
```

Testing checks:

- `stem + rest == normalized_word`
- splits happen only at valid Sinhala cluster boundaries
- short or unsupported words can safely remain unsplit
- saved custom models can be loaded again
- the command-line tool works with the bundled model

The model was also evaluated with unsupervised corpus checks such as split
coverage, family-supported split rate, average confidence, and average rest
length. These are model-support metrics, not human gold-standard linguistic
accuracy scores.

The reported `confidence`, `score`, and frequency fields are model-support
signals. They are not grammatical labels and should not be read as a linguistic
proof that the split is the only correct analysis.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Run without installing:

```bash
printf 'ජනාධිපතිවරයාය ආණ්ඩුවට කරනවා\n' \
  | PYTHONPATH=src python3 -m sinhala_stem_segmenter.cli segment --json
```

## License

MIT License.
