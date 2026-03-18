# medicalcoding

# Medical Coding System

AI-assisted pipeline that reviews clinical notes and produces structured ICD-10-CM
diagnosis and CPT procedure code suggestions with confidence scores, evidence
references, and reviewer-ready warnings.

---

## Architecture Overview

```
Clinical Note (text)
       │
       ▼
  [Ingestion]          Normalise text, generate note_id
       │
       ▼
  [Extraction]         LLM call 1 — extract structured medical facts
  (gpt-4o)             (diagnoses, symptoms, procedures, medications, labs)
       │
       ▼
  [Code Retrieval]     TF-IDF search → top-K ICD-10 + CPT candidates
  (scikit-learn)       Narrows ~150 demo codes (tens of thousands in production)
       │
       ▼
  [Code Assignment]    LLM call 2 — select codes, assign confidence scores,
  (gpt-4o)             attach verbatim evidence quotes from the note
       │
       ▼
  [Validation]         Rule-based checks: conflicts, low confidence,
  (rule engine)        missing procedures, high-risk flags
       │
       ▼
  [ReviewPayload]      Structured JSON with full audit trail
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- **Gemini** (default): Google AI API key from [Google AI Studio](https://aistudio.google.com/apikey)
- **OpenAI** (optional): OpenAI API key
- Node.js 18+ (for the reviewer UI in `frontend/`)

### Deploy (Vercel)

This repository is a monorepo:

- **Frontend**: `frontend/` (Next.js) — deploy to Vercel
- **Backend**: `backend/` (FastAPI) — deploy to Render/Railway/etc.

If Vercel auto-detects Python at the repo root, this repo includes a root `vercel.json`
that forces Vercel to build the Next.js app in `frontend/`.

### Local Setup

```bash
# 1. Clone / navigate to the project
cd medical-coding-system

# 2. Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key (Gemini is the default provider)
# Windows PowerShell:
$env:GOOGLE_API_KEY="your-gemini-api-key"
# Or copy .env.example to .env and set GOOGLE_API_KEY or GEMINI_API_KEY

# 5. Run on the sample note (uses Gemini by default)
python main.py --input examples/sample_note.txt --output output.json --pretty

# To use OpenAI instead:
$env:OPENAI_API_KEY="sk-..."
python main.py --provider openai --input examples/sample_note.txt --output output.json --pretty
```

## CLI Reference

```
python main.py [OPTIONS]

Options:
  --input FILE      Path to clinical note text file
  --text TEXT       Inline clinical note text (alternative to --input)
  --output FILE     Write JSON result here (default: stdout)
  --provider P      LLM provider: gemini (default) or openai
  --model MODEL     Model name (default: gemini-2.0-flash for gemini, gpt-4o for openai)
  --top-k N         Retrieval candidates per concept (default: 10)
  --pretty          Pretty-print JSON output
  --log-level LVL   DEBUG | INFO | WARNING | ERROR (default: INFO)
  --log-dir DIR     Rotating log file directory (default: logs/)
```

---

## Output Format

The pipeline emits a `ReviewPayload` JSON object:

```json
{
  "note_id": "note_abc123def456",
  "processed_at": "2026-03-18T14:32:00Z",
  "note_word_count": 487,
  "extracted_facts": {
    "chief_complaint": "Progressive shortness of breath and leg swelling",
    "diagnoses_mentioned": ["acute decompensated heart failure", ...],
    ...
  },
  "diagnosis_codes": [
    {
      "code": "I50.22",
      "description": "Chronic systolic (congestive) heart failure",
      "confidence_score": 0.95,
      "confidence_level": "high",
      "is_primary": true,
      "evidence": [
        {
          "quote": "chronic systolic congestive heart failure exacerbation — primary diagnosis",
          "rationale": "Explicit documentation of chronic systolic CHF as primary diagnosis"
        }
      ]
    }
  ],
  "procedure_codes": [...],
  "warnings": [
    {
      "type": "documentation_gap",
      "severity": "warning",
      "message": "High-risk diagnosis I50.22 detected...",
      "related_codes": ["I50.22"]
    }
  ],
  "requires_human_review": true,
  "review_priority": "urgent",
  "pipeline_version": "1.0.0",
  "model_used": "gpt-4o",
  "audit_trail": [
    "[2026-03-18T14:32:00Z] Pipeline started: note_id=...",
    ...
  ]
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Generating the Architecture PDF

```bash
python generate_pdf.py
# Writes: docs/architecture.pdf
```

---

## Project Structure

```
medical-coding-system/
├── main.py                  # CLI entry point
├── generate_pdf.py          # Architecture PDF generator
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── models.py            # Pydantic data models
│   ├── ingestion.py         # Note loading + normalisation
│   ├── extraction.py        # LLM fact extraction (call 1)
│   ├── code_retrieval.py    # TF-IDF candidate retrieval
│   ├── coding.py            # LLM code assignment (call 2)
│   ├── validation.py        # Rule-based warning generation
│   ├── pipeline.py          # Orchestrator
│   └── audit.py             # Structured logging
├── data/
│   ├── icd10_codes.json     # ICD-10-CM code database (subset)
│   └── cpt_codes.json       # CPT code database (subset)
├── examples/
│   └── sample_note.txt      # Demo clinical note
├── tests/
│   └── test_pipeline.py
├── logs/                    # Rotating audit logs
└── docs/
    └── architecture.pdf     # Architecture document
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Two-stage LLM pipeline | Separation of concerns: extraction vs. selection improves accuracy and debuggability |
| TF-IDF pre-filtering | Reduces LLM context from ~150K+ tokens (all codes) to ~500 tokens; cost-effective and fast |
| JSON mode + temperature=0 | Deterministic, structured LLM output for reproducibility |
| Pydantic models throughout | Schema validation at every boundary; prevents malformed data propagating |
| Rule-based validation | Fast, deterministic, auditable conflict detection without LLM costs |
| Rotating file logging | Every pipeline run is permanently auditable in `logs/pipeline.log` |

---

## Limitations

- Code database is a representative subset (~150 ICD-10, ~80 CPT). Production use requires the full CMS datasets.
- Confidence scores reflect documentation quality as interpreted by the LLM; they are advisory, not definitive.
- The system does not perform claim scrubbing (NCCI edits, modifier logic).
- Multi-note batch processing and FHIR ingestion are not yet implemented.

---
