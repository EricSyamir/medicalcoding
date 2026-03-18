"""
Validation layer: post-process coding results to surface warnings, conflicts,
and documentation gaps for the human reviewer.

No LLM calls — all rule-based for speed, determinism, and auditability.
"""

from __future__ import annotations

import logging
from typing import List

from .models import (
    ConfidenceLevel,
    DiagnosisCode,
    ExtractedFacts,
    ProcedureCode,
    Warning,
    WarningSeverity,
    WarningType,
)

logger = logging.getLogger(__name__)

# Known conflicting code pairs (code_a, code_b, reason)
_CONFLICT_PAIRS: list[tuple[str, str, str]] = [
    ("E11.9", "E10.9", "Type 2 and Type 1 diabetes assigned simultaneously"),
    ("I50.22", "I50.32", "Systolic and diastolic heart failure both coded — specify type"),
    ("J44.9", "J44.1", "Unspecified COPD redundant when COPD with exacerbation is coded"),
    ("J18.9", "J44.0", "Verify: pneumonia + COPD-with-infection — confirm distinct organisms"),
]

# Diagnosis codes that require a supporting procedure code
_DX_REQUIRES_PROCEDURE: dict[str, list[str]] = {
    "I21.9": ["92928", "93458"],   # AMI → expect PCI or cath
    "K80.20": ["45378"],            # Gallstones → may expect surgical or endo workup
}

# Codes that signal high-risk and should trigger urgent review
_HIGH_RISK_CODES: set[str] = {
    "I21.9", "I21.01", "A41.9", "J96.00", "T14.91",
    "C34.10", "C50.911", "C61", "C18.9",
}


def validate(
    facts: ExtractedFacts,
    dx_codes: list[DiagnosisCode],
    px_codes: list[ProcedureCode],
) -> list[Warning]:
    """
    Run all validation rules and return a consolidated warning list.
    """
    warnings: list[Warning] = []

    warnings.extend(_check_no_primary(dx_codes))
    warnings.extend(_check_low_confidence(dx_codes, px_codes))
    warnings.extend(_check_conflicts(dx_codes))
    warnings.extend(_check_missing_procedures(dx_codes, px_codes))
    warnings.extend(_check_high_risk(dx_codes))
    warnings.extend(_check_empty_evidence(dx_codes, px_codes))
    warnings.extend(_check_missing_chief_complaint(facts, dx_codes))

    logger.info(
        "Validation complete: %d warnings (%d errors, %d warnings, %d info)",
        len(warnings),
        sum(1 for w in warnings if w.severity == WarningSeverity.ERROR),
        sum(1 for w in warnings if w.severity == WarningSeverity.WARNING),
        sum(1 for w in warnings if w.severity == WarningSeverity.INFO),
    )
    return warnings


# ---------------------------------------------------------------------------
# Individual rule checks
# ---------------------------------------------------------------------------

def _check_no_primary(dx_codes: list[DiagnosisCode]) -> list[Warning]:
    if dx_codes and not any(d.is_primary for d in dx_codes):
        return [
            Warning(
                type=WarningType.DOCUMENTATION_GAP,
                severity=WarningSeverity.WARNING,
                message="No primary diagnosis has been designated. "
                        "A first-listed/principal diagnosis is required for claims submission.",
                related_codes=[d.code for d in dx_codes],
            )
        ]
    return []


def _check_low_confidence(
    dx_codes: list[DiagnosisCode],
    px_codes: list[ProcedureCode],
) -> list[Warning]:
    warnings = []
    for code in dx_codes:
        if code.confidence_level == ConfidenceLevel.LOW:
            warnings.append(
                Warning(
                    type=WarningType.AMBIGUITY,
                    severity=WarningSeverity.WARNING,
                    message=f"ICD-10 {code.code} ({code.description}) has low confidence "
                            f"({code.confidence_score:.0%}). Documentation may be insufficient.",
                    related_codes=[code.code],
                )
            )
    for code in px_codes:
        if code.confidence_level == ConfidenceLevel.LOW:
            warnings.append(
                Warning(
                    type=WarningType.AMBIGUITY,
                    severity=WarningSeverity.WARNING,
                    message=f"CPT {code.code} ({code.description}) has low confidence "
                            f"({code.confidence_score:.0%}). Verify procedure was performed.",
                    related_codes=[code.code],
                )
            )
    return warnings


