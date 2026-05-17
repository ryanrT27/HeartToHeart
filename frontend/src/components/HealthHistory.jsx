export default function HealthHistory({ formData, setFormData, onNext, onBack }) {
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="demographics-screen">
      <h2 className="demographics-screen-title">Tell us about your health history below!</h2>

      <div className="onboarding-form-single">
        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">Currently breastfeeding?</legend>
          <select
            name="breastfeeding"
            className="demo-input-field demo-input-select"
            value={formData.breastfeeding || ""}
            onChange={handleChange}
          >
            <option value="">Select…</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </fieldset>

        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">Smoking history</legend>
          <select
            name="smoking"
            className="demo-input-field demo-input-select"
            value={formData.smoking || ""}
            onChange={handleChange}
          >
            <option value="">Select…</option>
            <option value="never">Never</option>
            <option value="former">Former</option>
            <option value="current">Current</option>
          </select>
        </fieldset>

        <fieldset className="demo-input-shell demo-input-shell--optional-note">
          <legend className="demo-input-label">Anything else we should know?</legend>
          {/* Free response is display-only; not saved to session or submitted */}
          <textarea
            className="demo-input-field demo-input-textarea"
            rows={4}
            placeholder="Optional! Share anything that might help us understand your situation and match you."
            aria-label="Anything else we should know?"
          />
        </fieldset>
      </div>

      <div className="onboarding-step-actions">
        <button type="button" className="hero-cta onboarding-cta onboarding-cta--outline" onClick={onBack}>
          Back
        </button>
        <button type="button" className="hero-cta onboarding-cta" onClick={onNext}>
          Next: Documents
        </button>
      </div>
    </div>
  );
}
