"""A bounded prescription-review harness for synthetic fixtures.

This module does not contain a clinical drug knowledge base. Its rules must be
supplied from an independently curated, versioned source before real use.
No output status means that a prescription is clinically safe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MedicationOrder:
    order_id: str
    ingredient_code: str
    dose_value: float | None
    dose_unit: str | None
    route: str | None
    frequency: str | None


@dataclass(frozen=True)
class PatientSnapshot:
    allergy_ingredient_codes: frozenset[str]
    egfr_ml_min_1_73m2: float | None = None


@dataclass(frozen=True)
class Rule:
    rule_id: str
    kind: str  # ddi or renal
    drug_a: str
    drug_b: str | None
    severity: str  # critical or warning
    evidence_source: str
    evidence_version: str
    egfr_below: float | None = None


@dataclass(frozen=True)
class Finding:
    kind: str
    severity: str
    order_ids: tuple[str, ...]
    message: str
    rule_id: str | None = None
    evidence_source: str | None = None
    evidence_version: str | None = None


@dataclass(frozen=True)
class Review:
    status: str  # stop, needs_information, review, or no_rule_hit
    knowledge_scope: str
    findings: tuple[Finding, ...]


def review(snapshot: PatientSnapshot, orders: Iterable[MedicationOrder],
           rules: Iterable[Rule], knowledge_scope: str) -> Review:
    if not knowledge_scope:
        raise ValueError("knowledge_scope is required")
    orders = tuple(orders)
    rules = tuple(rules)
    if len({o.order_id for o in orders}) != len(orders):
        raise ValueError("order_id values must be unique")
    for rule in rules:
        if not rule.evidence_source or not rule.evidence_version:
            raise ValueError("every rule needs versioned evidence")
        if rule.kind not in {"ddi", "renal"} or rule.severity not in {"critical", "warning"}:
            raise ValueError("unsupported rule")

    findings: list[Finding] = []
    for order in orders:
        missing = [key for key, value in {
            "ingredient_code": order.ingredient_code,
            "dose_value": order.dose_value,
            "dose_unit": order.dose_unit,
            "route": order.route,
            "frequency": order.frequency,
        }.items() if value is None or value == ""]
        if missing:
            findings.append(Finding("missing_order_field", "needs_information", (order.order_id,),
                                    "Missing structured fields: " + ", ".join(missing)))
        if order.ingredient_code and order.ingredient_code in snapshot.allergy_ingredient_codes:
            findings.append(Finding("exact_code_allergy", "critical", (order.order_id,),
                                    "Ingredient code matches a documented allergy code"))

    by_ingredient: dict[str, list[str]] = {}
    for order in orders:
        if order.ingredient_code:
            by_ingredient.setdefault(order.ingredient_code, []).append(order.order_id)
    for code, ids in by_ingredient.items():
        if len(ids) > 1:
            findings.append(Finding("same_ingredient_multiple_orders", "warning", tuple(sorted(ids)),
                                    "Multiple orders have the same normalized ingredient; review intent"))

    for rule in rules:
        if rule.kind == "ddi" and rule.drug_b:
            for left in by_ingredient.get(rule.drug_a, []):
                for right in by_ingredient.get(rule.drug_b, []):
                    if left != right:
                        findings.append(Finding("ddi", rule.severity, tuple(sorted((left, right))),
                                                "Interaction rule matched", rule.rule_id,
                                                rule.evidence_source, rule.evidence_version))
        elif rule.kind == "renal" and rule.drug_a in by_ingredient:
            if rule.egfr_below is None:
                raise ValueError("renal rule needs egfr_below")
            for order_id in by_ingredient[rule.drug_a]:
                if snapshot.egfr_ml_min_1_73m2 is None:
                    findings.append(Finding("renal_measurement_missing", "needs_information", (order_id,),
                                            "eGFR is required for this rule", rule.rule_id,
                                            rule.evidence_source, rule.evidence_version))
                elif snapshot.egfr_ml_min_1_73m2 < rule.egfr_below:
                    findings.append(Finding("renal_threshold", rule.severity, (order_id,),
                                            "eGFR is below the rule threshold", rule.rule_id,
                                            rule.evidence_source, rule.evidence_version))

    severities = {f.severity for f in findings}
    status = ("stop" if "critical" in severities else
              "needs_information" if "needs_information" in severities else
              "review" if "warning" in severities else "no_rule_hit")
    return Review(status, knowledge_scope, tuple(findings))


def replace_one_order(orders: Iterable[MedicationOrder], order_id: str,
                      replacement: MedicationOrder) -> tuple[MedicationOrder, ...]:
    """Apply one proposed change. A caller must review the result again."""
    orders = tuple(orders)
    if replacement.order_id != order_id:
        raise ValueError("replacement must retain the order_id")
    if sum(order.order_id == order_id for order in orders) != 1:
        raise ValueError("exactly one source order must match")
    return tuple(replacement if order.order_id == order_id else order for order in orders)
