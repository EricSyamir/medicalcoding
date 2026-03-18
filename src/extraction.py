"""
Medical fact extraction via LLM (OpenAI or Gemini).

LLM Call 1 of 2: extract structured clinical facts from the raw note text.
The output feeds the retrieval and coding layers.
"""

from __future__ import annotations

import json
import logging
from textwrap import dedent
from typing import TYPE_CHECKING

from .models import ExtractedFacts

if TYPE_CHECKING:
    from .llm import LLMClient

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = dedent("""
    You are a senior clinical documentation specialist with expertise in medical
    coding (CPC-certified). Your task is to read a clinical note and extract
    structured medical facts that will be used to assign ICD-10-CM and CPT codes.

    Return ONLY valid JSON matching the schema below. Do not add commentary.

    Schema:
    {
      "chief_complaint": "<string or null>",
      "diagnoses_mentioned": ["<list of explicit and implied diagnoses>"],
      "symptoms_signs": ["<list of symptoms, signs, physical exam findings>"],
      "procedures_mentioned": ["<list of procedures performed or ordered>"],
      "medications": ["<list of medications with doses if mentioned>"],
      "lab_imaging_results": ["<list of lab/imaging results with values>"],
      "relevant_history": ["<past medical history, surgical history, family history>"],
      "supporting_quotes": ["<verbatim short excerpts (≤20 words each) that strongly support coding>"]
    }

    Rules:
    - Be specific: include qualifiers (laterality, acuity, severity, stage).
    - Include both confirmed and probable diagnoses (note uncertainty).
    - Do not fabricate information not in the note.
    - Keep each list item concise (one concept per item).
""").strip()


def extract_facts(
    note_text: str,
    llm: "LLMClient",
    model_name: str = "",
) -> ExtractedFacts:
    """
    Use the LLM to extract structured medical facts from a clinical note.

    Parameters
    ----------
    note_text:
        The raw (normalised) clinical note.
    llm:
        An LLM client (OpenAI or Gemini) with generate_json().
    model_name:
        Display name for logging (optional).

    Returns
    -------
    ExtractedFacts
        Validated Pydantic model of extracted medical facts.
    """
    logger.info("Extracting medical facts with model=%s", model_name or "llm")

    user_message = f"Clinical Note:\n\n{note_text}"

    try:
        data = llm.generate_json(EXTRACTION_SYSTEM_PROMPT, user_message)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Failed to parse extraction response as JSON: %s", exc)
        raise ValueError(f"LLM returned invalid JSON during extraction: {exc}") from exc

    facts = ExtractedFacts(**data)
    logger.info(
        "Extraction complete: %d diagnoses, %d symptoms, %d procedures",
        len(facts.diagnoses_mentioned),
        len(facts.symptoms_signs),
        len(facts.procedures_mentioned),
    )
    return facts
