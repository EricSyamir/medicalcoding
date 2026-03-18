"""
Ingestion layer: load and preprocess clinical notes from file or string input.
Produces a normalized text representation with basic metadata.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Union


class ClinicalNote:
    """Holds a loaded, normalised clinical note ready for the pipeline."""

    def __init__(self, text: str, source: str = "inline"):
        self.raw_text = text
        self.source = source
        self.note_id = self._generate_id(text)
        self.normalized_text = self._normalize(text)
        self.word_count = len(self.normalized_text.split())

    # ------------------------------------------------------------------
    # Class-level factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "ClinicalNote":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Clinical note not found: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        return cls(text=text, source=str(path))

    @classmethod
    def from_string(cls, text: str) -> "ClinicalNote":
        return cls(text=text.strip(), source="inline")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_id(text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        return f"note_{digest}"

    @staticmethod
    def _normalize(text: str) -> str:
        # Unicode NFC normalisation
        text = unicodedata.normalize("NFC", text)
        # Collapse excessive whitespace while preserving paragraph structure
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def __repr__(self) -> str:
        return f"<ClinicalNote id={self.note_id} words={self.word_count} source={self.source!r}>"