def _check_conflicts(dx_codes: list[DiagnosisCode]) -> list[Warning]:
    coded = {d.code for d in dx_codes}
    warnings = []
    for code_a, code_b, reason in _CONFLICT_PAIRS:
        if code_a in coded and code_b in coded:
            warnings.append(
                Warning(
                    type=WarningType.CONFLICT,
                    severity=WarningSeverity.ERROR,
                    message=f"Coding conflict between {code_a} and {code_b}: {reason}",
                    related_codes=[code_a, code_b],
                )
            )
    return warnings


def _check_missing_procedures(
    dx_codes: list[DiagnosisCode],
    px_codes: list[ProcedureCode],
) -> list[Warning]:
    coded_dx = {d.code for d in dx_codes}
    coded_px = {p.code for p in px_codes}
    warnings = []
    for dx, expected_px in _DX_REQUIRES_PROCEDURE.items():
        if dx in coded_dx and not coded_px.intersection(expected_px):
            warnings.append(
                Warning(
                    type=WarningType.MISSING_INFO,
                    severity=WarningSeverity.INFO,
                    message=f"Diagnosis {dx} is present but no expected supporting procedure "
                            f"code found (expected one of: {', '.join(expected_px)}). "
                            "Verify documentation.",
                    related_codes=[dx] + expected_px,
                )
            )
    return warnings


def _check_high_risk(dx_codes: list[DiagnosisCode]) -> list[Warning]:
    warnings = []
    for code in dx_codes:
        if code.code in _HIGH_RISK_CODES:
            warnings.append(
                Warning(
                    type=WarningType.DOCUMENTATION_GAP,
                    severity=WarningSeverity.WARNING,
                    message=f"High-risk diagnosis {code.code} ({code.description}) detected. "
                            "Ensure all supporting documentation, staging, and complications are coded.",
                    related_codes=[code.code],
                )
            )
    return warnings


def _check_empty_evidence(
    dx_codes: list[DiagnosisCode],
    px_codes: list[ProcedureCode],
) -> list[Warning]:
    warnings = []
    for code in dx_codes:
        if not code.evidence:
            warnings.append(
                Warning(
                    type=WarningType.DOCUMENTATION_GAP,
                    severity=WarningSeverity.WARNING,
                    message=f"ICD-10 {code.code} has no supporting evidence quotes. "
                            "Human reviewer should verify source documentation.",
                    related_codes=[code.code],
                )
            )
    for code in px_codes:
        if not code.evidence:
            warnings.append(
                Warning(
                    type=WarningType.DOCUMENTATION_GAP,
                    severity=WarningSeverity.WARNING,
                    message=f"CPT {code.code} has no supporting evidence quotes. "
                            "Verify procedure documentation.",
                    related_codes=[code.code],
                )
            )
    return warnings


def _check_missing_chief_complaint(
    facts: ExtractedFacts,
    dx_codes: list[DiagnosisCode],
) -> list[Warning]:
    warnings = []
    if not facts.chief_complaint:
        warnings.append(
            Warning(
                type=WarningType.MISSING_INFO,
                severity=WarningSeverity.INFO,
                message="Chief complaint could not be identified in the note. "
                        "Ensure the principal diagnosis reflects the reason for the encounter.",
            )
        )
    return warnings


def determine_review_priority(warnings: list[Warning], dx_codes: list[DiagnosisCode]) -> str:
    """Compute overall review priority from warnings and high-risk codes."""
    if any(w.severity == WarningSeverity.ERROR for w in warnings):
        return "urgent"
    if any(d.code in _HIGH_RISK_CODES for d in dx_codes):
        return "urgent"
    if any(w.severity == WarningSeverity.WARNING for w in warnings):
        return "normal"
    return "low"
