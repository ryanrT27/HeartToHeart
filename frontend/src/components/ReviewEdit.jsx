import { useState } from "react";
import { commaList } from "../formatDisplay";

const GENDER_IDENTITY_LABELS = {
  woman: "Woman",
  man: "Man",
  non_binary: "Non-binary",
  prefer_not_to_say: "Prefer not to say",
  another_identity: "Another identity",
};

function genderIdentityLabel(value) {
  if (value == null || value === "") return "—";
  return GENDER_IDENTITY_LABELS[value] || String(value);
}

const DIAGNOSIS_FIELDS = [
  { key: "preeclampsia", label: "Preeclampsia" },
  { key: "hellp_syndrome", label: "HELLP Syndrome" },
  { key: "gestational_hypertension", label: "Gestational Hypertension" },
  { key: "peripartum_cardiomyopathy", label: "Peripartum Cardiomyopathy" },
  { key: "gestational_diabetes", label: "Gestational Diabetes" },
  { key: "preterm_delivery", label: "Preterm Delivery" },
];

const BIOMARKER_FIELDS = [
  { key: "sflt1_plgf_ratio", label: "sFlt-1/PlGF Ratio", unit: "ratio" },
  { key: "nt_probnp", label: "NT-proBNP", unit: "pg/mL" },
  { key: "troponin_t", label: "Troponin T", unit: "ng/L" },
  { key: "proteinuria", label: "Proteinuria", unit: "mg/24h" },
  { key: "hba1c", label: "HbA1c", unit: "%" },
  { key: "hemoglobin", label: "Hemoglobin", unit: "g/dL" },
  { key: "fasting_glucose", label: "Fasting Glucose", unit: "mg/dL" },
  { key: "total_cholesterol", label: "Total Cholesterol", unit: "mg/dL" },
];

const VITAL_FIELDS = [
  { key: "systolic_bp", label: "Systolic BP", unit: "mmHg" },
  { key: "diastolic_bp", label: "Diastolic BP", unit: "mmHg" },
  { key: "resting_heart_rate", label: "Resting Heart Rate", unit: "bpm" },
];

