"""
Test suite for the medical coding pipeline.

Tests are designed to run without a live OpenAI API key by mocking LLM calls.
The code retrieval, validation, and model layers are tested with real data.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
SAMPLE_NOTE = ROOT / "examples" / "sample_note.txt"


# ---------------------------------------------------------------------------
# Ingestion tests
# ---------------------------------------------------------------------------

class TestIngestion:
    def test_from_string(self):
        from src.ingestion import ClinicalNote
        note = ClinicalNote.from_string("Patient has hypertension and diabetes.")
        assert note.word_count == 5
        assert note.note_id.startswith("note_")

    def test_from_file(self):
        from src.ingestion import ClinicalNote
        note = ClinicalNote.from_file(SAMPLE_NOTE)
        assert note.word_count > 100
        assert "heart failure" in note.normalized_text.lower()

    def test_missing_file_raises(self):
        from src.ingestion import ClinicalNote
        with pytest.raises(FileNotFoundError):
            ClinicalNote.from_file("/nonexistent/path/note.txt")

    def test_normalization_collapses_whitespace(self):
        from src.ingestion import ClinicalNote
        note = ClinicalNote.from_string("Hello   World\n\n\n\nTest")
        assert "   " not in note.normalized_text
        assert note.normalized_text.count("\n\n\n") == 0

    def test_unique_ids_for_different_notes(self):
        from src.ingestion import ClinicalNote
        n1 = ClinicalNote.from_string("Note one")
        n2 = ClinicalNote.from_string("Note two")
        assert n1.note_id != n2.note_id

    def test_same_content_same_id(self):
        from src.ingestion import ClinicalNote
        n1 = ClinicalNote.from_string("Identical note content.")
        n2 = ClinicalNote.from_string("Identical note content.")
        assert n1.note_id == n2.note_id


# ---------------------------------------------------------------------------
# Code retrieval tests
# ---------------------------------------------------------------------------

class TestCodeRetrieval:
    @pytest.fixture(scope="class")
    def retriever(self):
        from src.code_retrieval import CodeRetriever
        return CodeRetriever(
            icd10_path=DATA_DIR / "icd10_codes.json",
            cpt_path=DATA_DIR / "cpt_codes.json",
            top_k=5,
        )

    def test_icd10_search_returns_results(self, retriever):
        results = retriever.search_icd10("hypertension high blood pressure")
        assert len(results) > 0
        assert any("I10" in r["code"] for r in results)

    def test_cpt_search_returns_results(self, retriever):
        results = retriever.search_cpt("office visit established patient")
        assert len(results) > 0
        codes = [r["code"] for r in results]
        assert any(c.startswith("992") for c in codes)

    def test_retrieval_scores_are_normalised(self, retriever):
        results = retriever.search_icd10("diabetes mellitus type 2")
        for r in results:
            assert 0.0 <= r["retrieval_score"] <= 1.0

    def test_results_sorted_by_score(self, retriever):
        results = retriever.search_icd10("heart failure congestive")
        scores = [r["retrieval_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_query_returns_empty(self, retriever):
        results = retriever.search_icd10("")
        assert results == []

    def test_bulk_search_deduplicates(self, retriever):
        queries = ["hypertension", "high blood pressure", "elevated BP"]
        results = retriever.bulk_search_icd10(queries)
        codes = [r["code"] for r in results]
        assert len(codes) == len(set(codes))

    def test_cpt_ecg_retrieval(self, retriever):
        results = retriever.search_cpt("electrocardiogram ECG 12 lead")
        assert any(r["code"] == "93000" for r in results)

    def test_icd10_pneumonia_retrieval(self, retriever):
        results = retriever.search_icd10("pneumonia lung infection")
        assert any(r["code"] == "J18.9" for r in results)


# ---------------------------------------------------------------------------
# Pydantic model tests
# ---------------------------------------------------------------------------

class TestModels:
    def test_diagnosis_code_valid(self):
        from src.models import ConfidenceLevel, DiagnosisCode, EvidenceReference
        code = DiagnosisCode(
            code="I10",
            description="Essential hypertension",
            confidence_score=0.92,
            confidence_level=ConfidenceLevel.HIGH,
            is_primary=True,
            evidence=[
                EvidenceReference(
                    quote="history of hypertension",
                    rationale="Explicit documentation of hypertension",
                )
            ],
        )
        assert code.code == "I10"
        assert code.confidence_level == ConfidenceLevel.HIGH

    def test_procedure_code_valid(self):
        from src.models import ConfidenceLevel, ProcedureCode
        code = ProcedureCode(
            code="93000",
            description="ECG with interpretation",
            confidence_score=0.88,
            confidence_level=ConfidenceLevel.HIGH,
        )
        assert code.code == "93000"

    def test_review_payload_summary(self):
        from datetime import datetime
        from src.models import (
            ConfidenceLevel,
            DiagnosisCode,
            ExtractedFacts,
            ReviewPayload,
            Warning,
            WarningSeverity,
            WarningType,
        )
        payload = ReviewPayload(
            note_id="note_test001",
            processed_at=datetime.utcnow(),
            extracted_facts=ExtractedFacts(chief_complaint="chest pain"),
            diagnosis_codes=[
                DiagnosisCode(
                    code="I10",
                    description="Hypertension",
                    confidence_score=0.9,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            ],
            procedure_codes=[],
            warnings=[
                Warning(
                    type=WarningType.MISSING_INFO,
                    severity=WarningSeverity.INFO,
                    message="Test warning",
                )
            ],
        )
        summary = payload.summary()
        assert "note_test001" in summary
        assert "1 diagnosis codes" in summary
        assert "1 warnings" in summary

    def test_invalid_icd10_code_format(self):
        from pydantic import ValidationError
        from src.models import ConfidenceLevel, DiagnosisCode
        with pytest.raises(ValidationError):
            DiagnosisCode(
                code="INVALID",
                description="Bad code",
                confidence_score=0.5,
                confidence_level=ConfidenceLevel.MEDIUM,
            )

    def test_invalid_cpt_code_format(self):
        from pydantic import ValidationError
        from src.models import ConfidenceLevel, ProcedureCode
        with pytest.raises(ValidationError):
            ProcedureCode(
                code="ABCDE",
                description="Bad CPT",
                confidence_score=0.5,
                confidence_level=ConfidenceLevel.MEDIUM,
            )


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidation:
    def _make_dx(self, code: str, is_primary: bool = False, confidence: float = 0.85):
        from src.models import ConfidenceLevel, DiagnosisCode
        level = (
            ConfidenceLevel.HIGH if confidence >= 0.8
            else ConfidenceLevel.MEDIUM if confidence >= 0.5
            else ConfidenceLevel.LOW
        )
        return DiagnosisCode(
            code=code,
            description=f"Description for {code}",
            confidence_score=confidence,
            confidence_level=level,
            is_primary=is_primary,
        )

    def _make_px(self, code: str, confidence: float = 0.85):
        from src.models import ConfidenceLevel, ProcedureCode
        level = ConfidenceLevel.HIGH if confidence >= 0.8 else ConfidenceLevel.MEDIUM
        return ProcedureCode(
            code=code,
            description=f"Description for {code}",
            confidence_score=confidence,
            confidence_level=level,
        )

    def test_no_primary_diagnosis_triggers_warning(self):
        from src.models import ExtractedFacts, WarningSeverity
        from src.validation import validate
        facts = ExtractedFacts()
        dx = [self._make_dx("I10", is_primary=False)]
        warnings = validate(facts, dx, [])
        assert any(w.severity == WarningSeverity.WARNING for w in warnings)

    def test_conflict_detection(self):
        from src.models import ExtractedFacts, WarningSeverity, WarningType
        from src.validation import validate
        facts = ExtractedFacts()
        dx = [
            self._make_dx("E11.9", is_primary=True),
            self._make_dx("E10.9"),
        ]
        warnings = validate(facts, dx, [])
        conflict_warnings = [w for w in warnings if w.type == WarningType.CONFLICT]
        assert len(conflict_warnings) > 0
        assert any(w.severity == WarningSeverity.ERROR for w in conflict_warnings)

    def test_low_confidence_triggers_warning(self):
        from src.models import ExtractedFacts, WarningSeverity
        from src.validation import validate
        facts = ExtractedFacts()
        dx = [self._make_dx("I10", is_primary=True, confidence=0.3)]
        warnings = validate(facts, dx, [])
        assert any(w.severity == WarningSeverity.WARNING for w in warnings)

    def test_high_risk_code_triggers_warning(self):
        from src.models import ExtractedFacts
        from src.validation import validate
        facts = ExtractedFacts()
        dx = [self._make_dx("I21.9", is_primary=True)]
        warnings = validate(facts, dx, [])
        assert any("I21.9" in w.related_codes for w in warnings)

    def test_clean_coding_no_errors(self):
        from src.models import ExtractedFacts, WarningSeverity
        from src.validation import validate
        facts = ExtractedFacts(chief_complaint="hypertension follow-up")
        dx = [self._make_dx("I10", is_primary=True, confidence=0.92)]
        px = [self._make_px("99213", confidence=0.88)]
        # Provide evidence manually
        dx[0].evidence.append(
            __import__("src.models", fromlist=["EvidenceReference"]).EvidenceReference(
                quote="history of hypertension", rationale="Explicit diagnosis"
            )
        )
        px[0].evidence.append(
            __import__("src.models", fromlist=["EvidenceReference"]).EvidenceReference(
                quote="established patient office visit", rationale="E&M documentation"
            )
        )
        warnings = validate(facts, dx, px)
        errors = [w for w in warnings if w.severity == WarningSeverity.ERROR]
        assert len(errors) == 0

    def test_review_priority_urgent_on_errors(self):
        from src.models import ExtractedFacts
        from src.validation import determine_review_priority, validate
        facts = ExtractedFacts()
        # Conflict pair triggers ERROR
        dx = [
            self._make_dx("E11.9", is_primary=True),
            self._make_dx("E10.9"),
        ]
        warnings = validate(facts, dx, [])
        priority = determine_review_priority(warnings, dx)
        assert priority == "urgent"


# ---------------------------------------------------------------------------
# End-to-end pipeline test (mocked LLM)
# ---------------------------------------------------------------------------

class TestPipelineMocked:
    MOCK_EXTRACTION = {
        "chief_complaint": "shortness of breath and leg swelling",
        "diagnoses_mentioned": [
            "chronic systolic heart failure",
            "hypertension",
            "type 2 diabetes mellitus",
        ],
        "symptoms_signs": ["dyspnea on exertion", "bilateral pitting edema", "orthopnea"],
        "procedures_mentioned": ["ECG", "chest X-ray", "BMP"],
        "medications": ["furosemide", "carvedilol", "metformin", "insulin glargine"],
        "lab_imaging_results": [
            "BNP 980 pg/mL elevated",
            "creatinine 2.1 from baseline 1.8",
            "HbA1c 8.2%",
        ],
        "relevant_history": ["history of CABG 2018", "CKD stage 3", "former smoker"],
        "supporting_quotes": [
            "chronic systolic congestive heart failure exacerbation",
            "BP 152/94 mmHg",
            "HbA1c 8.2%",
        ],
    }

    MOCK_CODING = {
        "diagnosis_codes": [
            {
                "code": "I50.22",
                "description": "Chronic systolic (congestive) heart failure",
                "confidence_score": 0.96,
                "is_primary": True,
                "evidence": [
                    {
                        "quote": "chronic systolic congestive heart failure exacerbation",
                        "rationale": "Explicitly documented as primary diagnosis",
                    }
                ],
            },
            {
                "code": "I10",
                "description": "Essential (primary) hypertension",
                "confidence_score": 0.91,
                "is_primary": False,
                "evidence": [
                    {
                        "quote": "hypertension, BP 152/94 mmHg",
                        "rationale": "Documented history and elevated BP",
                    }
                ],
            },
            {
                "code": "E11.65",
                "description": "Type 2 diabetes mellitus with hyperglycemia",
                "confidence_score": 0.88,
                "is_primary": False,
                "evidence": [
                    {
                        "quote": "glucose 187, HbA1c 8.2%",
                        "rationale": "T2DM with documented hyperglycemia",
                    }
                ],
            },
        ],
        "procedure_codes": [
            {
                "code": "99223",
                "description": "Initial hospital inpatient care, high level medical decision making",
                "confidence_score": 0.90,
                "evidence": [
                    {
                        "quote": "Admit to telemetry for IV diuresis",
                        "rationale": "High-complexity inpatient admission",
                    }
                ],
            },
            {
                "code": "93000",
                "description": "Electrocardiogram, routine ECG with interpretation",
                "confidence_score": 0.93,
                "evidence": [
                    {
                        "quote": "12-lead ECG: Normal sinus rhythm at 88 bpm",
                        "rationale": "ECG performed and interpreted",
                    }
                ],
            },
        ],
    }

    def _make_mock_llm(self):
        """Build a mock LLM client with generate_json returning extraction then coding."""
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = [self.MOCK_EXTRACTION, self.MOCK_CODING]
        mock_llm.model = "mock"
        return mock_llm

    @patch("src.pipeline.create_llm_client")
    def test_full_pipeline_produces_review_payload(self, mock_create_llm):
        from src.ingestion import ClinicalNote
        from src.pipeline import MedicalCodingPipeline

        mock_llm = self._make_mock_llm()
        mock_create_llm.return_value = (mock_llm, "mock")

        pipeline = MedicalCodingPipeline(
            provider="gemini",
            api_key="test-key",
            model="gemini-2.0-flash",
        )
        note = ClinicalNote.from_string(
            "Patient with heart failure, hypertension, and diabetes."
        )
        result = pipeline.process_note(note)

        assert result.note_id == note.note_id
        assert len(result.diagnosis_codes) == 3
        assert len(result.procedure_codes) == 2
        assert any(d.is_primary for d in result.diagnosis_codes)
        assert result.pipeline_version == "1.0.0"
        assert len(result.audit_trail) > 0
        assert result.extracted_facts.chief_complaint is not None

    def test_missing_api_key_raises(self):
        import os
        from src.pipeline import MedicalCodingPipeline

        # Temporarily remove keys from environment
        original_openai = os.environ.pop("OPENAI_API_KEY", None)
        original_google = os.environ.pop("GOOGLE_API_KEY", None)
        original_gemini = os.environ.pop("GEMINI_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="OpenAI API key required"):
                MedicalCodingPipeline(provider="openai")

            with pytest.raises(ValueError, match="Gemini API key required"):
                MedicalCodingPipeline(provider="gemini")
        finally:
            if original_openai:
                os.environ["OPENAI_API_KEY"] = original_openai
            if original_google:
                os.environ["GOOGLE_API_KEY"] = original_google
            if original_gemini:
                os.environ["GEMINI_API_KEY"] = original_gemini
