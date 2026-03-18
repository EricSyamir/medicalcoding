"""
Code retrieval layer.

Uses TF-IDF over code descriptions + keyword fields to narrow the search space
from tens of thousands of codes down to a small set of candidates per concept.
This pre-filtering reduces LLM context size and cost while maintaining recall.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class CodeRetriever:
    """
    TF-IDF-based retrieval index for ICD-10-CM and CPT codes.

    Strategy
    --------
    Each code is indexed by concatenating its code string, description, and any
    keyword synonyms.  Queries (extracted medical concepts) are vectorised with
    the same vocabulary, and cosine similarity selects the top-K candidates.
    A minimum similarity threshold prunes irrelevant results.
    """

    MIN_SCORE = 0.05

    def __init__(
        self,
        icd10_path: str | Path,
        cpt_path: str | Path,
        top_k: int = 10,
    ) -> None:
        self.top_k = top_k
        self.icd10_codes: list[dict] = self._load(icd10_path)
        self.cpt_codes: list[dict] = self._load(cpt_path)

        logger.info(
            "Building TF-IDF indexes: %d ICD-10 codes, %d CPT codes",
            len(self.icd10_codes),
            len(self.cpt_codes),
        )
        self._icd10_vec, self._icd10_mat = self._build_index(self.icd10_codes)
        self._cpt_vec, self._cpt_mat = self._build_index(self.cpt_codes)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_icd10(self, query: str, top_k: int | None = None) -> list[dict]:
        """Return top-K ICD-10 candidates for a free-text medical concept."""
        return self._search(query, self._icd10_vec, self._icd10_mat, self.icd10_codes, top_k)

    def search_cpt(self, query: str, top_k: int | None = None) -> list[dict]:
        """Return top-K CPT candidates for a free-text procedural concept."""
        return self._search(query, self._cpt_vec, self._cpt_mat, self.cpt_codes, top_k)

    def bulk_search_icd10(self, queries: list[str]) -> list[dict]:
        """Deduplicated union of ICD-10 results across multiple queries."""
        return self._bulk_search(queries, self.search_icd10)

    def bulk_search_cpt(self, queries: list[str]) -> list[dict]:
        """Deduplicated union of CPT results across multiple queries."""
        return self._bulk_search(queries, self.search_cpt)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load(path: str | Path) -> list[dict]:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _build_index(codes: list[dict]):
        """Fit a TF-IDF vectoriser over all code documents."""
        docs = [
            " ".join(
                filter(
                    None,
                    [
                        c.get("code", ""),
                        c.get("description", ""),
                        " ".join(c.get("keywords", [])),
                        c.get("category", ""),
                    ],
                )
            )
            for c in codes
        ]
        vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1)
        mat = vec.fit_transform(docs)
        return vec, mat

    def _search(
        self,
        query: str,
        vectoriser: TfidfVectorizer,
        matrix,
        codes: list[dict],
        top_k: int | None,
    ) -> list[dict]:
        if not query.strip():
            return []
        k = top_k or self.top_k
        q_vec = vectoriser.transform([query])
        scores = cosine_similarity(q_vec, matrix).flatten()
        top_idx = np.argsort(scores)[::-1][:k]
        results = []
        for i in top_idx:
            score = float(scores[i])
            if score >= self.MIN_SCORE:
                results.append({**codes[i], "retrieval_score": round(score, 4)})
        return results

    @staticmethod
    def _bulk_search(queries: list[str], search_fn) -> list[dict]:
        seen: set[str] = set()
        merged: list[dict] = []
        for q in queries:
            for item in search_fn(q):
                code = item["code"]
                if code not in seen:
                    seen.add(code)
                    merged.append(item)
        # Re-sort by retrieval_score descending
        merged.sort(key=lambda x: x["retrieval_score"], reverse=True)
        return merged
