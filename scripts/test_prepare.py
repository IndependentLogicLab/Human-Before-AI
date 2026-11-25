"""
Human Before AI
IndependentLogicLab
Automated sample preparation tests.
"""

import unittest
import hashlib
from prepare import prepare_samples


class TestSamplePreparation(unittest.TestCase):

    def setUp(self):
        self.text = " ".join(
            f"word{i}" for i in range(5000)
        )

    def test_sample_length(self):
        samples = list(prepare_samples(self.text))

        self.assertGreater(len(samples), 0)

        for passage, count, start, end in samples:
            self.assertGreaterEqual(count, 750)
            self.assertLessEqual(count, 1500)
            self.assertEqual(len(passage.split()), count)

    def test_original_text_preserved(self):
        for passage, count, start, end in prepare_samples(
            self.text
        ):
            self.assertEqual(
                passage, self.text[start:end]
            )

    def test_no_overlap(self):
        previous_end = 0

        for passage, count, start, end in prepare_samples(
            self.text
        ):
            self.assertGreaterEqual(start, previous_end)
            previous_end = end

    def test_short_document(self):
        text = "word " * 749
        self.assertEqual(list(prepare_samples(text)), [])

    def test_minimum_length(self):
        text = "word " * 750
        samples = list(prepare_samples(text))

        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0][1], 750)

    def test_empty_document(self):
        self.assertEqual(list(prepare_samples("")), [])

    def test_reproducibility(self):
        first = list(prepare_samples(self.text))
        second = list(prepare_samples(self.text))

        self.assertEqual(first, second)

    def test_hash_consistency(self):
        passage = list(prepare_samples(self.text))[0][0]

        first = hashlib.sha256(
            passage.encode("utf-8")
        ).hexdigest()

        second = hashlib.sha256(
            passage.encode("utf-8")
        ).hexdigest()

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_whitespace_preserved(self):
        text = "word \n\t" * 800

        for passage, count, start, end in prepare_samples(text):
            self.assertEqual(passage, text[start:end])


if __name__ == "__main__":
    unittest.main(verbosity=2)
