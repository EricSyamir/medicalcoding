"""
Pipeline orchestrator: ties ingestion → extraction → retrieval → coding → validation
into a single callable that returns a ReviewPayload.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .audit import AuditTrail
from .code_retrieval import CodeRetriever
from .coding import assign_codes
from .extraction import extract_facts
from .ingestion import ClinicalNote
from .models import ReviewPayload
from .llm import create_llm_client
from .validation import determine_review_priority, validate

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


class MedicalCodingPipeline:
    """
    End-to-end medical coding pipeline.

    Parameters
    ----------
    provider:
        LLM provider: "openai" or "gemini".
    api_key:
        API key for the provider. Falls back to OPENAI_API_KEY or GOOGLE_API_KEY/GEMINI_API_KEY.
    model:
        Model name (e.g. gpt-4o, gemini-1.5-flash).
    data_dir:
        Directory containing icd10_codes.json and cpt_codes.json.
    top_k_candidates:
        Number of retrieval candidates to pass to the LLM per concept.
    """

    PIPELINE_VERSION = "1.0.0"

    def __init__(
        self,
        provider: str = "openai",
        api_key: str | None = None,
        model: str | None = None,
        data_dir: str | Path = _DEFAULT_DATA_DIR,
        top_k_candidates: int = 10,
    ) -> None:
        self.llm, self.model = create_llm_client(provider=provider, api_key=api_key, model=model)

        data_dir = Path(data_dir)
        self.retriever = CodeRetriever(
            icd10_path=data_dir / "icd10_codes.json",
            cpt_path=data_dir / "cpt_codes.json",
            top_k=top_k_candidates,
        )
        logger.info("Pipeline initialised (model=%s, top_k=%d)", model, top_k_candidates)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def process_note(self, note: ClinicalNote) -> ReviewPayload:
        """
        Run the full pipeline on a ClinicalNote and return a ReviewPayload.

        Steps
        -----
        1. Audit trail init
        2. LLM extraction of medical facts
        3. TF-IDF retrieval of ICD-10 + CPT candidates
        4. LLM code assignment with confidence + evidence
        5. Rule-based validation and warning generation
        6. Assemble and return ReviewPayload
        """
        audit = AuditTrail(note.note_id)
        audit.record(f"Pipeline started: note_id={note.note_id}, source={note.source}, words={note.word_count}")

        # ── Step 1: Extract facts ──────────────────────────────────────
        audit.record("Step 1/4: Extracting clinical facts via LLM")
        try:
            facts = extract_facts(note.normalized_text, self.llm, self.model)
        except Exception as exc:
            audit.record(f"Extraction failed: {exc}")
            raise

        audit.record(
            f"Extraction complete: {len(facts.diagnoses_mentioned)} diagnoses, "
            f"{len(facts.symptoms_signs)} symptoms, "
            f"{len(facts.procedures_mentioned)} procedures"
        )

        # ── Step 2: Retrieve candidate codes ──────────────────────────
        audit.record("Step 2/4: Retrieving candidate codes via TF-IDF")

        # Build diverse queries from all extracted signals
        icd10_queries = (
            facts.diagnoses_mentioned
            + facts.symptoms_signs
            + facts.relevant_history
        )
        cpt_queries = (
            facts.procedures_mentioned
            + facts.symptoms_signs[:3]  # context for E&M level
        )

        icd10_candidates = self.retriever.bulk_search_icd10(icd10_queries)
        cpt_candidates = self.retriever.bulk_search_cpt(cpt_queries)

        audit.record(
            f"Retrieval complete: {len(icd10_candidates)} ICD-10 candidates, "
            f"{len(cpt_candidates)} CPT candidates"
        )

        # ── Step 3: Assign codes ───────────────────────────────────────
        audit.record("Step 3/4: Assigning and scoring codes via LLM")
        try:
            dx_codes, px_codes = assign_codes(
                note_text=note.normalized_text,
                facts=facts,
                icd10_candidates=icd10_candidates,
                cpt_candidates=cpt_candidates,
                llm=self.llm,
            )
        except Exception as exc:
            audit.record(f"Code assignment failed: {exc}")
            raise

        audit.record(
            f"Coding complete: {len(dx_codes)} diagnosis codes, {len(px_codes)} procedure codes"
        )

        # ── Step 4: Validate ───────────────────────────────────────────
        audit.record("Step 4/4: Running rule-based validation")
        warnings = validate(facts, dx_codes, px_codes)
        priority = determine_review_priority(warnings, dx_codes)
        audit.record(
            f"Validation complete: {len(warnings)} warnings, review_priority={priority}"
        )

        # ── Assemble payload ───────────────────────────────────────────
        payload = ReviewPayload(
            note_id=note.note_id,
            note_word_count=note.word_count,
            extracted_facts=facts,
            diagnosis_codes=dx_codes,
            procedure_codes=px_codes,
            warnings=warnings,
            requires_human_review=True,
            review_priority=priority,
            pipeline_version=self.PIPELINE_VERSION,
            model_used=self.model,
            audit_trail=audit.events(),
        )

        audit.record(f"Pipeline complete. Summary: {payload.summary()}")
        return payload

    def process_file(self, path: str | Path) -> ReviewPayload:
        """Convenience wrapper: ingest from file path then process."""
        note = ClinicalNote.from_file(path)
        return self.process_note(note)

    def process_text(self, text: str) -> ReviewPayload:
        """Convenience wrapper: ingest from string then process."""
        note = ClinicalNote.from_string(text)
        return self.process_note(note)
