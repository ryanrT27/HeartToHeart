"""
Maternal/Postpartum Cardiovascular Trials Pipeline (Local Ollama)

Queries ClinicalTrials.gov for recruiting studies related to maternal/postpartum
cardiovascular health, then uses a local Llama 3 model via Ollama to:
  1. Parse eligibility criteria into structured JSON
  2. Extract clinical diagnoses, biomarkers, and vital signs (unified schema)

Prerequisites:
    1. Install Ollama from https://ollama.com (or have it running on Windows host)
    2. Pull and start the model:
           ollama run llama3
    3. Install Python dependencies:
           pip install requests
    4. Run:
           python pipeline.py

Output: maternal_cardio_trials_parsed.json (resumes from checkpoint automatically).
"""

import json
import logging
import os
import time
from typing import Any

import requests

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
    '(postpartum OR pregnant OR maternal OR pregnancy) AND '
    '(cardiovascular OR preeclampsia OR "peripartum cardiomyopathy" '
    'OR hypertension OR "heart failure")'
)

PAGE_SIZE = 50
CT_SLEEP = 1.0

# Ollama local server.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = 1200  # 5 minutes per request

OUTPUT_FILE = "maternal_cardio_trials_parsed.json"
CHECKPOINT_EVERY = 10  # save more frequently since each call is slower

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
# Ollama LLM client
# ---------------------------------------------------------------------------


def _call_ollama(system_prompt: str, user_text: str) -> dict[str, Any] | None:
    """Send a prompt to local Ollama and return parsed JSON, or None on failure."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "format": "json",
        "stream": False,
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
    except requests.Timeout:
        logger.error("Ollama request timed out after %ds.", OLLAMA_TIMEOUT)
        return None
    except requests.ConnectionError:
        logger.error(
            "Cannot connect to Ollama at %s. Is 'ollama serve' running?", OLLAMA_URL
        )
        return None
    except requests.RequestException as exc:
        logger.error("Ollama request failed: %s", exc)
        return None

    try:
        result = resp.json()
        content = result["message"]["content"]
        return json.loads(content)
    except (KeyError, json.JSONDecodeError) as exc:
        logger.error("Failed to parse Ollama response as JSON: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Step 1 — Fetch studies from ClinicalTrials.gov v2 API
# ---------------------------------------------------------------------------


def fetch_all_studies() -> list[dict[str, Any]]:
    """Fetch all pages of recruiting maternal/cardiovascular studies."""
    all_studies: list[dict[str, Any]] = []
    page_token: str | None = None
    page_number = 0

    while True:
        page_number += 1
        params: dict[str, Any] = {
            "query.term": SEARCH_TERM,
            "filter.overallStatus": "RECRUITING",
            "pageSize": PAGE_SIZE,
        }
        if page_number == 1:
            params["countTotal"] = "true"
        if page_token:
            params["pageToken"] = page_token

        try:
            response = requests.get(
                CLINICALTRIALS_BASE_URL, params=params, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("API request failed on page %d: %s", page_number, exc)
            break

        data = response.json()

        if page_number == 1:
            total = data.get("totalCount", "unknown")
            logger.info("Total matching recruiting studies: %s", total)

        studies = data.get("studies", [])
        all_studies.extend(studies)
        logger.info(
            "Page %d: fetched %d studies (running total: %d)",
            page_number, len(studies), len(all_studies),
        )

        page_token = data.get("nextPageToken")
        if not page_token:
            logger.info("No more pages. Done fetching.")
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
# Step 3 — LLM extraction via Ollama
# ---------------------------------------------------------------------------


def parse_eligibility_with_ollama(raw_criteria: str) -> dict[str, Any] | None:
    """Parse eligibility text into structured criteria via local Llama."""
    parsed = _call_ollama(ELIGIBILITY_SYSTEM_PROMPT, raw_criteria)
    if parsed is None:
        return None

    missing = ELIGIBILITY_EXPECTED_KEYS - parsed.keys()
    if missing:
        logger.warning("Eligibility response missing keys: %s", missing)
        return None

    return parsed


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


def parse_biomarkers_with_ollama(metadata: dict[str, Any]) -> dict[str, Any] | None:
    """Extract diagnoses, biomarkers, and vitals using the unified schema."""
    combined_text = _build_biomarker_input(metadata)
    if not combined_text:
        return None

    parsed = _call_ollama(PIPELINE_BIOMARKER_PROMPT, combined_text)
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
                "Checkpoint: %d complete, %d need reprocessing.", len(complete), reprocess_count
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
    logger.info("=== Local Ollama Pipeline (model: %s, timeout: %ds) ===", OLLAMA_MODEL, OLLAMA_TIMEOUT)

    # Verify Ollama is reachable.
    try:
        health = requests.get("http://localhost:11434/", timeout=5)
        health.raise_for_status()
    except requests.RequestException:
        logger.error(
            "Cannot reach Ollama at http://localhost:11434/. "
            "Please run 'ollama serve' or 'ollama run llama3' first."
        )
        return

    # Step 1: Fetch studies.
    logger.info("Step 1: Querying ClinicalTrials.gov v2 API...")
    raw_studies = fetch_all_studies()
    logger.info("Total studies fetched: %d", len(raw_studies))

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
            structured_elig = parse_eligibility_with_ollama(raw_criteria)
            if structured_elig is not None:
                elig_success += 1
            else:
                elig_failed += 1

        # --- Biomarker / diagnosis / vitals extraction ---
        logger.info("[%d/%d] %s — extracting biomarkers...", idx, total, nct_id)
        structured_bio = parse_biomarkers_with_ollama(metadata)
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
