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
    <>
      <h2 className="screen-heading">Review & Edit</h2>
      <p style={{ color: "#475569", margin: 0, fontSize: 14 }}>
        Verify the information below. Edit anything that looks incorrect before matching.
      </p>

      {/* Demographics summary */}
      <section className="review-section">
        <h3>Demographics</h3>
        <div className="summary-grid">
          <span>Age: {demo.age || "—"}</span>
          <span>Gender identity: {genderIdentityLabel(demo.gender_identity)}</span>
          <span>Race: {commaList(demo.race_ethnicity) || "—"}</span>
          <span>Height: {demo.height_cm ? `${demo.height_cm.toFixed(1)} cm` : "—"}</span>
          <span>Weight: {demo.weight_kg ? `${demo.weight_kg.toFixed(1)} kg` : "—"}</span>
          <span>BMI: {demo.bmi ? demo.bmi.toFixed(1) : "—"}</span>
          <span>Country: {demo.country || "—"}</span>
          <span>State / Province: {demo.subdivision || "—"}</span>
        </div>
      </section>

      {/* Pregnancy summary */}
      <section className="review-section">
        <h3>Pregnancy</h3>
        <div className="summary-grid">
          <span>
            {preg.currently_pregnant === true && "Currently pregnant"}
            {preg.currently_pregnant === false && "Postpartum"}
            {preg.currently_pregnant == null && "—"}
          </span>
          {preg.currently_pregnant === true && <span>Week: {preg.current_week || "—"}</span>}
          {preg.currently_pregnant === false && <span>Delivered: {preg.delivery_date || "—"}</span>}
          <span>Type: {preg.pregnancy_type || preg.delivery_type || "—"}</span>
        </div>
      </section>

      {/* Health history summary */}
      <section className="review-section">
        <h3>Health History</h3>
        <div className="summary-grid">
          <span>Breastfeeding: {hh.currently_breastfeeding === true ? "Yes" : hh.currently_breastfeeding === false ? "No" : "—"}</span>
          <span>Smoking: {hh.smoking_status || "—"}</span>
        </div>
      </section>

      {/* Diagnoses */}
      <section className="review-section">
        <h3>Diagnoses</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {DIAGNOSIS_FIELDS.map((d) => (
            <div key={d.key}>
              <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                <input type="checkbox" checked={!!diag[d.key]} onChange={() => toggleDiag(d.key)} />
                {d.label}
              </label>
              {d.key === "preeclampsia" && diag.preeclampsia && (
                <select
                  value={diag.preeclampsia_onset || ""}
                  onChange={(e) => setDiagField("preeclampsia_onset", e.target.value)}
                  style={{ marginLeft: 28, marginTop: 4 }}
                  className="inline-select"
                >
                  <option value="">Onset unknown</option>
                  <option value="early">Early (&lt;34 weeks)</option>
                  <option value="late">Late (≥34 weeks)</option>
                </select>
              )}
              {d.key === "preterm_delivery" && diag.preterm_delivery && (
                <input
                  type="number"
                  placeholder="Delivery week"
                  value={diag.delivery_week || ""}
                  onChange={(e) => setDiagField("delivery_week", e.target.value ? Number(e.target.value) : null)}
                  style={{ marginLeft: 28, marginTop: 4, width: 120 }}
                />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Biomarkers */}
      <section className="review-section">
        <h3>Biomarkers</h3>
        {visibleBiomarkers.length === 0 && !showAllBiomarkers && (
          <p style={{ color: "#94a3b8", fontSize: 14 }}>No biomarkers extracted from documents.</p>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {visibleBiomarkers.map((b) => (
            <div key={b.key} style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <span style={{ width: 140, fontSize: 14, fontWeight: 500 }}>{b.label}</span>
              <input
                type="number"
                step="any"
                placeholder="Value"
                value={bio[b.key]?.value ?? ""}
                onChange={(e) => setBioValue(b.key, "value", e.target.value)}
                style={{ width: 80 }}
              />
              <span style={{ fontSize: 12, color: "#64748b" }}>{b.unit}</span>
              <label style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
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
          <button className="btn-link" style={{ marginTop: 8 }} onClick={() => setShowAllBiomarkers(true)}>
            + Show all biomarkers
          </button>
        )}
      </section>

      {/* Vitals */}
      <section className="review-section">
        <h3>Vitals</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {VITAL_FIELDS.map((v) => (
            <div key={v.key} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 160, fontSize: 14, fontWeight: 500 }}>{v.label}</span>
              <input
                type="number"
                placeholder="Value"
                value={vitals[v.key]?.value ?? ""}
                onChange={(e) => setVitalValue(v.key, e.target.value)}
                style={{ width: 80 }}
              />
              <span style={{ fontSize: 12, color: "#64748b" }}>{v.unit}</span>
            </div>
          ))}
        </div>
      </section>

      <div style={{ display: "flex", gap: 10 }}>
        <button className="btn-back" onClick={onBack}>Back</button>
        <button className="btn-primary" onClick={onSubmit}>Find Matching Trials</button>
      </div>
    </>
  );
}
