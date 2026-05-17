import { useState } from "react";
import { COUNTRY_OPTIONS, subdivisionsForCountry } from "../data/geoRegions.js";

const RACE_OPTIONS = [
  { id: "white", label: "White" },
  { id: "black", label: "Black or African American" },
  { id: "hispanic", label: "Hispanic or Latino" },
  { id: "asian", label: "Asian" },
  { id: "native_american", label: "American Indian or Alaska Native" },
  { id: "pacific_islander", label: "Native Hawaiian or Pacific Islander" },
  { id: "other", label: "Other" },
];

const GENDER_OPTIONS = [
  { value: "", label: "Select…" },
  { value: "woman", label: "Woman" },
  { value: "man", label: "Man" },
  { value: "non_binary", label: "Non-binary" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
  { value: "another_identity", label: "Another identity" },
];

export default function Demographics({ formData, setFormData, onNext, onExitAssessment }) {
  const raceSelections = formData.race_ethnicity || [];
  
  // NEW: State to hold our validation error message
  const [errorMsg, setErrorMsg] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    // Clear the error message once they start typing/selecting again
    if (errorMsg) setErrorMsg(""); 

    if (name === "country") {
      setFormData({ ...formData, country: value, subdivision: "" });
      return;
    }
    setFormData({ ...formData, [name]: value });
  };

  const toggleRace = (id) => {
    if (errorMsg) setErrorMsg("");
    
    const updated = raceSelections.includes(id)
      ? raceSelections.filter((r) => r !== id)
      : [...raceSelections, id];
    setFormData({ ...formData, race_ethnicity: updated });
  };

  const subs = formData.country ? subdivisionsForCountry(formData.country) : null;
  const subSelectDisabled = !formData.country;

  // NEW: Validation function before moving to the next step
  const handleNext = () => {
    // 1. Check all basic text/select fields
    if (
      !formData.age ||
      !formData.genderIdentity ||
      !formData.heightFeet ||
      !formData.heightInches ||
      !formData.weight ||
      !formData.country
    ) {
      setErrorMsg("Please fill out all required fields.");
      return;
    }

    // 2. Check conditional state/province field (if their country has states)
    if (subs && subs.length > 0 && !formData.subdivision) {
      setErrorMsg("Please select a state/province.");
      return;
    }

    // 3. Check that at least one race/ethnicity is selected
    if (raceSelections.length === 0) {
      setErrorMsg("Please select at least one option for Race/Ethnicity.");
      return;
    }

    // If everything is filled out, clear errors and proceed
    setErrorMsg("");
    onNext();
  };

  return (
    <div className="demographics-screen">
      <h2 className="demographics-screen-title">Tell us about yourself below!</h2>

      <div className="demographics-form">
        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">Age *</legend>
          <input
            type="number"
            name="age"
            className="demo-input-field"
            value={formData.age || ""}
            onChange={handleChange}
            placeholder="Type here"
            min={0}
          />
        </fieldset>

        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">Gender identity *</legend>
          <select
            name="genderIdentity"
            className="demo-input-field demo-input-select"
            value={formData.genderIdentity || ""}
            onChange={handleChange}
          >
            {GENDER_OPTIONS.map((o) => (
              <option key={o.value || "placeholder"} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </fieldset>

        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">Height *</legend>
          <div className="demo-height-row">
            <input
              type="number"
              name="heightFeet"
              className="demo-input-field"
              value={formData.heightFeet || ""}
              onChange={handleChange}
              placeholder="ft"
              min={0}
            />
            <input
              type="number"
              name="heightInches"
              className="demo-input-field"
              value={formData.heightInches || ""}
              onChange={handleChange}
              placeholder="in"
              min={0}
              max={11}
            />
          </div>
        </fieldset>

        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">Weight *</legend>
          <input
            type="number"
            name="weight"
            className="demo-input-field"
            value={formData.weight || ""}
            onChange={handleChange}
            placeholder="lbs"
            min={0}
            step="0.1"
          />
        </fieldset>

        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">Country *</legend>
          <select
            name="country"
            className="demo-input-field demo-input-select"
            value={formData.country || ""}
            onChange={handleChange}
          >
            <option value="">Select country…</option>
            {COUNTRY_OPTIONS.map((c) => (
              <option key={c.id || c} value={c.id || c}>
                {c.label || c}
              </option>
            ))}
          </select>
        </fieldset>

        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">State / Province *</legend>
          <select
            name="subdivision"
            className="demo-input-field demo-input-select"
            value={formData.subdivision || ""}
            onChange={handleChange}
            disabled={subSelectDisabled}
          >
            <option value="">
              {subSelectDisabled ? "Select country first…" : "Select state/province…"}
            </option>
            {subs &&
              subs.map((s) => (
                <option key={s.id || s} value={s.id || s}>
                  {s.label || s}
                </option>
              ))}
            {formData.country && subs === null && (
              <option value="Not listed">Not listed</option>
            )}
          </select>
        </fieldset>

        <fieldset className="demo-input-shell demo-input-shell--full-width">
          <legend className="demo-input-label">Race / Ethnicity *</legend>
          <div className="demo-race-options">
            {RACE_OPTIONS.map((opt) => (
              <label key={opt.id} className="demo-race-option">
                <input
                  type="checkbox"
                  checked={raceSelections.includes(opt.id)}
                  onChange={() => toggleRace(opt.id)}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </fieldset>
      </div>

      {errorMsg && <p className="demographics-validation-msg">{errorMsg}</p>}

      <div className="onboarding-step-actions">
        <button type="button" className="hero-cta onboarding-cta onboarding-cta--outline" onClick={onExitAssessment}>
          Back
        </button>
        {/* NEW: Call handleNext instead of onNext directly */}
        <button type="button" className="hero-cta onboarding-cta" onClick={handleNext}>
          Next
        </button>
      </div>
    </div>
  );
}