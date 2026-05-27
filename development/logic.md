# Logic

The package implements a data-driven Sinhala stem/rest segmenter.

It is not a lemmatizer and does not delete text. The central invariant is:

```text
stem + rest == normalized_word
```

## Training Logic

1. Normalize input text with Unicode NFC normalization.
2. Extract Sinhala-script word tokens.
3. Split each word into Sinhala orthographic clusters.
4. Generate all legal split points that do not cut inside Sinhala writing units.
5. For each legal split, collect:
   - left part as a stem candidate
   - right part as a rest/suffix candidate
   - frequency counts for the stem/rest pattern
6. Store:
   - word frequencies
   - stem candidate to rest candidate counts
   - global rest/suffix frequencies
7. Save the learned counts as a model resource.

## Segmentation Logic

For a new word:

1. Normalize the word.
2. Split it into Sinhala orthographic clusters.
3. Generate every legal `stem + rest` split.
4. Look up each split in the learned model.
5. Score each candidate split.
6. Select the highest-scoring split above the minimum score threshold.
7. If no candidate is strong enough, return the whole word as `stem` and an
   empty `rest`.

## Sinhala Boundary Logic

The segmenter uses conservative Sinhala cluster boundaries. It avoids splitting
inside:

- dependent vowel signs
- al-lakuna/virama sequences
- ZWJ and ZWNJ sequences
- Sinhala combining signs
- related abugida writing units

This protects the written shape of Sinhala words while still allowing
data-driven segmentation.
