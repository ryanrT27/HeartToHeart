"""
Maternal/Postpartum Cardiovascular Trials Pipeline (Groq)

Queries ClinicalTrials.gov for studies related to maternal/postpartum cardiovascular
health (configurable overall statuses), then uses Groq-hosted Llama models to:
  1. Parse eligibility criteria into structured JSON
  2. Extract clinical diagnoses, biomarkers, and vital signs (unified schema)

Prerequisites:
    1. Get a Groq API key: https://console.groq.com/keys
    2. Export GROQ_API_KEY or put it in a .env file (python-dotenv).
    3. pip install -r requirements.txt
    4. Run: python pipeline.py

Environment (optional):
    CT_OVERALL_STATUSES — comma-separated Overall Status filters (default includes
        RECRUITING and NOT_YET_RECRUITING for more coverage).
    GROQ_MIN_INTERVAL_SEC — minimum seconds between LLM calls (default 0.85).
    GROQ_PIPELINE_MODEL / GROQ_PIPELINE_FALLBACK_MODEL — override Groq model IDs.

Output: maternal_cardio_trials_parsed.json (resumes from checkpoint automatically).
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from groq import Groq

from biomarker_schema import (
    PIPELINE_BIOMARKER_PROMPT,
    validate_biomarker_response,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CLINICALTRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

SEARCH_TERM = (
    "(postpartum OR pregnant OR maternal OR pregnancy) AND "
    "(cardiovascular OR preeclampsia OR \"peripartum cardiomyopathy\" "
    "OR hypertension OR \"heart failure\")"
)

PAGE_SIZE = 50
CT_SLEEP = 1.0

# Multiple statuses → more trials than RECRUITING-only (dedupe by NCT ID).
CT_OVERALL_STATUSES = [
    s.strip()
    for s in os.environ.get(
        "CT_OVERALL_STATUSES",
        "RECRUITING,NOT_YET_RECRUITING",
    ).split(",")
    if s.strip()
]

GROQ_PRIMARY_MODEL = os.environ.get("GROQ_PIPELINE_MODEL", "llama-3.3-70b-versatile")
GROQ_FALLBACK_MODEL = os.environ.get("GROQ_PIPELINE_FALLBACK_MODEL", "llama-3.1-8b-instant")
GROQ_MIN_INTERVAL_SEC = float(os.environ.get("GROQ_MIN_INTERVAL_SEC", "0.85"))
GROQ_TIMEOUT_SEC = float(os.environ.get("GROQ_TIMEOUT_SEC", "120"))
GROQ_RATE_LIMIT_BACKOFF = float(os.environ.get("GROQ_RATE_LIMIT_BACKOFF_SEC", "4.0"))

OUTPUT_FILE = "maternal_cardio_trials_parsed.json"
CHECKPOINT_EVERY = 10

_groq_client: Groq | None = None
_last_groq_call_monotonic: float = 0.0

# Required keys in the eligibility LLM response.
ELIGIBILITY_EXPECTED_KEYS = {
    "min_age",
    "max_age",
    "requires_postpartum",
    "max_months_postpartum",
    "required_conditions",
    "excluded_conditions",
}

# ---------------------------------------------------------------------------
# LLM system prompt (eligibility)
# ---------------------------------------------------------------------------

ELIGIBILITY_SYSTEM_PROMPT = """\
You are a clinical data extraction specialist. Your task is to read raw eligibility
criteria text from a clinical trial and extract key quantifiable standards that a
patient-matching application can filter against.

Rules:
- Extract ONLY information explicitly stated in the text. Do not infer or assume.
- For ages, convert any stated range (e.g. "18 to 45 years") to integer years.
- requires_postpartum must be true only if the criteria explicitly state the
  participant must be in a postpartum period at enrollment.
- max_months_postpartum must be an integer only when a specific postpartum window
  is given (e.g. "within 6 months postpartum" → 6).
- For required_conditions and excluded_conditions, use lowercase, plain medical terms.
- If a field cannot be determined from the text, use null for scalars and [] for lists.
- Output ONLY a single JSON object with these exact keys:

