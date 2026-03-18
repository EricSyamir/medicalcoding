#!/usr/bin/env python3
"""
Generate the architecture PDF document (1-2 pages).
Writes to docs/architecture.pdf.

Usage:
    python generate_pdf.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

BASE = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "DocTitle",
    parent=BASE["Title"],
    fontSize=16,
    leading=20,
    alignment=TA_CENTER,
    spaceAfter=4,
)
SUBTITLE_STYLE = ParagraphStyle(
    "DocSubtitle",
    parent=BASE["Normal"],
    fontSize=10,
    leading=13,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#555555"),
    spaceAfter=14,
)
H1_STYLE = ParagraphStyle(
    "H1",
    parent=BASE["Heading1"],
    fontSize=12,
    leading=15,
    textColor=colors.HexColor("#1a3a5c"),
    spaceBefore=10,
    spaceAfter=4,
)
BODY_STYLE = ParagraphStyle(
    "Body",
    parent=BASE["Normal"],
    fontSize=9,
    leading=13,
    spaceAfter=4,
)
BULLET_STYLE = ParagraphStyle(
    "Bullet",
    parent=BASE["Normal"],
    fontSize=9,
    leading=12,
    leftIndent=14,
    bulletIndent=4,
    spaceAfter=2,
)
MONO_STYLE = ParagraphStyle(
    "Mono",
    parent=BASE["Code"],
    fontSize=8,
    leading=11,
    leftIndent=14,
    textColor=colors.HexColor("#2e4057"),
)

ACCENT = colors.HexColor("#1a3a5c")
LIGHT = colors.HexColor("#e8eef5")


def hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=ACCENT, spaceAfter=6, spaceBefore=2)


def h1(text: str) -> Paragraph:
    return Paragraph(text, H1_STYLE)


def body(text: str) -> Paragraph:
    return Paragraph(text, BODY_STYLE)


def bullet(text: str) -> Paragraph:
    return Paragraph(f"• {text}", BULLET_STYLE)


def mono(text: str) -> Paragraph:
    return Paragraph(text, MONO_STYLE)


def sp(height: float = 6) -> Spacer:
    return Spacer(1, height)


# ---------------------------------------------------------------------------
# Main content builder
# ---------------------------------------------------------------------------

def build_content() -> list:
    story = []

    # ── Title block ─────────────────────────────────────────────────────────
    story.append(Paragraph("Medical Coding Pipeline", TITLE_STYLE))
    story.append(Paragraph(
        "Architecture & Design Document  ·  v1.0.0  ·  March 2026",
        SUBTITLE_STYLE,
    ))
    story.append(hr())

    # ── 1. Overall Architecture & Data Flow ─────────────────────────────────
    story.append(h1("1. Overall Architecture & Data Flow"))
    story.append(body(
        "The pipeline converts an unstructured clinical note into a structured, "
        "reviewer-ready payload containing ICD-10-CM diagnosis codes and CPT procedure "
        "codes with confidence scores, verbatim evidence references, and warnings."
    ))
    story.append(sp(4))

    # Pipeline flow table
    flow_data = [
        ["Stage", "Component", "Output"],
        ["1 – Ingestion", "ingestion.py", "Normalised text + note_id (SHA-256)"],
        ["2 – Extraction", "extraction.py (LLM call 1)", "ExtractedFacts (JSON via gpt-4o)"],
        ["3 – Retrieval", "code_retrieval.py (TF-IDF)", "Top-K ICD-10 + CPT candidates"],
        ["4 – Coding", "coding.py (LLM call 2)", "Scored DiagnosisCode + ProcedureCode"],
        ["5 – Validation", "validation.py (rule engine)", "Warning list, review priority"],
        ["6 – Output", "models.py (Pydantic)", "ReviewPayload JSON (audit trail)"],
    ]
    col_w = [1.2 * inch, 1.9 * inch, 3.1 * inch]
    tbl = Table(flow_data, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#aaaaaa")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(sp(6))

    # ── 2. Code Retrieval / Filtering Strategy ───────────────────────────────
    story.append(h1("2. Code Retrieval & Filtering Strategy"))
    story.append(body(
        "ICD-10-CM contains ~72,000 codes; CPT contains ~10,000. Passing all codes "
        "to an LLM in a single prompt is cost-prohibitive and degrades accuracy. "
        "A two-stage filtering approach is used:"
    ))
    story.append(bullet(
        "<b>Stage A – TF-IDF index (offline):</b> Each code is indexed by its code string, "
        "description, and synonym keywords using a bigram TF-IDF vectoriser "
        "(scikit-learn). The index is built once at pipeline startup."
    ))
    story.append(bullet(
        "<b>Stage B – Per-concept query (online):</b> Each extracted clinical concept "
        "(diagnosis, symptom, procedure) is vectorised and cosine-similarity ranked "
        "against the index. The top-K results (default K=10) are selected per query; "
        "a bulk-search pass deduplicates across all concepts."
    ))
    story.append(bullet(
        "<b>Result:</b> The LLM receives ~20–50 candidate codes per note instead of "
        "thousands, reducing prompt token cost by >99% while maintaining high recall "
        "for documented conditions."
    ))
    story.append(sp(4))

    # ── 3. LLM Usage & Prompting Approach ───────────────────────────────────
    story.append(h1("3. LLM Usage & Prompting Approach"))
    story.append(body(
        "Two specialised LLM calls are made per note, each with "
        "<b>temperature=0</b> for determinism and <b>JSON mode</b> for structured output:"
    ))
    story.append(bullet(
        "<b>Call 1 – Fact Extraction:</b> A system prompt positions the LLM as a "
        "'senior clinical documentation specialist.' The prompt requests a structured "
        "JSON object (chief complaint, diagnoses, symptoms, procedures, medications, "
        "lab results, history, supporting quotes). Strict schema enforcement prevents "
        "hallucination beyond the documented content."
    ))
    story.append(bullet(
        "<b>Call 2 – Code Assignment:</b> A system prompt positions the LLM as a "
        "'CPC-certified coder with 15 years experience.' The prompt injects extracted "
        "facts, candidate codes from retrieval, and an excerpt of the original note. "
        "The LLM selects codes <i>only</i> from the candidate list, assigns confidence "
        "scores (0.0–1.0) using documented criteria, designates a primary diagnosis, "
        "and attaches verbatim quote evidence for each code."
    ))
    story.append(bullet(
        "<b>Model:</b> gpt-4o (default). Any OpenAI-compatible endpoint can be "
        "substituted via the --model flag. gpt-4o-mini reduces cost for lower-stakes "
        "or batch use cases."
    ))
    story.append(sp(4))

    # ── 4. Key Technical Decisions & Trade-offs ──────────────────────────────
    story.append(h1("4. Key Technical Decisions & Trade-offs"))

    decisions = [
        ["Decision", "Choice", "Trade-off"],
        ["Code search", "TF-IDF (lexical)",
         "Fast, zero-cost, interpretable. Misses semantic synonyms "
         "— mitigated by keyword augmentation per code."],
        ["LLM calls", "Two-stage (extract then code)",
         "Higher latency vs. single call. Improves accuracy and "
         "debuggability; each stage can be independently tested."],
        ["Structured output", "JSON mode + Pydantic",
         "Eliminates parsing fragility; schema validation at every "
         "boundary guarantees downstream safety."],
        ["Validation", "Rule-based (no LLM)",
         "Deterministic, auditable, zero additional API cost. "
         "Cannot catch all clinical edge cases."],
        ["Code DB", "Local JSON (subset)",
         "Simple, portable, version-controllable. Production requires "
         "full CMS datasets and automated update pipeline."],
        ["Temperature", "0.0 (deterministic)",
         "Same note always produces same output — essential for "
         "audits. Forfeits creative coverage of edge cases."],
    ]
    col_w2 = [1.1 * inch, 1.3 * inch, 3.8 * inch]
    tbl2 = Table(decisions, colWidths=col_w2)
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#aaaaaa")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("WORDWRAP", (0, 0), (-1, -1), True),
    ]))
    story.append(tbl2)
    story.append(sp(6))

    # ── 5. Limitations & Possible Extensions ─────────────────────────────────
    story.append(h1("5. Limitations & Possible Extensions"))

    story.append(body("<b>Current Limitations:</b>"))
    story.append(bullet(
        "Code database is a curated ~150-code demonstration subset; "
        "production requires the full annual CMS ICD-10-CM and AMA CPT releases."
    ))
    story.append(bullet(
        "No claim-scrubbing logic (NCCI edits, modifier rules, bundling/unbundling). "
        "A dedicated scrubber layer must be added before payer submission."
    ))
    story.append(bullet(
        "Confidence scores are LLM-generated estimates, not calibrated probabilities. "
        "They should be treated as advisory signals, not ground-truth certainty."
    ))
    story.append(bullet(
        "Single-note, synchronous processing only. Bulk ingestion and async "
        "processing are not yet implemented."
    ))
    story.append(bullet(
        "No FHIR / HL7 integration; input is plain text. Real EHRs require "
        "a structured-to-text conversion or native FHIR parsing layer."
    ))
    story.append(sp(4))

    story.append(body("<b>Possible Extensions:</b>"))
    story.append(bullet(
        "<b>Semantic retrieval:</b> Replace TF-IDF with a dense embedding index "
        "(e.g., OpenAI embeddings + FAISS) for better synonym matching."
    ))
    story.append(bullet(
        "<b>Fine-tuned coding model:</b> Fine-tune an open-source LLM on "
        "labelled coding datasets (MIMIC-III, CMS synthetic data) to reduce "
        "API dependency and improve domain accuracy."
    ))
    story.append(bullet(
        "<b>Human-in-the-loop feedback loop:</b> Capture reviewer overrides, "
        "feed them back as few-shot examples to continuously improve the prompts."
    ))
    story.append(bullet(
        "<b>Batch pipeline:</b> Wrap the pipeline in Apache Airflow or Prefect "
        "for high-volume, parallelised note processing with retry logic."
    ))
    story.append(bullet(
        "<b>REST API:</b> Expose the pipeline via FastAPI with OAuth2 for "
        "integration with EHR systems and third-party billing platforms."
    ))
    story.append(bullet(
        "<b>Audit database:</b> Persist ReviewPayload objects to PostgreSQL "
        "for longitudinal analytics, compliance reporting, and model evaluation."
    ))

    story.append(sp(8))
    story.append(hr())
    story.append(Paragraph(
        "medical-coding-system v1.0.0  ·  github.com/your-org/medical-coding-system  ·  MIT License",
        ParagraphStyle("footer", parent=BASE["Normal"], fontSize=7,
                       textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
    ))

    return story


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    out_dir = Path(__file__).parent / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "architecture.pdf"

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(build_content())
    print(f"PDF written to: {out_path}")


if __name__ == "__main__":
    main()
