"""Unified patient schema and LLM prompt definitions."""

from typing import Any

UNIFIED_EXPECTED_KEYS = {"demographics", "pregnancy", "health_history", "diagnoses", "biomarkers", "vitals"}

_JSON_SCHEMA_EXAMPLE = """\
{
  "demographics": {
    "age": <integer or null>,
    "race_ethnicity": [<string>, ...] or null,
    "height_cm": <number or null>,
    "weight_kg": <number or null>,
    "bmi": <number or null>,
    "zip_code": <string or null>,
    "radius_miles": <integer or null>
  },
  "pregnancy": {
    "currently_pregnant": <true/false/null>,
    "current_week": <integer or null>,
    "pregnancy_type": <"single"/"multiple"/null>,
    "delivery_date": <"YYYY-MM-DD" or null>,
    "delivery_type": <"single"/"multiple"/null>
  },
  "health_history": {
    "currently_breastfeeding": <true/false/null>,
    "smoking_status": <"never"/"former"/"current"/null>
  },
  "diagnoses": {
    "preeclampsia": <true/false>,
    "preeclampsia_onset": <"early"/"late"/null>,
    "hellp_syndrome": <true/false>,
    "gestational_hypertension": <true/false>,
    "peripartum_cardiomyopathy": <true/false>,
    "gestational_diabetes": <true/false>,
    "preterm_delivery": <true/false>,
    "delivery_week": <integer or null>
  },
  "biomarkers": {
    "sflt1_plgf_ratio": {"value": <number or null>, "unit": <string or null>, "high_risk": <true/false/null>},
    "nt_probnp": {"value": <number or null>, "unit": <string or null>, "high_risk": <true/false/null>},
    "troponin_t": {"value": <number or null>, "unit": <string or null>, "high_risk": <true/false/null>},
    "proteinuria": {"value": <number or null>, "unit": <string or null>, "high_risk": <true/false/null>},
    "hba1c": {"value": <number or null>, "unit": <string or null>, "high_risk": <true/false/null>},
    "hemoglobin": {"value": <number or null>, "unit": <string or null>, "high_risk": <true/false/null>},
    "fasting_glucose": {"value": <number or null>, "unit": <string or null>, "high_risk": <true/false/null>},
    "total_cholesterol": {"value": <number or null>, "unit": <string or null>, "high_risk": <true/false/null>}
  },
  "vitals": {
    "systolic_bp": {"value": <integer or null>, "unit": <string or null>, "flag": <"normal"/"elevated"/"severe"/null>, "severe": <true/false/null>},
    "diastolic_bp": {"value": <integer or null>, "unit": <string or null>, "flag": <"normal"/"elevated"/"severe"/null>, "severe": <true/false/null>},
    "resting_heart_rate": {"value": <integer or null>, "unit": <string or null>, "flag": <"normal"/"elevated"/null>}
  }
}"""

_SHARED_RULES = """\
Demographics extraction rules:
- "age": Extract patient age in years as an integer.
- "race_ethnicity": Extract as a list of lowercase strings (e.g. ["white", "hispanic"]).
- "height_cm" and "weight_kg": Extract numeric values. Convert inches to cm (* 2.54),
  lbs to kg (/ 2.205) if needed. Calculate "bmi" = weight_kg / (height_cm/100)^2.
- "zip_code": Extract 5-digit ZIP if present.
- "radius_miles": null unless explicitly stated.

Pregnancy status extraction rules:
- "currently_pregnant": true if the patient is stated to be currently pregnant.
- "current_week": gestational week if pregnant and stated.
- "pregnancy_type": "single" or "multiple" (twins, triplets, etc.) if stated.
- "delivery_date": ISO date of most recent delivery if the patient is postpartum and date is given.
- "delivery_type": "single" or "multiple" for the most recent delivery if stated.

Health history extraction rules:
- "currently_breastfeeding": true/false if stated, null if not mentioned.
- "smoking_status": "never", "former", or "current" if stated, null if not mentioned.

Clinical diagnosis detection rules:
- "preeclampsia": true if preeclampsia is mentioned. Set "preeclampsia_onset" to "early"
  if onset is described as < 34 weeks, "late" if >= 34 weeks, null if not specified.
- "hellp_syndrome": true if HELLP syndrome is mentioned.
- "gestational_hypertension": true if gestational hypertension OR pregnancy-induced
  hypertension (PIH) is mentioned.
- "peripartum_cardiomyopathy": true if peripartum cardiomyopathy or PPCM is mentioned.
- "gestational_diabetes": true if gestational diabetes (GDM) is mentioned.
- "preterm_delivery": true if preterm delivery or delivery before 37 weeks is mentioned.
  Set "delivery_week" to the gestational week if stated, else null.

Lab biomarker extraction rules:
- For each biomarker, extract the numeric value and its unit from the text.
- "high_risk" flagging thresholds:
  * sflt1_plgf_ratio: high_risk = true if value > 38
  * nt_probnp: high_risk = true if value > 125 pg/mL
  * troponin_t: high_risk = true if value > 14 ng/L
  * proteinuria: high_risk = true if value > 300 mg/24h OR dipstick >= 1+
  * hba1c: high_risk = true if value >= 5.7%
  * hemoglobin, fasting_glucose, total_cholesterol: set high_risk to null (no universal threshold)
- If a biomarker is not found, set value/unit/high_risk all to null.

Vital sign extraction rules:
- systolic_bp: flag = "elevated" if >= 140, "severe" if >= 160, else "normal". severe = true if >= 160.
- diastolic_bp: flag = "elevated" if >= 90, "severe" if >= 110, else "normal". severe = true if >= 110.
- resting_heart_rate: flag = "elevated" if > 100 bpm, else "normal".
- If a vital is not found, set all its fields to null.

General rules:
- Extract ONLY information explicitly stated in the text. Do not infer or assume.
- Output ONLY a single JSON object matching the schema below — no explanation, no markdown fences.
"""

PIPELINE_BIOMARKER_PROMPT = f"""\
You are a clinical data extraction specialist analyzing text from a clinical trial
(eligibility criteria, outcome measures, study summary, and detailed description).

Your task is to identify any demographics requirements, pregnancy status criteria,
health history requirements, clinical diagnoses mentioned as conditions being studied,
any biomarker thresholds specified as inclusion/exclusion criteria or outcome measures,
and any vital sign cutoffs stated in the trial text.

If a diagnosis is a focus of the trial (inclusion criterion or condition being studied),
mark it as true. If a biomarker threshold is stated, record it as the value.
If a vital sign cutoff is given, record it. For demographics/pregnancy/health_history,
extract any criteria or requirements mentioned (e.g. age range, pregnancy requirement).

{_SHARED_RULES}

{_JSON_SCHEMA_EXAMPLE}
"""

LAB_REPORT_PROMPT = f"""\
You are a clinical data extractor analyzing an anonymized patient lab report or
health record. Your task is to find the patient's demographics, pregnancy status,
health history, actual test results, diagnoses, and vital sign measurements.

Extract the patient's real values as reported in the document. Apply the high-risk
thresholds to flag values that exceed safe levels.

{_SHARED_RULES}

{_JSON_SCHEMA_EXAMPLE}
"""


def validate_response(parsed: Any) -> dict[str, Any] | None:
    if not isinstance(parsed, dict):
        return None
    if not UNIFIED_EXPECTED_KEYS.issubset(parsed.keys()):
        return None
    for key in ("demographics", "pregnancy", "health_history", "diagnoses", "biomarkers", "vitals"):
        if not isinstance(parsed.get(key), dict):
            return None
    return parsed
