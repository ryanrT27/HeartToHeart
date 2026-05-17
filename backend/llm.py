"""Groq LLM client for biomarker extraction."""

import json
import logging
import os
import time
from typing import Any

from groq import Groq

from backend.schema import LAB_REPORT_PROMPT, validate_response

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set")
        _client = Groq(api_key=key)
    return _client


def extract_biomarkers(anonymized_text: str) -> dict[str, Any]:
    """Run LLM extraction. Returns validated schema dict or raises."""
    client = _get_client()

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": LAB_REPORT_PROMPT},
                    {"role": "user", "content": anonymized_text},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = resp.choices[0].message.content
            if not content:
                continue

            parsed = json.loads(content)
            validated = validate_response(parsed)
            if validated is None:
                raise ValueError("LLM response does not match schema")
            return validated

        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}") from e
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                if model == PRIMARY_MODEL:
                    logger.warning("70B rate-limited, falling back to 8B")
                    time.sleep(2)
                    continue
            raise

    raise RuntimeError("Both models rate-limited")
