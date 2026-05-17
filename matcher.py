"""
Clinical Trial Matcher

Loads the pre-processed clinical trials JSON and scores patient profiles
against each trial using a weighted multi-factor algorithm.

Scoring factors (total weight = 100):
  - Age match:          15 points
  - Postpartum match:   10 points
  - Pregnancy match:    10 points
  - Diagnosis overlap:  25 points
  - Biomarker relevance:20 points
  - Vital sign match:   10 points
  - Condition match:    10 points
"""

import json
import logging
import os
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)

TRIALS_FILE = os.environ.get(
    "TRIALS_JSON_PATH",
    os.path.join(os.path.dirname(__file__), "maternal_cardio_trials_parsed.json"),
)

# ---------------------------------------------------------------------------
# Lazy singleton for trials data
# ---------------------------------------------------------------------------

_trials_cache: list[dict[str, Any]] | None = None


def _load_trials() -> list[dict[str, Any]]:
    global _trials_cache
    if _trials_cache is not None:
        return _trials_cache

    if not os.path.exists(TRIALS_FILE):
        logger.warning("Trials file not found at %s — matcher will return empty.", TRIALS_FILE)
        _trials_cache = []
        return _trials_cache

    with open(TRIALS_FILE, encoding="utf-8") as f:
        _trials_cache = json.load(f)

    logger.info("Loaded %d trials from %s", len(_trials_cache), TRIALS_FILE)
    return _trials_cache


def reload_trials() -> int:
    """Force reload of trials data. Returns the number of trials loaded."""
    global _trials_cache
    _trials_cache = None
    return len(_load_trials())


def get_trials_count() -> int:
    return len(_load_trials())


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

WEIGHT_AGE = 15
WEIGHT_POSTPARTUM = 10
WEIGHT_PREGNANCY = 10
WEIGHT_DIAGNOSIS = 25
WEIGHT_BIOMARKER = 20
WEIGHT_VITALS = 10
WEIGHT_CONDITIONS = 10

MAX_MATCH_POINTS = (
    WEIGHT_AGE
    + WEIGHT_POSTPARTUM
    + WEIGHT_PREGNANCY
    + WEIGHT_DIAGNOSIS
    + WEIGHT_BIOMARKER
    + WEIGHT_VITALS
    + WEIGHT_CONDITIONS
)


def _match_percent(total: float) -> float:
    if MAX_MATCH_POINTS <= 0:
        return 0.0
    return round(100.0 * float(total) / MAX_MATCH_POINTS, 1)


def _score_age(patient: dict[str, Any], trial: dict[str, Any]) -> tuple[float, list[str]]:
    """Score based on whether patient age falls within trial's age range."""
    elig = trial.get("eligibility", {}).get("structured") or {}
    min_age = elig.get("min_age")
    max_age = elig.get("max_age")

    patient_age = (patient.get("demographics") or {}).get("age")

    if patient_age is None:
        return WEIGHT_AGE * 0.5, []

    reasons = []
    if min_age is not None and patient_age < min_age:
        return 0, []
    if max_age is not None and patient_age > max_age:
        return 0, []

    reasons.append(f"age {patient_age} within trial range [{min_age or '?'}-{max_age or '?'}]")
    return WEIGHT_AGE, reasons


def _score_postpartum(patient: dict[str, Any], trial: dict[str, Any]) -> tuple[float, list[str]]:
    """Score postpartum alignment."""
    elig = trial.get("eligibility", {}).get("structured") or {}
    requires_pp = elig.get("requires_postpartum", False)
    max_months = elig.get("max_months_postpartum")

    if not requires_pp:
        return WEIGHT_POSTPARTUM, []

    pregnancy = patient.get("pregnancy") or {}
    currently_pregnant = pregnancy.get("currently_pregnant")
    delivery_date_str = pregnancy.get("delivery_date")

    if currently_pregnant is True:
        return 0, []

    if not delivery_date_str:
        return WEIGHT_POSTPARTUM * 0.3, []

    reasons = []
    if max_months is not None:
        try:
            delivery = datetime.fromisoformat(delivery_date_str).date()
            months_pp = (date.today() - delivery).days / 30.44
            if months_pp > max_months:
                return 0, []
            reasons.append(f"postpartum {months_pp:.0f} months (within {max_months})")
        except (ValueError, TypeError):
            pass

    if not reasons:
        reasons.append("postpartum status matches")
    return WEIGHT_POSTPARTUM, reasons