export default function ReviewEdit({ profile, setProfile, onSubmit, onBack }) {
  const [showAllBiomarkers, setShowAllBiomarkers] = useState(false);

  const diag = profile.diagnoses || {};
  const bio = profile.biomarkers || {};
  const vitals = profile.vitals || {};
  const demo = profile.demographics || {};
  const preg = profile.pregnancy || {};
  const hh = profile.health_history || {};

  const toggleDiag = (key) => {
    setProfile({
      ...profile,
      diagnoses: { ...diag, [key]: !diag[key] },
    });
  };

  const setDiagField = (key, value) => {
    setProfile({ ...profile, diagnoses: { ...diag, [key]: value || null } });
  };

  const setBioValue = (key, field, value) => {
    const current = bio[key] || { value: null, unit: null, high_risk: null };
    setProfile({
      ...profile,
      biomarkers: {
        ...bio,
        [key]: { ...current, [field]: field === "value" ? (value === "" ? null : Number(value)) : value },
      },
    });
  };

  const setVitalValue = (key, value) => {
    const current = vitals[key] || { value: null, unit: null, flag: null };
    setProfile({
      ...profile,
      vitals: { ...vitals, [key]: { ...current, value: value === "" ? null : Number(value) } },
    });
  };

  const hasBioValue = (key) => bio[key]?.value != null;
  const visibleBiomarkers = showAllBiomarkers
    ? BIOMARKER_FIELDS
    : BIOMARKER_FIELDS.filter((b) => hasBioValue(b.key));

  return (
    <div className="demographics-screen">
      <h2 className="demographics-screen-title">Review your information below!</h2>
      <p className="onboarding-lead">
        Verify the information below. Edit anything that looks incorrect before matching.
      </p>

      <div className="onboarding-review-sections">
        <fieldset className="demo-input-shell demo-input-shell--full-width">
          <legend className="demo-input-label">Demographics</legend>
          <div className="review-summary-grid">
            <span>Age: {demo.age || "—"}</span>
            <span>Gender identity: {genderIdentityLabel(demo.gender_identity)}</span>
            <span>Race: {commaList(demo.race_ethnicity) || "—"}</span>
            <span>Height: {demo.height_cm ? `${demo.height_cm.toFixed(1)} cm` : "—"}</span>
            <span>Weight: {demo.weight_kg ? `${demo.weight_kg.toFixed(1)} kg` : "—"}</span>
            <span>BMI: {demo.bmi ? demo.bmi.toFixed(1) : "—"}</span>
            <span>Country: {demo.country || "—"}</span>
            <span>State / Province: {demo.subdivision || "—"}</span>
          </div>
        </fieldset>

        <fieldset className="demo-input-shell demo-input-shell--full-width">
          <legend className="demo-input-label">Pregnancy</legend>
          <div className="review-summary-grid">
            <span>
              {preg.currently_pregnant === true && "Currently pregnant"}
              {preg.currently_pregnant === false && "Postpartum"}
              {preg.currently_pregnant == null && "—"}
            </span>
            {preg.currently_pregnant === true && <span>Week: {preg.current_week || "—"}</span>}
            {preg.currently_pregnant === false && <span>Delivered: {preg.delivery_date || "—"}</span>}
            <span>Type: {preg.pregnancy_type || preg.delivery_type || "—"}</span>
          </div>
        </fieldset>

        <fieldset className="demo-input-shell demo-input-shell--full-width">
          <legend className="demo-input-label">Health history</legend>
          <div className="review-summary-grid">
            <span>
              Breastfeeding:{" "}
              {hh.currently_breastfeeding === true ? "Yes" : hh.currently_breastfeeding === false ? "No" : "—"}
            </span>
            <span>Smoking: {hh.smoking_status || "—"}</span>
          </div>
        </fieldset>

        <fieldset className="demo-input-shell demo-input-shell--full-width">
          <legend className="demo-input-label">Diagnoses</legend>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
            {DIAGNOSIS_FIELDS.map((d) => (
              <div key={d.key}>
                <label className="demo-race-option">
                  <input type="checkbox" checked={!!diag[d.key]} onChange={() => toggleDiag(d.key)} />
                  {d.label}
                </label>
                {d.key === "preeclampsia" && diag.preeclampsia && (
                  <div className="review-nested-field">
                    <select
                      value={diag.preeclampsia_onset || ""}
                      onChange={(e) => setDiagField("preeclampsia_onset", e.target.value)}
                      className="demo-input-field demo-input-select"
                    >
                      <option value="">Onset unknown</option>
                      <option value="early">Early (&lt;34 weeks)</option>
                      <option value="late">Late (≥34 weeks)</option>
                    </select>
                  </div>
                )}
                {d.key === "preterm_delivery" && diag.preterm_delivery && (
                  <div className="review-nested-field">
                    <input
                      type="number"
                      placeholder="Delivery week"
                      className="demo-input-field review-field-narrow"
                      value={diag.delivery_week ?? ""}
                      onChange={(e) =>
                        setDiagField("delivery_week", e.target.value ? Number(e.target.value) : null)
                      }
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </fieldset>

        <fieldset className="demo-input-shell demo-input-shell--full-width">
          <legend className="demo-input-label">Biomarkers</legend>
          {visibleBiomarkers.length === 0 && !showAllBiomarkers && (
            <p className="onboarding-muted-text">No biomarkers extracted from documents.</p>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
            {visibleBiomarkers.map((b) => (
              <div key={b.key} className="review-biomarker-row">
                <span className="review-inline-label">{b.label}</span>
                <input
                  type="number"
                  step="any"
                  placeholder="Value"
                  className="demo-input-field review-field-narrow"
                  value={bio[b.key]?.value ?? ""}
                  onChange={(e) => setBioValue(b.key, "value", e.target.value)}
                />
                <span className="review-unit-muted">{b.unit}</span>
                <label className="demo-race-option">
                  <input
                    type="checkbox"
                    checked={!!bio[b.key]?.high_risk}
                    onChange={(e) => setBioValue(b.key, "high_risk", e.target.checked)}
                  />
                  High risk
                </label>
              </div>
            ))}
          </div>
          {!showAllBiomarkers && (
            <button type="button" className="onboarding-text-link" onClick={() => setShowAllBiomarkers(true)}>
              + Show all biomarkers
            </button>
          )}
        </fieldset>

        <fieldset className="demo-input-shell demo-input-shell--full-width">
          <legend className="demo-input-label">Vitals</legend>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
            {VITAL_FIELDS.map((v) => (
              <div key={v.key} className="review-vital-row">
                <span className="review-inline-label">{v.label}</span>
                <input
                  type="number"
                  placeholder="Value"
                  className="demo-input-field review-field-narrow"
                  value={vitals[v.key]?.value ?? ""}
                  onChange={(e) => setVitalValue(v.key, e.target.value)}
                />
                <span className="review-unit-muted">{v.unit}</span>
              </div>
            ))}
          </div>
        </fieldset>
      </div>

      <div className="onboarding-step-actions">
        <button type="button" className="hero-cta onboarding-cta onboarding-cta--outline" onClick={onBack}>
          Back
        </button>
        <button type="button" className="hero-cta onboarding-cta" onClick={onSubmit}>
          Find Matching Trials
        </button>
      </div>
    </div>
  );
}
