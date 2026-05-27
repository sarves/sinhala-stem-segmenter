import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sinhala_stem_segmenter import SinhalaStemSegmenter


class ModelTests(unittest.TestCase):
    def test_segment_preserves_word(self):
        model = SinhalaStemSegmenter(min_family_size=2, min_rest_frequency=1, min_score=1.0)
        model.fit_texts(
            [
                "ජනාධිපතිවරයා ජනාධිපතිවරයාය ජනාධිපතිවරයාට",
                "ආණ්ඩුව ආණ්ඩුවේ ආණ්ඩුවට",
            ]
        )

        result = model.segment("ජනාධිපතිවරයාට")

        self.assertEqual(result.stem + result.rest, result.normalized)
        self.assertTrue(result.split)
        self.assertTrue(result.rest)

    def test_unknown_short_word_no_split(self):
        model = SinhalaStemSegmenter()
        result = model.segment("මම")
        self.assertEqual(result.stem, "මම")
        self.assertEqual(result.rest, "")
        self.assertFalse(result.split)

    def test_gzip_model_roundtrip(self):
        model = SinhalaStemSegmenter(min_family_size=2, min_rest_frequency=1, min_score=1.0)
        model.fit_texts(["ආණ්ඩුව ආණ්ඩුවට ආණ්ඩුවේ"])

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "model.json.gz"
            model.save(path)
            loaded = SinhalaStemSegmenter.load(path)

        result = loaded.segment("ආණ්ඩුවට")
        self.assertEqual(result.stem + result.rest, result.normalized)


if __name__ == "__main__":
    unittest.main()
