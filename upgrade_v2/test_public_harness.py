import json
import unittest

from run_public_harness import gated_answer, followup_prompt, paired_ci


CASE = {"id": "x", "type": "interaction", "dialogue": "Patient takes warfarin daily.",
        "options": ["one", "two", "three"], "gold": "B"}


class PublicHarnessTests(unittest.TestCase):
    def test_gold_does_not_enter_prompt(self):
        prompt = followup_prompt(CASE, "A", "harness")
        self.assertIn("Patient takes warfarin daily", prompt)
        self.assertNotIn("gold", prompt.lower())

    def test_ungrounded_change_is_rejected(self):
        response = json.dumps({"evidence_quote": "not in dialogue", "concern": "risk",
                               "decision": "CHANGE", "final": "B"})
        self.assertEqual(gated_answer(response, CASE, "A"), ("A", "ungrounded_change"))

    def test_grounded_change_is_allowed(self):
        response = json.dumps({"evidence_quote": "takes warfarin", "concern": "risk",
                               "decision": "CHANGE", "final": "B"})
        self.assertEqual(gated_answer(response, CASE, "A"), ("B", "changed"))

    def test_invalid_keep_cannot_silently_change(self):
        response = json.dumps({"evidence_quote": "", "concern": "", "decision": "KEEP", "final": "B"})
        self.assertEqual(gated_answer(response, CASE, "A"), ("A", "invalid_keep"))

    def test_identical_predictions_have_zero_paired_interval(self):
        self.assertEqual(paired_ci([1, 0, 1, 0], [1, 0, 1, 0], draws=100), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
