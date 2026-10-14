import unittest

from evolution_gate import FrozenEvaluation, eligible_for_promotion
from harness import MedicationOrder, PatientSnapshot, Rule, replace_one_order, review


def order(order_id: str, ingredient: str, dose: float = 1.0) -> MedicationOrder:
    return MedicationOrder(order_id, ingredient, dose, "unit", "oral", "daily")


class HarnessTests(unittest.TestCase):
    def test_exact_allergy_code_stops(self):
        result = review(PatientSnapshot(frozenset({"ING-A"})), [order("one", "ING-A")],
                        [], "synthetic-fixture-v1")
        self.assertEqual(result.status, "stop")
        self.assertEqual(result.findings[0].kind, "exact_code_allergy")

    def test_versioned_ddi_and_one_order_repair(self):
        rule = Rule("R1", "ddi", "ING-A", "ING-B", "critical", "fixture", "v1")
        before = [order("one", "ING-A"), order("two", "ING-B")]
        self.assertEqual(review(PatientSnapshot(frozenset()), before, [rule],
                                "synthetic-fixture-v1").status, "stop")
        after = replace_one_order(before, "two", order("two", "ING-C"))
        result = review(PatientSnapshot(frozenset()), after, [rule], "synthetic-fixture-v1")
        self.assertEqual(result.status, "no_rule_hit")
        self.assertEqual(after[0], before[0])

    def test_missing_renal_information_requests_data(self):
        rule = Rule("R2", "renal", "ING-C", None, "critical", "fixture", "v1", 30)
        result = review(PatientSnapshot(frozenset(), None), [order("one", "ING-C")],
                        [rule], "synthetic-fixture-v1")
        self.assertEqual(result.status, "needs_information")

    def test_rule_without_provenance_is_rejected(self):
        rule = Rule("R3", "ddi", "ING-A", "ING-B", "critical", "", "v1")
        with self.assertRaises(ValueError):
            review(PatientSnapshot(frozenset()), [order("one", "ING-A")],
                   [rule], "synthetic-fixture-v1")

    def test_evolution_gate_rejects_safety_regression(self):
        old = FrozenEvaluation("v1", 250, 0.03, 8, 0.70)
        new = FrozenEvaluation("v2", 250, 0.04, 7, 0.75)
        self.assertEqual(eligible_for_promotion(old, new, True)[0], False)


if __name__ == "__main__":
    unittest.main()
