# Data Files

This directory contains exported tables from the bundled pretrained model.

## `suffix_frequencies.tsv`

All right-side remainders learned by the model, sorted by frequency.

The column name is `rest_or_suffix` because the model is data-driven. These
items are not manually labeled grammatical suffixes; they are right-side parts
that appeared after possible stems during training.

Columns:

```text
rest_or_suffix    frequency
```

## `stems.tsv`

All learned stem candidates in the bundled model, sorted by corpus support.

Columns:

```text
stem    family_size    family_tokens    stem_as_word_frequency
```

- `stem`: learned left-side candidate.
- `family_size`: number of different right-side remainders seen with the stem.
- `family_tokens`: total frequency of all words supporting this stem candidate.
- `stem_as_word_frequency`: how often the stem appeared as a standalone word.
