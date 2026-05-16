from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Maternal Health API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DATA SHAPE

class PatientData(BaseModel):
    user_role: str  # "patient" or "doctor"
    complications: List[str]

# ==========================================
# ENDPOINT 1: Upload & Parse (Teammate's Domain)
# ==========================================

@app.post("/api/upload-and-parse")
async def parse_document(file: UploadFile = File(...)):
    """
    1. Frontend uploads document.
    2. Teammate parses it here.
    3. Returns data to frontend for user to review.
    """
    # TODO: Teammate puts parsing logic here
    
    return {
        "status": "success",
        "parsed_complications": ["preeclampsia"] # Mock data
    }

# ENDPOINT 2: Submit & Validate (No Database)

@app.post("/api/submit-data")
def submit_data(data: PatientData):
    """
    1. User reviews data on frontend and clicks "Submit".
    2. Since we have no database, we just validate the data is formatted correctly 
       and tell the frontend it's safe to move to the Trial Matching phase.
    """
    return {
        "status": "success",
        "message": "Data validated successfully! Ready for trial matching.",
        "confirmed_data": data
    }

# ENDPOINT 3: Match Trials (Teammate's Domain)

@app.post("/api/match-trials")
def match_trials(data: PatientData):
    """
    1. Frontend sends the confirmed data here.
    2. Teammate hits ClinicalTrials.gov API based on the complications.
    """
    # TODO: Teammate puts ClinicalTrials logic here
    
    return {
        "status": "success",
        "trials": [
            {"title": "Mock Trial for Preeclampsia", "link": "https://clinicaltrials.gov/..."}
        ]
    }