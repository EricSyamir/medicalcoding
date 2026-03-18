"""
Code assignment via LLM (OpenAI or Gemini).

LLM Call 2 of 2: given extracted facts and candidate codes from the retrieval
layer, the LLM selects the most appropriate codes, assigns confidence scores,
and provides evidence references traceable back to the source note.
"""

from __future__ import annotations

import json
import logging
from textwrap import dedent
from typing import TYPE_CHECKING, Any

from .models import (
    ConfidenceLevel,
    DiagnosisCode,
    EvidenceReference,
    ExtractedFacts,
    ProcedureCode,
)

if TYPE_CHECKING:
    from .llm import LLMClient

logger = logging.getLogger(__name__)

CODING_SYSTEM_PROMPT = dedent("""
    You are a Certified Professional Coder (CPC) with 15 years of inpatient and
    outpatient medical coding experience. You follow ICD-10-CM and CPT Official
    Guidelines for Coding and Reporting.

    Your task: given structured clinical facts extracted from a note and a list of
    candidate codes retrieved from a code database, select the most appropriate
    codes and assign confidence scores.

    Return ONLY valid JSON in this exact structure:
    {
      "diagnosis_codes": [
        {
          "code": "<ICD-10-CM code>",
          "description": "<full code description>",
          "confidence_score": <float 0.0-1.0>,
          "is_primary": <true|false>,
          "evidence": [
            {
              "quote": "<verbatim excerpt from the note, ≤25 words>",
              "rationale": "<why this supports the code>"
            }
          ]
        }
      ],
      "procedure_codes": [
        {
          "code": "<CPT code>",
          "description": "<full code description>",
          "confidence_score": <float 0.0-1.0>,
          "evidence": [
            {
              "quote": "<verbatim excerpt>",
              "rationale": "<why this supports the code>"
            }
          ]
        }
      ]
    }

    Coding rules you MUST follow:
    1. Code to the highest level of specificity supported by documentation.
    2. Only assign codes for conditions/procedures explicitly documented.
    3. Mark one diagnosis as is_primary (the main reason for the encounter).
    4. Assign confidence_score based on documentation clarity:
       - 0.90–1.00: Explicitly stated with specificity
       - 0.70–0.89: Clearly implied with adequate documentation
       - 0.50–0.69: Probable but partially documented
       - 0.30–0.49: Possible, documentation incomplete
       - < 0.30: Uncertain, flag for review
    5. Do not hallucinate codes—only select from the provided candidate lists.
    6. Include Z-codes for relevant history, medications, and status when documented.
""").strip()


def _confidence_level(score: float) -> ConfidenceLevel:
    if score >= 0.80:
        return ConfidenceLevel.HIGH
    if score >= 0.50:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def assign_codes(
    note_text: str,
    facts: ExtractedFacts,
    icd10_candidates: list[dict[str, Any]],
    cpt_candidates: list[dict[str, Any]],
    llm: "LLMClient",
) -> tuple[list[DiagnosisCode], list[ProcedureCode]]:
    """
    Use the LLM to select and score codes from the retrieved candidates.

    Returns
    -------
    (diagnosis_codes, procedure_codes)
        Two lists of validated Pydantic models.
    """
    logger.info(
        "Assigning codes: %d ICD-10 candidates, %d CPT candidates",
        len(icd10_candidates),
        len(cpt_candidates),
    )

    # Serialise candidates concisely for the prompt
    icd10_list = "\n".join(
        f"  {c['code']}: {c['description']}" for c in icd10_candidates
    )
    cpt_list = "\n".join(
        f"  {c['code']}: {c['description']}" for c in cpt_candidates
    )

    facts_json = facts.model_dump_json(indent=2)

    user_message = dedent(f"""
        === Extracted Clinical Facts ===
        {facts_json}

        === Candidate ICD-10-CM Codes ===
        {icd10_list or "(none retrieved)"}

        === Candidate CPT Codes ===
        {cpt_list or "(none retrieved)"}

        === Original Note (excerpt for evidence quotes) ===
        {note_text[:3000]}{"...[truncated]" if len(note_text) > 3000 else ""}

        Select the appropriate codes from the candidates above. Follow all coding rules.
    """).strip()

    try:
        data = llm.generate_json(CODING_SYSTEM_PROMPT, user_message)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Failed to parse coding response as JSON: %s", exc)
        raise ValueError(f"LLM returned invalid JSON during coding: {exc}") from exc

    # Build validated Pydantic objects
    dx_codes: list[DiagnosisCode] = []
    for item in data.get("diagnosis_codes", []):
        score = float(item.get("confidence_score", 0.5))
        evidence = [
            EvidenceReference(
                quote=e.get("quote", ""),
                rationale=e.get("rationale", ""),
            )
            for e in item.get("evidence", [])
        ]
        try:
            dx_codes.append(
                DiagnosisCode(
                    code=item["code"],
                    description=item["description"],
                    confidence_score=round(score, 3),
                    confidence_level=_confidence_level(score),
                    is_primary=bool(item.get("is_primary", False)),
                    evidence=evidence,
                )
            )
        except Exception as exc:
            logger.warning("Skipping invalid diagnosis code %s: %s", item.get("code"), exc)

    px_codes: list[ProcedureCode] = []
    for item in data.get("procedure_codes", []):
        score = float(item.get("confidence_score", 0.5))
        evidence = [
            EvidenceReference(
                quote=e.get("quote", ""),
                rationale=e.get("rationale", ""),
            )
            for e in item.get("evidence", [])
        ]
        try:
            px_codes.append(
                ProcedureCode(
                    code=item["code"],
                    description=item["description"],
                    confidence_score=round(score, 3),
                    confidence_level=_confidence_level(score),
                    evidence=evidence,
                )
            )
        except Exception as exc:
            logger.warning("Skipping invalid procedure code %s: %s", item.get("code"), exc)

    logger.info(
        "Coding complete: %d diagnosis codes, %d procedure codes",
        len(dx_codes),
        len(px_codes),
    )
    return dx_codes, px_codes