{
  "min_age": <integer or null>,
  "max_age": <integer or null>,
  "requires_postpartum": <true or false>,
  "max_months_postpartum": <integer or null>,
  "required_conditions": ["<string>", ...],
  "excluded_conditions": ["<string>", ...]
}
"""


# ---------------------------------------------------------------------------
# Groq LLM client (rate-aware)
# ---------------------------------------------------------------------------


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your environment or .env file."
            )
        _groq_client = Groq(api_key=key)
    return _groq_client


def _groq_throttle() -> None:
    """Space out requests to reduce rate-limit / TPM bursts."""
    global _last_groq_call_monotonic
    now = time.monotonic()
    gap = now - _last_groq_call_monotonic
    wait = GROQ_MIN_INTERVAL_SEC - gap
    if wait > 0:
        time.sleep(wait)
    _last_groq_call_monotonic = time.monotonic()


def _call_groq_json(system_prompt: str, user_text: str) -> dict[str, Any] | None:
    """Send a prompt to Groq and return parsed JSON, or None on failure."""
    client = _get_groq()

    for model in (GROQ_PRIMARY_MODEL, GROQ_FALLBACK_MODEL):
        _groq_throttle()
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                timeout=GROQ_TIMEOUT_SEC,
            )
            content = resp.choices[0].message.content
            if not content:
                logger.warning("Groq (%s) returned empty content.", model)
                continue
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Groq (%s) returned invalid JSON: %s", model, exc)
            return None
        except Exception as exc:  # noqa: BLE001
            err = str(exc).lower()
            if "rate" in err or "429" in err or "limit" in err:
                logger.warning(
                    "Groq rate limit on %s — backing off %.1fs then retrying / fallback.",
                    model,
                    GROQ_RATE_LIMIT_BACKOFF,
                )
                time.sleep(GROQ_RATE_LIMIT_BACKOFF)
                if model == GROQ_PRIMARY_MODEL:
                    continue
                return None
            logger.error("Groq request failed (%s): %s", model, exc)
            if model == GROQ_PRIMARY_MODEL:
                continue
            return None

    logger.error("Groq: both models failed for this request.")
    return None


# ---------------------------------------------------------------------------
# Step 1 — Fetch studies from ClinicalTrials.gov v2 API
# ---------------------------------------------------------------------------


def fetch_all_studies() -> list[dict[str, Any]]:
    """Fetch all pages for each configured overall status; dedupe by NCT ID."""
    seen_nct: set[str] = set()
    all_studies: list[dict[str, Any]] = []

    for overall_status in CT_OVERALL_STATUSES:
        page_token: str | None = None
        page_number = 0
        logger.info("Fetching studies with filter.overallStatus=%s", overall_status)

        while True:
            page_number += 1
            params: list[tuple[str, str]] = [
                ("query.term", SEARCH_TERM),
                ("filter.overallStatus", overall_status),
                ("pageSize", str(PAGE_SIZE)),
            ]
            if page_number == 1:
                params.append(("countTotal", "true"))
            if page_token:
                params.append(("pageToken", page_token))

            try:
                response = requests.get(
                    CLINICALTRIALS_BASE_URL, params=params, timeout=30
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                logger.error(
                    "API request failed (%s page %d): %s",
                    overall_status,
                    page_number,
                    exc,
                )
                break

            data = response.json()

            if page_number == 1:
                total = data.get("totalCount", "unknown")
                logger.info(
                    "Total matching studies (%s): %s",
                    overall_status,
                    total,
                )

            studies = data.get("studies", [])
            new_on_page = 0
            for study in studies:
                nct = (
                    study.get("protocolSection", {})
                    .get("identificationModule", {})
                    .get("nctId")
                )
                if nct:
                    if nct in seen_nct:
                        continue
                    seen_nct.add(nct)
                all_studies.append(study)
                new_on_page += 1

            logger.info(
                "%s page %d: +%d new studies (unique total: %d)",
                overall_status,
                page_number,
                new_on_page,
                len(all_studies),
            )

            page_token = data.get("nextPageToken")
            if not page_token:
                logger.info("No more pages for status=%s.", overall_status)
                break

            time.sleep(CT_SLEEP)

    return all_studies


# ---------------------------------------------------------------------------
# Step 2 — Parse a single study into a metadata dictionary
# ---------------------------------------------------------------------------


def parse_study(study: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant fields from a raw study protocolSection."""
    ps = study.get("protocolSection", {})

    id_module = ps.get("identificationModule", {})
    desc_module = ps.get("descriptionModule", {})
    design_module = ps.get("designModule", {})
    locations_module = ps.get("contactsLocationsModule", {})
    eligibility_module = ps.get("eligibilityModule", {})
    outcomes_module = ps.get("outcomesModule", {})

    raw_locations = locations_module.get("locations", [])
    locations = [
        {
            "facility": loc.get("facility"),
            "city": loc.get("city"),
            "state": loc.get("state"),
            "zip": loc.get("zip"),
            "country": loc.get("country"),
        }
        for loc in raw_locations
    ]

    return {
        "nct_id": id_module.get("nctId"),
        "title": id_module.get("briefTitle"),
        "summary": desc_module.get("briefSummary"),
        "detailed_description": desc_module.get("detailedDescription"),
        "phases": design_module.get("phases", []),
        "locations": locations,
        "eligibility_criteria_raw": eligibility_module.get("eligibilityCriteria"),
        "primary_outcomes": outcomes_module.get("primaryOutcomes", []),
        "secondary_outcomes": outcomes_module.get("secondaryOutcomes", []),
    }


