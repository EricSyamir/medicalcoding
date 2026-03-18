"""
FastAPI backend — exposes the medical coding pipeline as an HTTP API.
Deploy to Render, Railway, or any container host.
"""

from __future__ import annotations

import os
import sys

# Allow imports from the project root (src/, data/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.audit import configure_logging
from src.pipeline import MedicalCodingPipeline

configure_logging(log_dir="logs")

app = FastAPI(
    title="Medical Coding API",
    description="AI-assisted ICD-10/CPT coding pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRequest(BaseModel):
    note_text: str
    provider: str = "gemini"
    model: str | None = None
    api_key: str | None = None  # optional: overrides server env key


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/process")
async def process_note(req: ProcessRequest):
    if not req.note_text.strip():
        raise HTTPException(status_code=400, detail="note_text is required and must not be empty.")

    try:
        pipeline = MedicalCodingPipeline(
            provider=req.provider,
            api_key=req.api_key or None,
            model=req.model or None,
        )
        result = pipeline.process_text(req.note_text)
        return result.model_dump(mode="json")

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        err = str(exc)
        if "429" in err or "quota" in err.lower() or "resourceexhausted" in err.lower():
            raise HTTPException(
                status_code=429,
                detail="API quota exceeded. Check your plan and billing, then retry.",
            )
        if "400" in err or "api_key_invalid" in err.lower() or "api key not valid" in err.lower():
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Please provide a valid key.",
            )
        raise HTTPException(status_code=500, detail=f"Pipeline error: {err[:300]}")