def _score_pregnancy(patient: dict[str, Any], trial: dict[str, Any]) -> tuple[float, list[str]]:
    """Score pregnancy status alignment."""
    elig = trial.get("eligibility", {}).get("structured") or {}
    required_conds = [c.lower() for c in (elig.get("required_conditions") or [])]

    pregnancy = patient.get("pregnancy") or {}
    currently_pregnant = pregnancy.get("currently_pregnant")

    pregnancy_required = any(
        kw in cond for cond in required_conds
        for kw in ("pregnan", "gestation")
    )

    if not pregnancy_required:
        return WEIGHT_PREGNANCY, []

    if currently_pregnant is True:
        return WEIGHT_PREGNANCY, ["currently pregnant matches trial requirement"]
    elif currently_pregnant is False:
        return 0, []

    return WEIGHT_PREGNANCY * 0.5, []


def _score_diagnoses(patient: dict[str, Any], trial: dict[str, Any]) -> tuple[float, list[str]]:
    """Score based on overlap between trial's studied conditions and patient diagnoses."""
    trial_bio = trial.get("biomarkers") or {}
    trial_diag = trial_bio.get("diagnoses") or {}

    trial_conditions = {k for k, v in trial_diag.items() if v is True}
    if not trial_conditions:
        return WEIGHT_DIAGNOSIS * 0.5, []

    patient_diag = (patient.get("diagnoses") or {})
    matched = []
    for cond in trial_conditions:
        if patient_diag.get(cond) is True:
            matched.append(cond)

    ratio = len(matched) / len(trial_conditions)
    score = WEIGHT_DIAGNOSIS * ratio
    reasons = [f"diagnosis match: {c}" for c in matched]
    return score, reasons


def _score_biomarkers(patient: dict[str, Any], trial: dict[str, Any]) -> tuple[float, list[str]]:
    """Score based on biomarker relevance overlap."""
    trial_bio = trial.get("biomarkers") or {}
    trial_markers = trial_bio.get("biomarkers") or {}
    patient_markers = (patient.get("biomarkers") or {})

    trial_relevant = {
        k for k, v in trial_markers.items()
        if isinstance(v, dict) and v.get("value") is not None
    }

    if not trial_relevant:
        return WEIGHT_BIOMARKER * 0.5, []

    matched = 0
    reasons = []
    for marker in trial_relevant:
        p_item = patient_markers.get(marker)
        if not isinstance(p_item, dict):
            continue
        if p_item.get("value") is not None:
            matched += 1
            if p_item.get("high_risk") is True:
                reasons.append(f"biomarker {marker} high-risk aligns with trial")

    ratio = matched / len(trial_relevant) if trial_relevant else 0
    score = WEIGHT_BIOMARKER * ratio
    if matched and not reasons:
        reasons.append(f"{matched}/{len(trial_relevant)} relevant biomarkers measured")
    return score, reasons


def _score_vitals(patient: dict[str, Any], trial: dict[str, Any]) -> tuple[float, list[str]]:
    """Score vital sign alignment."""
    trial_bio = trial.get("biomarkers") or {}
    trial_vitals = trial_bio.get("vitals") or {}
    patient_vitals = patient.get("vitals") or {}

    trial_relevant = {
        k for k, v in trial_vitals.items()
        if isinstance(v, dict) and v.get("value") is not None
    }

    if not trial_relevant:
        return WEIGHT_VITALS * 0.5, []

    matched = 0
    reasons = []
    for vital in trial_relevant:
        p_item = patient_vitals.get(vital)
        if not isinstance(p_item, dict):
            continue
        if p_item.get("value") is not None:
            matched += 1
            flag = p_item.get("flag")
            if flag in ("elevated", "severe"):
                reasons.append(f"vital {vital} {flag} aligns with trial criteria")

    ratio = matched / len(trial_relevant) if trial_relevant else 0
    score = WEIGHT_VITALS * ratio
    return score, reasons