# ---------------------------------------------------------------------------
# Step 3 — LLM extraction via Groq
# ---------------------------------------------------------------------------


def _normalize_eligibility_json(parsed: Any) -> dict[str, Any] | None:
    """Groq occasionally returns a JSON array or a wrapped object; coerce to one dict."""
    if isinstance(parsed, dict):
        if ELIGIBILITY_EXPECTED_KEYS <= parsed.keys():
            return parsed
        for key in ("structured", "criteria", "eligibility", "extracted", "result", "data", "output"):
            inner = parsed.get(key)
            if isinstance(inner, dict):
                coerced = _normalize_eligibility_json(inner)
                if coerced is not None:
                    return coerced
        if len(parsed) == 1:
            inner = next(iter(parsed.values()))
            if isinstance(inner, dict):
                return _normalize_eligibility_json(inner)
        return parsed

    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                coerced = _normalize_eligibility_json(item)
                if coerced is not None:
                    return coerced
        return None

    return None


def parse_eligibility_with_groq(raw_criteria: str) -> dict[str, Any] | None:
    """Parse eligibility text into structured criteria via Groq."""
    parsed = _call_groq_json(ELIGIBILITY_SYSTEM_PROMPT, raw_criteria)
    if parsed is None:
        return None

    obj = _normalize_eligibility_json(parsed)
    if obj is None:
        logger.warning(
            "Eligibility response was not usable JSON object (got %s).",
            type(parsed).__name__,
        )
        return None

    missing = ELIGIBILITY_EXPECTED_KEYS - obj.keys()
    if missing:
        logger.warning("Eligibility response missing keys: %s", missing)
        return None

    return obj


def _build_biomarker_input(metadata: dict[str, Any]) -> str | None:
    """Assemble combined text from all relevant sections for biomarker extraction."""
    sections: list[str] = []

    elig = metadata.get("eligibility_criteria_raw")
    if elig:
        sections.append(f"[ELIGIBILITY CRITERIA]\n{elig}")

    for outcome in metadata.get("primary_outcomes", []):
        measure = outcome.get("measure", "")
        desc = outcome.get("description", "")
        sections.append(f"[PRIMARY OUTCOME] {measure}: {desc}")

    for outcome in metadata.get("secondary_outcomes", []):
        measure = outcome.get("measure", "")
        desc = outcome.get("description", "")
        sections.append(f"[SECONDARY OUTCOME] {measure}: {desc}")

    summary = metadata.get("summary")
    if summary:
        sections.append(f"[BRIEF SUMMARY]\n{summary}")

    detailed = metadata.get("detailed_description")
    if detailed:
        sections.append(f"[DETAILED DESCRIPTION]\n{detailed}")

    if not sections:
        return None
    return "\n\n".join(sections)


def parse_biomarkers_with_groq(metadata: dict[str, Any]) -> dict[str, Any] | None:
    """Extract diagnoses, biomarkers, and vitals using the unified schema."""
    combined_text = _build_biomarker_input(metadata)
    if not combined_text:
        return None

    parsed = _call_groq_json(PIPELINE_BIOMARKER_PROMPT, combined_text)
    if parsed is None:
        return None

    validated = validate_biomarker_response(parsed)
    if validated is None:
        logger.warning("Biomarker response failed schema validation.")
        return None

    return validated


# ---------------------------------------------------------------------------
# Step 4 — Combine and save
# ---------------------------------------------------------------------------


