import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'upgrade_v45'))
import unittest
from evidence46 import sentence_bounds


class SentenceTests(unittest.TestCase):
    def test_recover_left_qualifier(self):
        text = 'Prior statement. For patients with condition X, this treatment improves survival. Next statement.'
        start = text.index('this treatment'); end = text.index('survival') + 4
        left, right = sentence_bounds(text, start, end)
        self.assertEqual(text[left:right].strip(), 'For patients with condition X, this treatment improves survival.')

    def test_decimal_is_not_boundary(self):
        text = 'At 2.5 mg daily, check response. Another statement.'
        left, right = sentence_bounds(text, text.index('mg'), text.index('check') + 3)
        self.assertEqual(left, 0)
        self.assertEqual(text[left:right].strip(), 'At 2.5 mg daily, check response.')


if __name__ == '__main__':
    unittest.main()
