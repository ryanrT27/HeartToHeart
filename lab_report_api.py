"""
Lab Report Upload & Biomarker Extraction API (Groq Cloud)

A FastAPI service that:
1. Accepts a PDF lab report upload
2. Extracts text locally (pdfplumber primary, pytesseract fallback for scans)
3. Anonymizes all PII using Microsoft Presidio
4. Sends the safe text to Groq (Llama 3.3 70B / 8B fallback) for structured
   cardiovascular biomarker extraction
5. Deletes the PDF immediately after extraction
6. Returns structured biomarker JSON (unified schema: diagnoses + biomarkers + vitals)

Prerequisites:
    1. Get a free Groq API key at https://console.groq.com/keys
    2. Create a .env file:
           GROQ_API_KEY=your_key_here
    3. Install dependencies:
           pip install -r requirements.txt
           sudo apt install tesseract-ocr poppler-utils
           python -m spacy download en_core_web_lg
    4. Start the server:
           uvicorn lab_report_api_groq:app --reload --port 8000

    # Upload a PDF:
    curl -X POST http://localhost:8000/upload-lab-report/ \
         -F "file=@my_lab_report.pdf"
"""

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from groq import Groq
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from biomarker_schema import (
    LAB_REPORT_BIOMARKER_PROMPT,
    validate_biomarker_response,
)
import matcher

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

UPLOAD_DIR = Path("/tmp/lab_reports")

# Groq models (free tier).
GROQ_PRIMARY_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"

# Minimum characters pdfplumber must extract before we fall back to OCR.
MIN_TEXT_LENGTH = 50

# Sessions expire after 1 hour.
SESSION_TTL_SECONDS = 3600

