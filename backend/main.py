import logging
import tempfile
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend import anonymize, llm, matcher, pdf

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

app = FastAPI(title="Maternal Health API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PatientProfile(BaseModel):
    demographics: dict[str, Any] = {}
    pregnancy: dict[str, Any] = {}
    health_history: dict[str, Any] = {}
    diagnoses: dict[str, Any] = {}
    biomarkers: dict[str, Any] = {}
    vitals: dict[str, Any] = {}


@app.get("/api/trials/count")
def trials_count():
    return {"count": matcher.get_trials_count()}


@app.post("/api/upload-and-parse")
async def upload_and_parse(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        raw_text = pdf.extract_text(tmp_path)
        if len(raw_text.strip()) < 20:
            raise HTTPException(422, "Could not extract text from the PDF.")
        anonymized = anonymize.anonymize_text(raw_text)
        extracted = llm.extract_biomarkers(anonymized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Processing failed")
        raise HTTPException(500, f"Processing failed: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"status": "success", "data": extracted}


@app.post("/api/submit-data")
def submit_data(profile: PatientProfile):
    demo = profile.demographics
    h = demo.get("height_cm")
    w = demo.get("weight_kg")
    if h and w:
        try:
            demo["bmi"] = round(float(w) / (float(h) / 100) ** 2, 1)
        except (ValueError, ZeroDivisionError):
            pass

    return {"status": "success", "confirmed_data": profile.model_dump()}


@app.post("/api/match-trials")
def match_trials(profile: PatientProfile):
    results = matcher.find_matches(profile.model_dump(), top_n=10)
    return {"status": "success", "trials": results}
