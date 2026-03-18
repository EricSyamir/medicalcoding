"""
Pydantic data models for the medical coding pipeline.
All structures are validated, serializable, and reviewer-ready.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ConfidenceLevel(str, Enum):
    HIGH = "high"      # ≥ 0.80
    MEDIUM = "medium"  # 0.50 – 0.79
    LOW = "low"        # < 0.50


class WarningSeverity(str, Enum):
    ERROR = "error"      # coding cannot proceed without resolution
    WARNING = "warning"  # review strongly advised
    INFO = "info"        # informational note for reviewer


class WarningType(str, Enum):
    MISSING_INFO = "missing_info"
    AMBIGUITY = "ambiguity"
    CONFLICT = "conflict"
    DOCUMENTATION_GAP = "documentation_gap"
    SPECIFICITY = "specificity"


# ---------------------------------------------------------------------------
# Supporting structures
# ---------------------------------------------------------------------------

class EvidenceReference(BaseModel):
    """Exact traceability from code suggestion back to note text."""

    quote: str = Field(
        ...,
        description="Verbatim excerpt from the clinical note supporting this code.",
    )
    rationale: str = Field(
        ...,
        description="Explanation of why this excerpt supports the suggested code.",
    )


class CandidateCode(BaseModel):
    """A code returned by the retrieval layer before LLM ranking."""

    code: str
    description: str
    retrieval_score: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Coded outputs
# ---------------------------------------------------------------------------

class DiagnosisCode(BaseModel):
    """A single ICD-10-CM diagnosis code suggestion."""

    code: str = Field(..., pattern=r"^[A-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?$")
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    is_primary: bool = False
    evidence: List[EvidenceReference] = Field(default_factory=list)
    reviewer_override: Optional[str] = None  # filled by human reviewer

    @field_validator("confidence_level", mode="before")
    @classmethod
    def derive_level(cls, v: str | ConfidenceLevel, info) -> ConfidenceLevel:
        if isinstance(v, ConfidenceLevel):
            return v
        return ConfidenceLevel(v)


class ProcedureCode(BaseModel):
    """A single CPT procedure code suggestion."""

    code: str = Field(..., pattern=r"^\d{5}[A-Z0-9]?$")
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    evidence: List[EvidenceReference] = Field(default_factory=list)
    reviewer_override: Optional[str] = None

    @field_validator("confidence_level", mode="before")
    @classmethod
    def derive_level(cls, v: str | ConfidenceLevel, info) -> ConfidenceLevel:
        if isinstance(v, ConfidenceLevel):
            return v
        return ConfidenceLevel(v)


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------

class Warning(BaseModel):
    """A warning, conflict, or documentation gap surfaced for the reviewer."""

    type: WarningType
    severity: WarningSeverity
    message: str
    related_codes: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Intermediate extraction payload
# ---------------------------------------------------------------------------

class ExtractedFacts(BaseModel):
    """Structured medical facts extracted by the LLM from the raw note."""

    chief_complaint: Optional[str] = None
    diagnoses_mentioned: List[str] = Field(default_factory=list)
    symptoms_signs: List[str] = Field(default_factory=list)
    procedures_mentioned: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    lab_imaging_results: List[str] = Field(default_factory=list)
    relevant_history: List[str] = Field(default_factory=list)
    supporting_quotes: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Final reviewer-ready payload
# ---------------------------------------------------------------------------

class ReviewPayload(BaseModel):
    """
    Complete, auditable output produced by the pipeline.
    Designed for human review and optional override.
    """

    note_id: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    note_word_count: int = 0

    # Core outputs
    extracted_facts: ExtractedFacts
    diagnosis_codes: List[DiagnosisCode] = Field(default_factory=list)
    procedure_codes: List[ProcedureCode] = Field(default_factory=list)
    warnings: List[Warning] = Field(default_factory=list)

    # Review metadata
    requires_human_review: bool = True
    review_priority: str = "normal"  # "urgent" | "normal" | "low"
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    # Audit
    pipeline_version: str = "1.0.0"
    model_used: str = ""
    audit_trail: List[str] = Field(default_factory=list)

    def summary(self) -> str:
        dx_count = len(self.diagnosis_codes)
        px_count = len(self.procedure_codes)
        warn_count = len(self.warnings)
        errors = sum(1 for w in self.warnings if w.severity == WarningSeverity.ERROR)
        return (
            f"Note {self.note_id}: {dx_count} diagnosis codes, "
            f"{px_count} procedure codes, {warn_count} warnings ({errors} errors)"
        )