# PII entity types to detect and redact.
PII_ENTITIES = [
    "PERSON",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "US_SSN",
    "DATE_TIME",
    "LOCATION",
    "NRP",
    "MEDICAL_LICENSE",
    "IP_ADDRESS",
    "US_DRIVER_LICENSE",
]

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Lab Report Biomarker Extractor (Groq)",
    description=(
        "Upload a PDF lab report and receive structured cardiovascular biomarkers. "
        "Uses Groq cloud API (Llama 3.3 70B with 8B fallback)."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Lazy singletons
# ---------------------------------------------------------------------------

_analyzer: AnalyzerEngine | None = None
_anonymizer: AnonymizerEngine | None = None
_groq_client: Groq | None = None


def get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        logger.info("Initializing Presidio AnalyzerEngine (first request)...")
        _analyzer = AnalyzerEngine()
    return _analyzer


def get_anonymizer() -> AnonymizerEngine:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Create a .env file with your key."
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


@dataclass
class UploadRecord:
    filename: str
    uploaded_at: str
    extracted: dict[str, Any]
    fields_contributed: list[str]


@dataclass
class Session:
    session_id: str
    created_at: float = field(default_factory=time.time)
    profile: dict[str, Any] = field(default_factory=dict)
    uploads: list[UploadRecord] = field(default_factory=list)


_sessions: dict[str, Session] = {}


def create_blank_profile() -> dict[str, Any]:
    """Build an all-null unified schema profile as the starting point."""
    return {
        "demographics": {
            "age": None,
            "race_ethnicity": None,
            "height_cm": None,
            "weight_kg": None,
            "bmi": None,
            "zip_code": None,
            "radius_miles": None,
        },
        "pregnancy": {
            "currently_pregnant": None,
            "current_week": None,
            "pregnancy_type": None,
            "delivery_date": None,
            "delivery_type": None,
        },
        "health_history": {
            "currently_breastfeeding": None,
            "smoking_status": None,
        },
        "diagnoses": {
            "preeclampsia": False,
            "preeclampsia_onset": None,
            "hellp_syndrome": False,
            "gestational_hypertension": False,
            "peripartum_cardiomyopathy": False,
            "gestational_diabetes": False,
            "preterm_delivery": False,
            "delivery_week": None,
        },
        "biomarkers": {
            "sflt1_plgf_ratio": {"value": None, "unit": None, "high_risk": None},
            "nt_probnp": {"value": None, "unit": None, "high_risk": None},
            "troponin_t": {"value": None, "unit": None, "high_risk": None},
            "proteinuria": {"value": None, "unit": None, "high_risk": None},
            "hba1c": {"value": None, "unit": None, "high_risk": None},
            "hemoglobin": {"value": None, "unit": None, "high_risk": None},
            "fasting_glucose": {"value": None, "unit": None, "high_risk": None},
            "total_cholesterol": {"value": None, "unit": None, "high_risk": None},
        },
        "vitals": {
            "systolic_bp": {"value": None, "unit": None, "flag": None, "severe": None},
            "diastolic_bp": {"value": None, "unit": None, "flag": None, "severe": None},
            "resting_heart_rate": {"value": None, "unit": None, "flag": None},
        },
    }


def _get_session(session_id: str) -> Session:
    """Retrieve a session by ID, raising 404 if not found or expired."""
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if time.time() - session.created_at > SESSION_TTL_SECONDS:
        del _sessions[session_id]
        raise HTTPException(status_code=410, detail="Session expired.")
    return session


def merge_into_profile(
    profile: dict[str, Any],
    extracted: dict[str, Any],
) -> list[str]:
    """Merge a single PDF's extraction into the running session profile.

    - Demographics/pregnancy/health_history: first non-null wins.
    - Diagnoses: OR for booleans, first-non-null for onset/week.
    - Biomarkers: first non-null value wins.
    - Vitals: first non-null value wins.
    """
    contributed: list[str] = []

    # --- Demographics ---
    src_demo = extracted.get("demographics", {})
    dst_demo = profile["demographics"]
    for key in dst_demo:
        if dst_demo[key] is None and src_demo.get(key) is not None:
            dst_demo[key] = src_demo[key]
            contributed.append(f"demographics.{key}")

    # --- Pregnancy ---
    src_preg = extracted.get("pregnancy", {})
    dst_preg = profile["pregnancy"]
    for key in dst_preg:
        if dst_preg[key] is None and src_preg.get(key) is not None:
            dst_preg[key] = src_preg[key]
            contributed.append(f"pregnancy.{key}")

    # --- Health history ---
    src_hh = extracted.get("health_history", {})
    dst_hh = profile["health_history"]
    for key in dst_hh:
        if dst_hh[key] is None and src_hh.get(key) is not None:
            dst_hh[key] = src_hh[key]
            contributed.append(f"health_history.{key}")

    # --- Diagnoses ---
    src_diag = extracted.get("diagnoses", {})
    dst_diag = profile["diagnoses"]
    for key in dst_diag:
        src_val = src_diag.get(key)
        if src_val is None:
            continue
        if isinstance(dst_diag[key], bool):
            if src_val is True and not dst_diag[key]:
                dst_diag[key] = True
                contributed.append(f"diagnoses.{key}")
        else:
            if dst_diag[key] is None and src_val is not None:
                dst_diag[key] = src_val
                contributed.append(f"diagnoses.{key}")

    src_bio = extracted.get("biomarkers", {})
    dst_bio = profile["biomarkers"]
    for key in dst_bio:
        if dst_bio[key]["value"] is not None:
            continue
        src_item = src_bio.get(key, {})
        if src_item.get("value") is not None:
            dst_bio[key] = {
                "value": src_item["value"],
                "unit": src_item.get("unit"),
                "high_risk": src_item.get("high_risk"),
            }
            contributed.append(f"biomarkers.{key}")

    src_vitals = extracted.get("vitals", {})
    dst_vitals = profile["vitals"]
    for key in dst_vitals:
        if dst_vitals[key]["value"] is not None:
            continue
        src_item = src_vitals.get(key, {})
        if src_item.get("value") is not None:
            dst_vitals[key] = {
                "value": src_item["value"],
                "unit": src_item.get("unit"),
                "flag": src_item.get("flag"),
                **({"severe": src_item.get("severe")} if "severe" in dst_vitals[key] else {}),
            }
            contributed.append(f"vitals.{key}")

    return contributed


def list_missing_fields(profile: dict[str, Any]) -> list[str]:
    """Return field paths that are still null/unfilled."""
    missing: list[str] = []
    for key, val in profile["demographics"].items():
        if val is None:
            missing.append(f"demographics.{key}")
    for key, val in profile["pregnancy"].items():
        if val is None:
            missing.append(f"pregnancy.{key}")
    for key, val in profile["health_history"].items():
        if val is None:
            missing.append(f"health_history.{key}")
    for key, val in profile["diagnoses"].items():
        if isinstance(val, bool):
            continue
        if val is None:
            missing.append(f"diagnoses.{key}")
    for key, item in profile["biomarkers"].items():
        if item["value"] is None:
            missing.append(f"biomarkers.{key}")
    for key, item in profile["vitals"].items():
        if item["value"] is None:
            missing.append(f"vitals.{key}")
    return missing


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF, preserving layout and table structures."""
    import pdfplumber

    pages_text: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(layout=True) or ""

            tables = page.extract_tables() or []
            table_md_parts: list[str] = []
            for table in tables:
                if not table:
                    continue
                md_rows: list[str] = []
                for row_idx, row in enumerate(table):
                    cells = [str(cell) if cell is not None else "" for cell in row]
                    md_rows.append("| " + " | ".join(cells) + " |")
                    if row_idx == 0:
                        md_rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
                if md_rows:
                    table_md_parts.append("\n".join(md_rows))

            page_content = text
            if table_md_parts:
                page_content += "\n\n" + "\n\n".join(table_md_parts)

            pages_text.append(f"--- Page {page_num} ---\n{page_content}")

    full_text = "\n\n".join(pages_text)

    if len(full_text.strip()) < MIN_TEXT_LENGTH:
        logger.info("pdfplumber extracted < %d chars; falling back to OCR.", MIN_TEXT_LENGTH)
        full_text = _ocr_fallback(pdf_path)

    return full_text


def _ocr_fallback(pdf_path: Path) -> str:
    """Convert PDF pages to images and run pytesseract OCR on each."""
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(str(pdf_path))
    pages: list[str] = []
    for page_num, img in enumerate(images, start=1):
        text = pytesseract.image_to_string(img)
        pages.append(f"--- Page {page_num} (OCR) ---\n{text}")
    return "\n\n".join(pages)


# ---------------------------------------------------------------------------
# Anonymization
# ---------------------------------------------------------------------------


def anonymize_text(raw_text: str) -> str:
    """Remove PII from text using Microsoft Presidio."""
    analyzer = get_analyzer()
    anonymizer = get_anonymizer()

    results = analyzer.analyze(
        text=raw_text,
        entities=PII_ENTITIES,
        language="en",
    )

    anonymized = anonymizer.anonymize(text=raw_text, analyzer_results=results)
    logger.info("Anonymized %d PII entities.", len(results))
    return anonymized.text


# ---------------------------------------------------------------------------
# LLM biomarker extraction via Groq
# ---------------------------------------------------------------------------


def extract_biomarkers(anonymized_text: str) -> dict[str, Any]:
    """Send anonymized lab text to Groq and get structured biomarkers.

    Uses 70B primary with 8B fallback on rate limit.
    Raises HTTPException on failure.
    """
    client = get_groq()

    for model in (GROQ_PRIMARY_MODEL, GROQ_FALLBACK_MODEL):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": LAB_REPORT_BIOMARKER_PROMPT},
                    {"role": "user", "content": anonymized_text},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = response.choices[0].message.content
            if not content:
                logger.warning("Groq returned empty content with model %s.", model)
                continue

            parsed = json.loads(content)
            validated = validate_biomarker_response(parsed)
            if validated is None:
                raise HTTPException(
                    status_code=500,
                    detail="LLM response does not match the expected schema.",
                )
            return validated

        except HTTPException:
            raise
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500, detail=f"LLM response was not valid JSON: {exc}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            exc_str = str(exc).lower()
            if "rate_limit" in exc_str or "429" in exc_str:
                if model == GROQ_PRIMARY_MODEL:
                    logger.warning("70B rate-limited, falling back to 8B...")
                    time.sleep(2)
                    continue
            raise HTTPException(
                status_code=500, detail=f"Groq API error: {exc}"
            ) from exc

    raise HTTPException(
        status_code=503,
        detail="Both Groq models are rate-limited. Try again later.",
    )


# ---------------------------------------------------------------------------
# Endpoints: standalone single-file upload
# ---------------------------------------------------------------------------


@app.post("/upload-lab-report/")
async def upload_lab_report(file: UploadFile) -> dict[str, Any]:
    """Accept a PDF lab report, extract and anonymize text, return biomarkers."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Upload a file ending in .pdf.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4()}.pdf"
    pdf_path = UPLOAD_DIR / unique_name

    try:
        contents = await file.read()
        pdf_path.write_bytes(contents)
        logger.info("Saved upload to %s (%d bytes).", pdf_path, len(contents))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to save uploaded file: {exc}"
        ) from exc

    try:
        raw_text = extract_text_from_pdf(pdf_path)
    finally:
        pdf_path.unlink(missing_ok=True)
        logger.info("Deleted temporary PDF: %s", pdf_path)

    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Could not extract any readable text from the uploaded PDF.",
        )

    anonymized = anonymize_text(raw_text)
    biomarkers = extract_biomarkers(anonymized)
    return biomarkers


