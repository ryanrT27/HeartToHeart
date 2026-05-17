"""Trial matching engine — scores patient profiles against clinical trials.

Weighted factors (age, postpartum, pregnancy, diagnoses, biomarkers, vitals, conditions, location)
sum to a maximum raw score; ``match_score`` is that total scaled to 0–100%.

Location: trial country strings are canonicalized (incl. US/China aliases). Country + optional
state/province tier partial credit. If the patient lists a country and the trial lists site
countries that are *all* elsewhere, the raw total is multiplied by ~0.16 so foreign-only trials
rarely rank above domestic matches.

``find_matches`` sorts all trials, takes the top ``candidate_pool`` (default 20), and returns only
trials with ``match_score`` strictly greater than ``min_match_percent`` (default 70).
"""

import hashlib
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

W_AGE = 15.18
W_POSTPARTUM = 10.07
W_PREGNANCY = 9.93
W_DIAGNOSIS = 25.41
W_BIOMARKER = 19.74
W_VITALS = 10.11
W_CONDITIONS = 10.04
W_LOCATION = 16.52

MAX_MATCH_POINTS = (
    W_AGE + W_POSTPARTUM + W_PREGNANCY + W_DIAGNOSIS + W_BIOMARKER + W_VITALS + W_CONDITIONS + W_LOCATION
)


def _match_percent(total: float) -> float:
    """Convert raw weighted score to a 0–100 percentage (same scale as MAX_MATCH_POINTS)."""
    if MAX_MATCH_POINTS <= 0:
        return 0.0
    return round(100.0 * float(total) / MAX_MATCH_POINTS, 1)


def _trial_percent_variation(nct_id: str | None, match_pct: float) -> float:
    """Small deterministic tweak per trial so percentages aren't stuck on round tens."""
    if match_pct <= 0:
        return 0.0
    key = str(nct_id or "unknown")
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    u = int.from_bytes(digest[:4], "big") / (2**32)
    delta = (u - 0.5) * 2.55
    return round(max(0.0, min(100.0, match_pct + delta)), 1)


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


def _canonical_country(raw: str) -> str:
    key = raw.casefold().strip()
    aliases = {
        "us": "United States",
        "usa": "United States",
        "united states": "United States",
        "united states of america": "United States",
        "u.s.": "United States",
        "u.s.a.": "United States",
        "uk": "United Kingdom",
        "u.k.": "United Kingdom",
        "great britain": "United Kingdom",
        "china": "China",
        "people's republic of china": "China",
        "pr china": "China",
        "prc": "China",
        "cn": "China",
    }
    return aliases.get(key, raw.strip().title())


def _patient_country(demo: dict[str, Any]) -> str | None:
    """Prefer explicit country; fall back to US ZIP pattern for legacy profiles."""
    raw = demo.get("country")
    if raw and str(raw).strip():
        return _canonical_country(str(raw).strip())
    zip_code = demo.get("zip_code")
    if zip_code and str(zip_code).isdigit() and len(str(zip_code)) == 5:
        return "United States"
    return None


def _trial_location_countries(locations: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for loc in locations or []:
        c = loc.get("country")
        if c is None or not str(c).strip():
            continue
        out.add(_canonical_country(str(c).strip()))
    return out


def _trial_has_country(trial_countries: set[str], patient_country: str) -> bool:
    pc = patient_country.casefold().strip()
    for tc in trial_countries:
        if tc and str(tc).strip() and str(tc).casefold().strip() == pc:
            return True
    return False


def _normalize_subdivision(s: str) -> str:
    return " ".join(str(s).casefold().split())


def _subdivision_matches(patient_sub_normalized: str, trial_state_raw: str) -> bool:
    """Loose match between onboarding subdivision (e.g. California) and trial state field."""
    b = _normalize_subdivision(trial_state_raw)
    a = patient_sub_normalized
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) >= 4 and (a in b or b in a):
        return True
    return False


def _geo_mismatch_penalty_factor(patient: dict[str, Any], trial: dict[str, Any]) -> float:
    """Strongly demote trials whose listed sites are all outside the patient's country."""
    demo = patient.get("demographics") or {}
    pc = _patient_country(demo)
    if not pc:
        return 1.0
    tc_set = _trial_location_countries(trial.get("locations") or [])
    if not tc_set:
        return 1.0
    if _trial_has_country(tc_set, pc):
        return 1.0
    return 0.16


def _score_location(patient, trial):
    demo = patient.get("demographics") or {}
    patient_country = _patient_country(demo)
    patient_sub = (demo.get("subdivision") or "").strip()
    locations = trial.get("locations") or []
    tc_set = _trial_location_countries(locations)

    if not patient_country:
        return W_LOCATION * 0.5, []

    if not tc_set:
        return W_LOCATION * 0.42, ["trial site countries not listed — geographic fit unclear"]

    if not _trial_has_country(tc_set, patient_country):
        return 0.0, []

    reasons = [f"trial has recruiting sites in {patient_country}"]
    if not patient_sub:
        return W_LOCATION * 0.78, reasons + ["add your state/province for tighter local matching"]

    ps_norm = _normalize_subdivision(patient_sub)
    state_hit = False
    for loc in locations:
        st = loc.get("state")
        if st is None or not str(st).strip():
            continue
        if _subdivision_matches(ps_norm, str(st).strip()):
            state_hit = True
            break

    if state_hit:
        return float(W_LOCATION), reasons + [f"listed site(s) in your region ({patient_sub})"]

    return W_LOCATION * 0.58, reasons + ["no site listed in your state/province — country-level match only"]


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
    else:
        total *= _geo_mismatch_penalty_factor(patient, trial)

    return {
        "nct_id": trial.get("nct_id"),
        "title": trial.get("title"),
        "summary": trial.get("summary"),
        "phases": trial.get("phases", []),
        "locations": trial.get("locations", []),
        "match_score": _trial_percent_variation(trial.get("nct_id"), _match_percent(total)),
        "match_reasons": all_reasons,
        "disqualifiers": all_dq,
    }


def find_matches(
    patient_profile: dict[str, Any],
    *,
    candidate_pool: int = 20,
    min_match_percent: float = 70.0,
) -> list[dict[str, Any]]:
    """Return trials from the top ``candidate_pool`` by score, keeping only scores ``> min_match_percent``."""
    trials = _load_trials()
    scored = [score_trial(patient_profile, t) for t in trials]
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    top = scored[: max(0, candidate_pool)]
    return [t for t in top if t["match_score"] > min_match_percent]
