#!/usr/bin/env python3
"""
CLI entry point for the Medical Coding Pipeline.

Usage
-----
# Process a single file
python main.py --input examples/sample_note.txt --output output.json

# Process inline text (for testing)
python main.py --text "Patient presents with chest pain and shortness of breath."

# Use a different model
python main.py --input note.txt --model gpt-4o-mini --output result.json

# Pretty-print to stdout
python main.py --input note.txt --pretty
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)

from src.audit import configure_logging
from src.pipeline import MedicalCodingPipeline


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="medical-coder",
        description="AI-assisted ICD-10 / CPT coding pipeline for clinical notes.",
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--input", "-i",
        metavar="FILE",
        help="Path to clinical note text file.",
    )
    source.add_argument(
        "--text", "-t",
        metavar="TEXT",
        help="Clinical note text provided directly on the command line.",
    )

    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Write JSON result to this file (default: stdout).",
    )
    parser.add_argument(
        "--provider",
        default="gemini",
        choices=["openai", "gemini"],
        help="LLM provider (default: gemini).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (default: gemini-2.0-flash for gemini, gpt-4o for openai).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        dest="top_k",
        help="Number of candidate codes per concept (default: 10).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output (indent=2).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        dest="log_level",
        help="Logging verbosity (default: INFO).",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        dest="log_dir",
        help="Directory for rotating log files (default: logs/).",
    )

    return parser.parse_args(argv)

def _print_actionable_openai_error(exc: Exception) -> None:
    """
    Print a short, actionable error message for common OpenAI failures.
    Keeps secrets out of stdout/stderr while the logs retain full context.
    """
    msg = str(exc)

    # Most common: quota exhausted (429 insufficient_quota)
    if isinstance(exc, RateLimitError) and ("insufficient_quota" in msg or "quota" in msg.lower()):
        print(
            "ERROR: OpenAI quota exceeded (HTTP 429: insufficient_quota).\n"
            "- Verify billing is enabled and you have available credits.\n"
            "- If you're using a restricted project key, ensure it has access to the selected model.\n"
            "- Try a cheaper model: `--model gpt-4o-mini`.\n"
            "- Retry after a short delay if you recently changed billing settings.",
            file=sys.stderr,
        )
        return

    # Rate limits (429) but not quota (requests/minute)
    if isinstance(exc, RateLimitError):
        print(
            "ERROR: OpenAI rate limit hit (HTTP 429).\n"
            "- Wait a few seconds and retry.\n"
            "- Reduce parallel requests (this app already runs serially).\n"
            "- Consider a smaller model or lower throughput usage.",
            file=sys.stderr,
        )
        return

    if isinstance(exc, AuthenticationError):
        print(
            "ERROR: OpenAI authentication failed (HTTP 401/403).\n"
            "- Confirm `OPENAI_API_KEY` is set and valid.\n"
            "- If you rotated/revoked the key, update your environment and retry.\n"
            "- Ensure the key belongs to the correct organization/project.",
            file=sys.stderr,
        )
        return

    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        print(
            "ERROR: Network issue contacting OpenAI (connection/timeout).\n"
            "- Check internet connectivity and corporate proxy/VPN settings.\n"
            "- Retry in a minute.\n"
            "- If persistent, try again with a smaller note or different network.",
            file=sys.stderr,
        )
        return

    # Fallback: safe generic message
    print(f"ERROR: {exc}", file=sys.stderr)


def _print_gemini_error_feedback(exc: Exception) -> None:
    """
    Identify what went wrong with the Gemini API key/request,
    then print clear feedback.
    """
    err = str(exc).lower()
    msg = str(exc)

    # ── 1. What went wrong ─────────────────────────────────────────────
    print("\n--- What went wrong ---", file=sys.stderr)

    if "limit: 0" in msg and "quota" in err:
        print(
            "Your API key is valid, but the project has zero remaining quota.\n"
            "The free tier for this model shows 'limit: 0' — either the daily\n"
            "or per-minute allowance is exhausted, or billing is not enabled.",
            file=sys.stderr,
        )
    elif "429" in msg and ("quota" in err or "resourceexhausted" in err):
        print(
            "The Gemini API rejected the request due to quota or rate limits (HTTP 429).\n"
            "Your key works, but the project has hit its request/token limits.",
            file=sys.stderr,
        )
    elif "404" in msg or "not found" in msg:
        print(
            "The model name is not available for this API version.\n"
            "The key may be valid, but the requested model does not exist or was deprecated.",
            file=sys.stderr,
        )
    elif "400" in msg or "401" in msg or "403" in msg or "api_key_invalid" in err or "api key not valid" in err:
        print(
            "The API key is invalid, expired, or revoked.\n"
            "Authentication failed — the key was rejected by Google.",
            file=sys.stderr,
        )
    elif "permission" in err or "forbidden" in err:
        print(
            "Permission denied. The key may be valid but lacks access to this model or project.",
            file=sys.stderr,
        )
    else:
        print(f"An unexpected API error occurred: {msg[:200]}", file=sys.stderr)

    # ── 2. What to do ──────────────────────────────────────────────────
    print("\n--- What to do ---", file=sys.stderr)

    if "limit: 0" in msg and "quota" in err:
        print(
            "- Enable billing in Google AI Studio: https://aistudio.google.com/\n"
            "- Check usage and limits: https://ai.dev/rate-limit\n"
            "- Try a different model: --model gemini-2.5-flash-lite\n"
            "- Wait for the free-tier quota to reset (often daily)",
            file=sys.stderr,
        )
    elif "429" in msg and "quota" in err:
        print(
            "- Wait a minute and retry (rate limits reset quickly)\n"
            "- Check usage: https://ai.dev/rate-limit\n"
            "- Enable billing for higher limits",
            file=sys.stderr,
        )
    elif "404" in msg or "not found" in msg:
        print(
            "- Use a supported model: --model gemini-2.0-flash or --model gemini-2.5-flash\n"
            "- See available models: https://ai.google.dev/gemini-api/docs/models",
            file=sys.stderr,
        )
    elif "400" in msg or "401" in msg or "403" in msg or "api_key_invalid" in err or "api key not valid" in err:
        print(
            "- Create a new API key at https://aistudio.google.com/apikey\n"
            "- Set it: $env:GOOGLE_API_KEY=\"your-key\"\n"
            "- Ensure the key has not been revoked or restricted",
            file=sys.stderr,
        )
    else:
        print(
            "- Check https://ai.google.dev/gemini-api/docs for status and docs\n"
            "- Retry after a short delay\n"
            "- Run with --log-level DEBUG for full error details",
            file=sys.stderr,
        )
    print(file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    configure_logging(log_dir=args.log_dir, level=getattr(logging, args.log_level))
    logger = logging.getLogger("main")

    model = args.model or ("gemini-2.0-flash" if args.provider == "gemini" else "gpt-4o")
    logger.info("Medical Coding Pipeline starting")
    logger.info("Provider: %s  |  Model: %s  |  Top-K: %d", args.provider, model, args.top_k)

    try:
        pipeline = MedicalCodingPipeline(
            provider=args.provider,
            model=model,
            top_k_candidates=args.top_k,
        )
    except ValueError as exc:
        logger.error("Initialisation failed: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        if args.input:
            logger.info("Processing file: %s", args.input)
            result = pipeline.process_file(args.input)
        else:
            logger.info("Processing inline text (%d chars)", len(args.text))
            result = pipeline.process_text(args.text)
    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except OpenAIError as exc:
        # OpenAI-specific error handling (only when provider=openai).
        if args.log_level == "DEBUG":
            logger.exception("OpenAI API error: %s", exc)
        else:
            logger.error("OpenAI API error: %s", exc)
        _print_actionable_openai_error(exc)
        return 1
    except ValueError as exc:
        if "API key" in str(exc) or "api_key" in str(exc).lower():
            logger.error("API key error: %s", exc)
            key_hint = "GOOGLE_API_KEY or GEMINI_API_KEY" if args.provider == "gemini" else "OPENAI_API_KEY"
            print(f"ERROR: {exc}\nSet {key_hint} environment variable.", file=sys.stderr)
        else:
            logger.exception("Pipeline error: %s", exc)
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        err_str = str(exc)
        # Gemini / Google API errors — identify cause and give feedback
        if (any(x in err_str for x in ("429", "404", "401", "403", "400"))
            or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower()
            or "api_key_invalid" in err_str.lower() or "api key not valid" in err_str.lower()):
            logger.error("Gemini API error: %s", exc)
            print("ERROR: Gemini API request failed.", file=sys.stderr)
            _print_gemini_error_feedback(exc)
            return 1
        logger.exception("Pipeline error: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Serialise result
    indent = 2 if args.pretty else None
    json_output = result.model_dump_json(indent=indent)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(json_output, encoding="utf-8")
        logger.info("Result written to %s", out_path)
        print(f"Result written to: {out_path}")
        print(result.summary())
    else:
        print(json_output)

    # Return non-zero if urgent review needed (useful for CI/CD gating)
    if result.review_priority == "urgent":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
