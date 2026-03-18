"""
LLM abstraction layer: supports OpenAI and Google Gemini.
Provides a unified generate_json() interface for extraction and coding.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Protocol for LLM clients that return JSON."""

    def generate_json(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        """Return parsed JSON dict. Raises on failure."""
        ...


# ---------------------------------------------------------------------------
# OpenAI implementation
# ---------------------------------------------------------------------------

class OpenAILLM:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key)
        self.model = model

    def generate_json(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        return json.loads(raw)


# ---------------------------------------------------------------------------
# Google Gemini implementation
# ---------------------------------------------------------------------------

class GeminiLLM:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self.model = model

    def generate_json(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        import google.generativeai as genai
        # Gemini uses a single prompt; system + user combined
        full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"
        config = genai.types.GenerationConfig(
            temperature=0.0,
            response_mime_type="application/json",
        )
        response = self._model.generate_content(
            full_prompt,
            generation_config=config,
        )
        raw = response.text
        if not raw:
            raise ValueError("Gemini returned empty response")
        return json.loads(raw)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_llm_client(
    provider: str,
    api_key: str | None = None,
    model: str | None = None,
) -> tuple[LLMClient, str]:
    """
    Create an LLM client for the given provider.

    Returns
    -------
    (client, model_name)
    """
    provider = provider.lower()
    if provider == "openai":
        key = api_key or __import__("os").environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass api_key.")
        model_name = model or "gpt-4o"
        return OpenAILLM(api_key=key, model=model_name), model_name

    if provider == "gemini":
        key = api_key or __import__("os").environ.get("GOOGLE_API_KEY") or __import__("os").environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("Gemini API key required. Set GOOGLE_API_KEY or GEMINI_API_KEY or pass api_key.")
        model_name = model or "gemini-2.0-flash"
        return GeminiLLM(api_key=key, model=model_name), model_name

    raise ValueError(f"Unknown provider: {provider}. Use 'openai' or 'gemini'.")
