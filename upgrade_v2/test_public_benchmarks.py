"""Tests for deterministic public-benchmark selection and label integrity."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from run_public_openrouter import load_cases as load_rxsafe
from run_rxqa_openrouter import load_cases as load_rxqa


class PublicBenchmarkTests(unittest.TestCase):
    def test_rxsafe_deduplicates_scenarios_and_balances_gold_positions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for filename, key in (("RxSafeBench_Contradiction.json", "Contradiction"),
                                  ("RxSafeBench_Interaction.json", "interaction")):
                rows = [{"indication": "example", key: [{
                    "dialogue": f"fictional dialogue {i}", "med_true": "correct",
                    "med_false": "unsafe", "med_not_related": "unrelated"}
                    for i in range(3)]}]
                rows.append({"indication": "example", key: [rows[0][key][0]]})
                (root / filename).write_text(json.dumps(rows))
            cases = load_rxsafe(root, 3)
            self.assertEqual(len(cases), 6)
            self.assertEqual(len({c["id"] for c in cases}), 6)
            self.assertEqual({letter: sum(c["gold"] == letter for c in cases)
                              for letter in "ABC"}, {"A": 2, "B": 2, "C": 2})
            self.assertTrue(all(c["options"]["ABC".index(c["gold"])] == "correct"
                                for c in cases))

    def test_rxqa_rejects_inconsistent_answer_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rxqa.csv"
            with path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["q_id", "question", "A", "B", "C", "D",
                                                      "correct", "correct_idx", "pharmacist_rated_difficulty"])
                writer.writeheader()
                for i in range(300):
                    writer.writerow({"q_id": i, "question": "example?", "A": "a", "B": "b",
                                     "C": "c", "D": "d", "correct": "b" if i else "a",
                                     "correct_idx": 1, "pharmacist_rated_difficulty": "Easy"})
            with self.assertRaises(ValueError):
                load_rxqa(path, 300)


if __name__ == "__main__":
    unittest.main()
