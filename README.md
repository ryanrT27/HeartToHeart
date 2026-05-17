# Heart2Heart

Web application that collects a maternal-cardiovascular-oriented patient profile, optionally parses biomarkers and diagnoses from uploaded PDF lab reports, and scores the profile against a local corpus of ClinicalTrials.gov studies parsed into structured eligibility and clinical fields. The UI is a React (Vite) single-page app; the API is FastAPI (Python). PDFs go through `pdfplumber` (layout text and tables); if there isn’t enough text, it falls back to Tesseract OCR via `pdf2image`. Uploaded content is anonymized with Microsoft Presidio before structured extraction runs.

---

## Repository layout


| Path                                 | Role                                                                                                                                                                                         |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/`                           | FastAPI app (`main.py`), eligibility matcher (`matcher.py`), PDF ingestion (`pdf.py`), Presidio PII pipeline (`anonymize.py`), schema-validated clinical extraction (`llm.py`, `schema.py`). |
| `frontend/`                          | Vite + React UI (`src/App.jsx`, components, `src/api.js` HTTP client).                                                                                                                       |
| `maternal_cardio_trials_parsed.json` | Trial corpus consumed by the matcher (large JSON array). Override path with env var below.                                                                                                   |
| `pipeline.py`                        | Offline ETL: ClinicalTrials.gov API v2 ingestion, unstructured eligibility to structured JSON normalization, biomarker/diagnosis schema alignment, checkpointed writes to the corpus file.   |
| `requirements.txt`                   | Python dependencies for backend + pipeline.                                                                                                                                                  |
| `.env.example`                       | Documents `GROQ_API_KEY` and optional pipeline tuning variables.                                                                                                                             |


Should be run from the repository root (e.g. `uvicorn backend.main:app`), because modules use `from backend import ...`.

---

## Data pipeline (`pipeline.py`)

- Queries ClinicalTrials.gov with a fixed search string focused on pregnancy/postpartum/maternal cardiovascular terminology (see file header).
- Default overall statuses: `RECRUITING` and `NOT_YET_RECRUITING` (configurable via `CT_OVERALL_STATUSES`).
- For each study, uses a Large Language Model (defaults documented in `pipeline.py` and `.env.example`) to produce structured JSON aligned with the schemas used downstream.
- Writes `maternal_cardio_trials_parsed.json` at the repository root; supports intermittent runs via checkpoint logic inside the script.

Running:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python pipeline.py
```

Re-run when you want a refreshed trial set; point the matcher at the new file if you keep multiple copies (`TRIALS_JSON_PATH`).

---

## Backend API (FastAPI)

Start from repo root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Swagger docs:** `http://localhost:8000/docs`**.**