# ---------------------------------------------------------------------------
# Endpoints: session-based multi-PDF upload
# ---------------------------------------------------------------------------


@app.post("/sessions/")
async def create_session() -> dict[str, str]:
    """Create a new upload session."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = Session(
        session_id=session_id,
        profile=create_blank_profile(),
    )
    logger.info("Created session %s", session_id)
    return {"session_id": session_id}


@app.post("/sessions/{session_id}/upload")
async def session_upload(session_id: str, file: UploadFile) -> dict[str, Any]:
    """Upload a PDF into an existing session, merge results into profile."""
    session = _get_session(session_id)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Upload a file ending in .pdf.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4()}.pdf"
    pdf_path = UPLOAD_DIR / unique_name

    try:
        contents = await file.read()
        pdf_path.write_bytes(contents)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to save uploaded file: {exc}"
        ) from exc

    try:
        raw_text = extract_text_from_pdf(pdf_path)
    finally:
        pdf_path.unlink(missing_ok=True)

    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Could not extract any readable text from the uploaded PDF.",
        )

    anonymized = anonymize_text(raw_text)
    extracted = extract_biomarkers(anonymized)

    contributed = merge_into_profile(session.profile, extracted)

    record = UploadRecord(
        filename=file.filename or "unknown.pdf",
        uploaded_at=datetime.now(timezone.utc).isoformat(),
        extracted=extracted,
        fields_contributed=contributed,
    )
    session.uploads.append(record)

    logger.info(
        "Session %s: merged %d new fields from %s.",
        session_id, len(contributed), record.filename,
    )

    return {
        "filename": record.filename,
        "extracted": extracted,
        "fields_contributed": contributed,
        "profile": session.profile,
    }


@app.get("/sessions/{session_id}/profile")
async def get_session_profile(session_id: str) -> dict[str, Any]:
    """Get the current merged patient profile for a session."""
    session = _get_session(session_id)

    return {
        "session_id": session.session_id,
        "profile": session.profile,
        "uploads": [
            {
                "filename": u.filename,
                "uploaded_at": u.uploaded_at,
                "fields_contributed": u.fields_contributed,
            }
            for u in session.uploads
        ],
        "missing_fields": list_missing_fields(session.profile),
    }


# ---------------------------------------------------------------------------
# Endpoints: validate and match
# ---------------------------------------------------------------------------


@app.post("/sessions/{session_id}/validate")
async def validate_profile(session_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Accept a user-reviewed/edited profile and overwrite the session profile.

    Recalculates BMI if height and weight are provided.
    """
    session = _get_session(session_id)

    # Recalculate BMI if height and weight are present.
    demographics = profile.get("demographics") or {}
    height = demographics.get("height_cm")
    weight = demographics.get("weight_kg")
    if height and weight and height > 0:
        demographics["bmi"] = round(weight / (height / 100) ** 2, 1)
        profile["demographics"] = demographics

    session.profile = profile
    logger.info("Session %s: profile validated/updated by user.", session_id)

    return {
        "session_id": session.session_id,
        "profile": session.profile,
        "missing_fields": list_missing_fields(session.profile),
    }


@app.post("/sessions/{session_id}/match")
async def match_trials(session_id: str, top_n: int = 10) -> dict[str, Any]:
    """Match the validated patient profile against clinical trials.

    Returns the top N best-matched trials sorted by score.
    """
    session = _get_session(session_id)

    if top_n < 1:
        top_n = 1
    elif top_n > 50:
        top_n = 50

    matches = matcher.find_matches(session.profile, top_n=top_n)

    return {
        "session_id": session.session_id,
        "top_n": top_n,
        "matches": matches,
    }


@app.get("/trials/count")
async def trials_count() -> dict[str, int]:
    """Report how many clinical trials are loaded for matching."""
    return {"total_trials": matcher.get_trials_count()}
