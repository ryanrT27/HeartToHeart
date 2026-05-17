"""Trial matching engine — scores patient profiles against clinical trials."""

import json
import logging
import os
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)

TRIALS_FILE = os.environ.get(
    "TRIALS_JSON_PATH",
    os.path.join(os.path.dirname(__file__), "..", "maternal_cardio_trials_parsed.json"),
)

_trials_cache: list[dict[str, Any]] | None = None

W_AGE = 15
W_POSTPARTUM = 10
W_PREGNANCY = 10
W_DIAGNOSIS = 25
W_BIOMARKER = 20
W_VITALS = 10
W_CONDITIONS = 10
W_LOCATION = 10


def _load_trials() -> list[dict[str, Any]]:
    global _trials_cache
    if _trials_cache is not None:
        return _trials_cache
    if not os.path.exists(TRIALS_FILE):
        logger.warning("Trials file not found: %s", TRIALS_FILE)
        _trials_cache = []
        return _trials_cache
    with open(TRIALS_FILE, encoding="utf-8") as f:
        _trials_cache = json.load(f)
    logger.info("Loaded %d trials", len(_trials_cache))
    return _trials_cache


def reload_trials() -> int:
    global _trials_cache
    _trials_cache = None
    return len(_load_trials())


def get_trials_count() -> int:
    return len(_load_trials())


def _score_age(patient, trial):
    elig = trial.get("eligibility", {}).get("structured") or {}
    min_age, max_age = elig.get("min_age"), elig.get("max_age")
    age = (patient.get("demographics") or {}).get("age")

    if age is None:
        return W_AGE * 0.5, []
    if min_age is not None and age < min_age:
        return 0, []
    if max_age is not None and age > max_age:
        return 0, []
    return W_AGE, [f"age {age} within trial range [{min_age or '?'}-{max_age or '?'}]"]


def _score_postpartum(patient, trial):
    elig = trial.get("eligibility", {}).get("structured") or {}
    if not elig.get("requires_postpartum", False):
        return W_POSTPARTUM, []

    pregnancy = patient.get("pregnancy") or {}
    if pregnancy.get("currently_pregnant") is True:
        return 0, []

    delivery_str = pregnancy.get("delivery_date")
    if not delivery_str:
        return W_POSTPARTUM * 0.3, []

    max_months = elig.get("max_months_postpartum")
    if max_months is not None:
        try:
            delivery = datetime.fromisoformat(delivery_str).date()
            months_pp = (date.today() - delivery).days / 30.44
            if months_pp > max_months:
                return 0, []
            return W_POSTPARTUM, [f"postpartum {months_pp:.0f} months (within {max_months})"]
        except (ValueError, TypeError):
            pass

    return W_POSTPARTUM, ["postpartum status matches"]


def _score_pregnancy(patient, trial):
    elig = trial.get("eligibility", {}).get("structured") or {}
    required_conds = [c.lower() for c in (elig.get("required_conditions") or [])]
    pregnancy_required = any(
        kw in cond for cond in required_conds for kw in ("pregnan", "gestation")
    )
    if not pregnancy_required:
        return W_PREGNANCY, []

    currently_pregnant = (patient.get("pregnancy") or {}).get("currently_pregnant")
    if currently_pregnant is True:
        return W_PREGNANCY, ["currently pregnant matches trial requirement"]
    if currently_pregnant is False:
        return 0, []
    return W_PREGNANCY * 0.5, []


def _score_diagnoses(patient, trial):
    trial_diag = (trial.get("biomarkers") or {}).get("diagnoses") or {}
    trial_conditions = {k for k, v in trial_diag.items() if v is True}
    if not trial_conditions:
        return W_DIAGNOSIS * 0.5, []

    patient_diag = patient.get("diagnoses") or {}
    matched = [c for c in trial_conditions if patient_diag.get(c) is True]
    ratio = len(matched) / len(trial_conditions)
    return W_DIAGNOSIS * ratio, [f"diagnosis match: {c}" for c in matched]


