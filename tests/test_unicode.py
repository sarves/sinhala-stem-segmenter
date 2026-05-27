import unittest

from sinhala_stem_segmenter import legal_split_offsets, split_sinhala_clusters


class UnicodeTests(unittest.TestCase):
    def test_vowel_sign_stays_with_base(self):
        self.assertEqual(split_sinhala_clusters("කා"), ["කා"])

    def test_al_lakuna_zwj_sequence_stays_together(self):
        word = "ප්\u200dර"
        self.assertEqual(split_sinhala_clusters(word), [word])

    def test_cluster_boundaries_reconstruct(self):
        word = "ජනාධිපතිවරයාය"
        self.assertEqual("".join(split_sinhala_clusters(word)), word)

    def test_legal_offsets_do_not_include_inside_cluster(self):
        self.assertEqual(legal_split_offsets("කා"), [])


if __name__ == "__main__":
    unittest.main()