def build_output_record(
    metadata: dict[str, Any],
    structured_eligibility: dict[str, Any] | None,
    structured_biomarkers: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge trial metadata with LLM-structured eligibility and biomarkers."""
    return {
        "nct_id": metadata["nct_id"],
        "title": metadata["title"],
        "summary": metadata["summary"],
        "phases": metadata["phases"],
        "locations": metadata["locations"],
        "eligibility": {
            "raw": metadata["eligibility_criteria_raw"],
            "structured": structured_eligibility,
        },
        "biomarkers": structured_biomarkers,
    }


def save_results(records: list[dict[str, Any]], output_path: str) -> None:
    """Atomically write records to a JSON file."""
    tmp_path = output_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)
    os.replace(tmp_path, output_path)
    logger.info("Saved %d records to %s", len(records), output_path)


def load_checkpoint(output_path: str) -> tuple[list[dict[str, Any]], set[str]]:
    """Load existing output as a checkpoint to resume from."""
    if not os.path.exists(output_path):
        return [], set()

    try:
        with open(output_path, encoding="utf-8") as fh:
            records: list[dict[str, Any]] = json.load(fh)

        complete: list[dict[str, Any]] = []
        seen: set[str] = set()
        reprocess_count = 0
        for r in records:
            nct = r.get("nct_id")
            if not nct:
                continue
            bio = r.get("biomarkers")
            is_new_format = isinstance(bio, dict) and "demographics" in bio
            if is_new_format:
                complete.append(r)
                seen.add(nct)
            else:
                reprocess_count += 1

        if reprocess_count:
            logger.info(
                "Checkpoint: %d complete, %d need reprocessing.",
                len(complete),
                reprocess_count,
            )
        else:
            logger.info("Checkpoint: %d records already processed.", len(complete))
        return complete, seen
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load checkpoint (%s); starting fresh.", exc)
        return [], set()


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def main() -> None:
    logger.info(
        "=== Groq pipeline (primary=%s, min_interval=%.2fs) ===",
        GROQ_PRIMARY_MODEL,
        GROQ_MIN_INTERVAL_SEC,
    )

    if not os.getenv("GROQ_API_KEY"):
        logger.error(
            "GROQ_API_KEY is not set. Add it to your environment or .env and retry."
        )
        return

    try:
        _get_groq()
    except RuntimeError as exc:
        logger.error("%s", exc)
        return

    # Step 1: Fetch studies.
    logger.info(
        "Step 1: Querying ClinicalTrials.gov (statuses: %s)...",
        ", ".join(CT_OVERALL_STATUSES),
    )
    raw_studies = fetch_all_studies()
    logger.info("Total unique studies fetched: %d", len(raw_studies))

    # Step 2: Parse metadata.
    logger.info("Step 2: Parsing study metadata...")
    parsed_studies = [parse_study(s) for s in raw_studies]

    # Step 3: LLM structuring with checkpoint resume.
    output_records, seen_nct_ids = load_checkpoint(OUTPUT_FILE)
    elig_success = 0
    elig_skipped = 0
    elig_failed = 0
    bio_success = 0
    bio_skipped = 0
    new_this_run = 0

    total = len(parsed_studies)
    remaining = sum(1 for m in parsed_studies if m.get("nct_id") not in seen_nct_ids)
    logger.info("Remaining to process: %d / %d", remaining, total)

    for idx, metadata in enumerate(parsed_studies, start=1):
        nct_id = metadata.get("nct_id", "UNKNOWN")

        if nct_id in seen_nct_ids:
            continue

        # --- Eligibility extraction ---
        raw_criteria = metadata.get("eligibility_criteria_raw")

        if not raw_criteria:
            logger.warning(
                "[%d/%d] %s — no eligibility text, skipping.", idx, total, nct_id
            )
            structured_elig = None
            elig_skipped += 1
        else:
            logger.info("[%d/%d] %s — parsing eligibility...", idx, total, nct_id)
            structured_elig = parse_eligibility_with_groq(raw_criteria)
            if structured_elig is not None:
                elig_success += 1
            else:
                elig_failed += 1

        # --- Biomarker / diagnosis / vitals extraction ---
        logger.info("[%d/%d] %s — extracting biomarkers...", idx, total, nct_id)
        structured_bio = parse_biomarkers_with_groq(metadata)
        if structured_bio is None:
            bio_skipped += 1
        else:
            bio_success += 1

        output_records.append(
            build_output_record(metadata, structured_elig, structured_bio)
        )
        seen_nct_ids.add(nct_id)
        new_this_run += 1

        # Periodic checkpoint.
        if new_this_run % CHECKPOINT_EVERY == 0:
            logger.info("Checkpoint: %d processed this run, saving...", new_this_run)
            save_results(output_records, OUTPUT_FILE)

    # Final save.
    logger.info("Step 4: Saving final results...")
    save_results(output_records, OUTPUT_FILE)

    # Summary.
    logger.info("=== Pipeline complete ===")
    logger.info("  Total studies        : %d", total)
    logger.info("  Already checkpointed : %d", total - new_this_run)
    logger.info("  Eligibility parsed   : %d", elig_success)
    logger.info("  Eligibility skipped  : %d", elig_skipped)
    logger.info("  Eligibility errors   : %d", elig_failed)
    logger.info("  Biomarkers found     : %d", bio_success)
    logger.info("  Biomarkers none/empty: %d", bio_skipped)
    logger.info("  Output file          : %s", OUTPUT_FILE)


if __name__ == "__main__":
    main()