def _score_biomarkers(patient, trial):
    trial_markers = (trial.get("biomarkers") or {}).get("biomarkers") or {}
    patient_markers = patient.get("biomarkers") or {}
    relevant = {k for k, v in trial_markers.items() if isinstance(v, dict) and v.get("value") is not None}

    if not relevant:
        return W_BIOMARKER * 0.5, []

    matched = 0
    reasons = []
    for marker in relevant:
        p = patient_markers.get(marker)
        if isinstance(p, dict) and p.get("value") is not None:
            matched += 1
            if p.get("high_risk") is True:
                reasons.append(f"biomarker {marker} high-risk aligns with trial")

    ratio = matched / len(relevant)
    if matched and not reasons:
        reasons.append(f"{matched}/{len(relevant)} relevant biomarkers measured")
    return W_BIOMARKER * ratio, reasons


def _score_vitals(patient, trial):
    trial_vitals = (trial.get("biomarkers") or {}).get("vitals") or {}
    patient_vitals = patient.get("vitals") or {}
    relevant = {k for k, v in trial_vitals.items() if isinstance(v, dict) and v.get("value") is not None}

    if not relevant:
        return W_VITALS * 0.5, []

    matched = 0
    reasons = []
    for vital in relevant:
        p = patient_vitals.get(vital)
        if isinstance(p, dict) and p.get("value") is not None:
            matched += 1
            flag = p.get("flag")
            if flag in ("elevated", "severe"):
                reasons.append(f"vital {vital} {flag} aligns with trial criteria")

    return W_VITALS * (matched / len(relevant)), reasons


def _score_conditions(patient, trial):
    elig = trial.get("eligibility", {}).get("structured") or {}
    required = [c.lower() for c in (elig.get("required_conditions") or []) if c.strip()]
    excluded = [c.lower() for c in (elig.get("excluded_conditions") or []) if c.strip()]

    patient_diag = patient.get("diagnoses") or {}
    patient_conds = {k.replace("_", " ") for k, v in patient_diag.items() if v is True}

    disqualifiers = []
    for excl in excluded:
        for pc in patient_conds:
            if excl in pc or pc in excl:
                disqualifiers.append(f"excluded condition: {excl}")
    if disqualifiers:
        return 0, [], disqualifiers

    if not required:
        return W_CONDITIONS, [], []

    matched = 0
    reasons = []
    for req in required:
        for pc in patient_conds:
            if req in pc or pc in req:
                matched += 1
                reasons.append(f"condition '{req}' matches")
                break

    return W_CONDITIONS * (matched / len(required)), reasons, []


def _score_location(patient, trial):
    zip_code = (patient.get("demographics") or {}).get("zip_code")
    if not zip_code:
        return W_LOCATION * 0.5, []

    # Infer patient country from zip format: 5-digit = US
    patient_country = "United States" if str(zip_code).isdigit() and len(str(zip_code)) == 5 else None
    if not patient_country:
        return W_LOCATION * 0.5, []

    locations = trial.get("locations") or []
    trial_countries = {loc.get("country") for loc in locations if loc.get("country")}

    if not trial_countries:
        return W_LOCATION * 0.5, []

    if patient_country in trial_countries:
        return W_LOCATION, ["trial has US locations"]
    return 0, []


def score_trial(patient: dict[str, Any], trial: dict[str, Any]) -> dict[str, Any]:
    total = 0.0
    all_reasons: list[str] = []
    all_dq: list[str] = []

    for scorer in (_score_age, _score_postpartum, _score_pregnancy, _score_diagnoses, _score_biomarkers, _score_vitals):
        score, reasons = scorer(patient, trial)
        total += score
        all_reasons.extend(reasons)

    cond_score, cond_reasons, cond_dq = _score_conditions(patient, trial)
    total += cond_score
    all_reasons.extend(cond_reasons)

    loc_score, loc_reasons = _score_location(patient, trial)
    total += loc_score
    all_reasons.extend(loc_reasons)
    all_dq.extend(cond_dq)

    if all_dq:
        total = 0

    return {
        "nct_id": trial.get("nct_id"),
        "title": trial.get("title"),
        "summary": trial.get("summary"),
        "phases": trial.get("phases", []),
        "locations": trial.get("locations", []),
        "match_score": round(total, 1),
        "match_reasons": all_reasons,
        "disqualifiers": all_dq,
    }


def find_matches(patient_profile: dict[str, Any], top_n: int = 10) -> list[dict[str, Any]]:
    trials = _load_trials()
    scored = [score_trial(patient_profile, t) for t in trials]
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:top_n]