def _score_conditions(patient: dict[str, Any], trial: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    """Score based on required/excluded conditions text matching."""
    elig = trial.get("eligibility", {}).get("structured") or {}
    required = [c.lower() for c in (elig.get("required_conditions") or []) if c.strip()]
    excluded = [c.lower() for c in (elig.get("excluded_conditions") or []) if c.strip()]

    patient_diag = patient.get("diagnoses") or {}
    patient_conditions = {k.replace("_", " ") for k, v in patient_diag.items() if v is True}

    reasons = []
    disqualifiers = []

    # Check exclusions first.
    for excl in excluded:
        for pc in patient_conditions:
            if excl in pc or pc in excl:
                disqualifiers.append(f"excluded condition: {excl}")

    if disqualifiers:
        return 0, reasons, disqualifiers

    # Check required conditions.
    if not required:
        return WEIGHT_CONDITIONS, reasons, disqualifiers

    matched = 0
    for req in required:
        for pc in patient_conditions:
            if req in pc or pc in req:
                matched += 1
                reasons.append(f"condition '{req}' matches")
                break

    ratio = matched / len(required) if required else 0
    score = WEIGHT_CONDITIONS * ratio
    return score, reasons, disqualifiers


# ---------------------------------------------------------------------------
# Main matching function
# ---------------------------------------------------------------------------


def score_trial(patient: dict[str, Any], trial: dict[str, Any]) -> dict[str, Any]:
    """Score a single trial against a patient profile."""
    total = 0.0
    all_reasons: list[str] = []
    all_disqualifiers: list[str] = []

    age_score, age_reasons = _score_age(patient, trial)
    total += age_score
    all_reasons.extend(age_reasons)

    pp_score, pp_reasons = _score_postpartum(patient, trial)
    total += pp_score
    all_reasons.extend(pp_reasons)

    preg_score, preg_reasons = _score_pregnancy(patient, trial)
    total += preg_score
    all_reasons.extend(preg_reasons)

    diag_score, diag_reasons = _score_diagnoses(patient, trial)
    total += diag_score
    all_reasons.extend(diag_reasons)

    bio_score, bio_reasons = _score_biomarkers(patient, trial)
    total += bio_score
    all_reasons.extend(bio_reasons)

    vital_score, vital_reasons = _score_vitals(patient, trial)
    total += vital_score
    all_reasons.extend(vital_reasons)

    cond_score, cond_reasons, cond_disq = _score_conditions(patient, trial)
    total += cond_score
    all_reasons.extend(cond_reasons)
    all_disqualifiers.extend(cond_disq)

    # Hard disqualification: age out of range returns 0 from that scorer,
    # but excluded conditions are an explicit DQ.
    if all_disqualifiers:
        total = 0

    return {
        "nct_id": trial.get("nct_id"),
        "title": trial.get("title"),
        "summary": trial.get("summary"),
        "phases": trial.get("phases", []),
        "locations": trial.get("locations", []),
        "match_score": _match_percent(total),
        "match_reasons": all_reasons,
        "disqualifiers": all_disqualifiers,
    }


def find_matches(
    patient_profile: dict[str, Any],
    top_n: int | None = None,
    *,
    candidate_pool: int = 20,
    min_match_percent: float = 70.0,
) -> list[dict[str, Any]]:
    """Rank all trials, take the top ``pool`` by score, return those with match ``> min_match_percent``."""
    pool = candidate_pool if top_n is None else top_n
    if pool < 1:
        pool = 1
    elif pool > 50:
        pool = 50

    trials = _load_trials()

    scored = [score_trial(patient_profile, t) for t in trials]
    scored.sort(key=lambda x: x["match_score"], reverse=True)

    top = scored[:pool]
    return [t for t in top if t["match_score"] > min_match_percent]