| Method | Path                    | Purpose                                                                                                                                                        |
| ------ | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET`  | `/api/trials/count`     | Number of trials loaded from JSON (0 if file missing).                                                                                                         |
| `POST` | `/api/upload-and-parse` | Multipart PDF: `pdfplumber` extraction (with OCR fallback for thin text layers), Presidio anonymization, then structured extraction (`GROQ_API_KEY` required). |
| `POST` | `/api/submit-data`      | Accepts `PatientProfile` JSON; computes BMI when height/weight present; returns echoed payload.                                                                |
| `POST` | `/api/match-trials`     | Same profile shape; runs `matcher.find_matches` and returns ranked trials for the UI.                                                                          |


CORS is configured to allow any origin (`allow_origins=["*"]`), suitable for local dev with a separate Vite origin.

### Trial loading

`matcher.TRIALS_FILE` defaults to `maternal_cardio_trials_parsed.json` next to `backend/` (resolved relative to `matcher.py`’s directory). Override:

```bash
export TRIALS_JSON_PATH=/absolute/path/to/custom.json
```

### Matching engine (`matcher.py`)

- Weighted dimensions include age, postpartum window, pregnancy timing, diagnoses, biomarkers, vitals, condition phrases, and trial location vs patient country/state (with penalties when trial sites are entirely outside the patient’s country).
- Raw weighted points are scaled to 0–100%.
- Filtering: top `candidate_pool` trials by raw score (default 20), then only trials with `match_score` > `min_match_percent` (default 70) are returned. Exact constants and helpers live in `matcher.py` (module docstring summarizes behavior).

### PDF and privacy (`pdf.py`, `anonymize.py`)

- Module entrypoints for pdfplumber extraction, OCR fallback, and Presidio.

### LLM extraction (`llm.py`)

- LLM validates against `backend.schema` for lab-style extraction from anonymized text and clinical descriptions.

---

## Frontend (`frontend/`)

Stack: React 18, Vite 6, global styles in `src/index.css`, fonts (Fredoka + Merriweather) linked from `index.html`.

### Routing / views (`src/App.jsx`)

No React Router: view state is local React state.

- Marketing: header (`SiteHeader`) + `main` — Home (`LandingHero`), About (`AboutPage`), Privacy (`PrivacyPage`).
- Onboarding: multi-step flow (`Onboarding.jsx`): demographics, pregnancy, health history, optional PDF upload (`FileUpload` → `uploadAndParse`), review/edit, then `submitData` + `matchTrials`; progress persisted in `sessionStorage` via `assessmentSession.js`.
- Results: `Results.jsx` shows headline count, export-to-CSV, and per-trial cards.

Leaving onboarding while a session exists triggers a browser confirm; clearing uses `clearAssessmentSession()`.

### API client (`src/api.js`)

Hard-coded base URL `http://localhost:8000/api`. For deployment, change this (or introduce `import.meta.env.VITE_API_BASE`) so the browser hits your deployed API.

### UI specifics (current behavior)

- Landing: hero copy + imagery; Our Mission cards use PNG icons (`megaphone 1.png`, `chart-line 1.png`, `pregnant 1.png`) centered in the decorative circles, styled monochrome via CSS `filter` where applied; impact section with doctor image, overlapping quote pill, and footer contact block.
- Favicon: `frontend/index.html` points at `public/Ellipse 7.png` (URL-encoded path).
- Results cards: match percentage in a tilted heart-shaped badge (SVG gradient + label); metadata row with NCT ID as plain text and “View official listing” linking out to ClinicalTrials.gov; summary and locations above a footer region for match-reason and disqualifier pills with a top border; CSV export includes NCT ID, title, match %, phases, summary, and listing URL.

### Frontend commands

```bash
cd frontend
npm install
npm run dev          # dev server (default port 5173)
npm run build        # production bundle to frontend/dist
npm run preview      # serve dist locally
```

---

## Environment variables


| Variable              | Used by                         | Notes                                                           |
| --------------------- | ------------------------------- | --------------------------------------------------------------- |
| `GROQ_API_KEY`        | `backend/llm.py`, `pipeline.py` | Required for PDF extraction path and for rebuilding trial JSON. |
| `TRIALS_JSON_PATH`    | `backend/matcher.py`            | Optional override for trial corpus path.                        |
| `CT_OVERALL_STATUSES` | `pipeline.py`                   | ClinicalTrials.gov overall statuses.                            |


Use a `.env` file in the repository root for local runs; `python-dotenv` loads it in `backend/main.py` and in `pipeline.py`.

---

## Running backend + frontend together (local)

Terminal 1 — API (from repo root):

```bash
source .venv/bin/activate
pip install -r requirements.txt   # once
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 — UI:

```bash
cd frontend
npm install   # once
npm run dev
```

Open the Vite URL (typically `http://localhost:5173`). Ensure `maternal_cardio_trials_parsed.json` exists or `/api/trials/count` will report zero matches until you run `pipeline.py` or supply a file via `TRIALS_JSON_PATH`.

---

## Deployment notes (short)

- Serve the Vite `dist/` output behind any static host or CDN; configure the API base URL to your production FastAPI origin.
- Restrict CORS in `backend/main.py` to known frontend origins instead of `*` when exposing the API publicly.

