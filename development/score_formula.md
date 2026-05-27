# Score Formula

For each legal split candidate, the model computes this score:

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

## Terms

- `family_size`: number of different rest parts seen with the same stem.
- `family_tokens`: total frequency of the full stem family.
- `rest_frequency`: total frequency of the selected rest part.
- `stem_as_word_frequency`: how often the stem appeared as a standalone word.
- `stem_clusters`: Sinhala orthographic clusters in the stem.
- `rest_clusters`: Sinhala orthographic clusters in the rest.

## Why Logarithms?

The formula uses `log(1 + value)` so large frequency values help, but do not
overpower every other signal.

## Rewards

The score rewards:

- stems that appear with many different rest parts
- stem families that appear often
- rest parts that are common across the model
- stems that also occur as standalone words
- stems that are not too short

## Penalties

The score penalizes:

- very long rest parts
- very short stems

The score is an internal evidence score. It is not a grammatical label and not
a probability of linguistic correctness.
