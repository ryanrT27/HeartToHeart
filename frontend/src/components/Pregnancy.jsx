export default function Pregnancy({ formData, setFormData, onNext, onBackToDemographics }) {
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const setStatus = (status) => {
    setFormData({ ...formData, pregnancyStatus: status });
  };

  const handleBack = () => {
    if (!formData.pregnancyStatus) {
      onBackToDemographics();
      return;
    }
    setFormData({
      ...formData,
      pregnancyStatus: "",
      currentWeek: "",
      pregnancyType: "",
      deliveryDate: "",
      deliveryType: "",
    });
  };

  return (
    <div className="demographics-screen">
      <h2 className="demographics-screen-title">Tell us about your pregnancy below!</h2>

      {!formData.pregnancyStatus ? (
        <>
          <div className="pregnancy-status-choices">
            <button type="button" className="hero-cta onboarding-cta" onClick={() => setStatus("pregnant")}>
              Currently Pregnant
            </button>
            <button type="button" className="hero-cta onboarding-cta" onClick={() => setStatus("delivered")}>
              Recently Delivered
            </button>
          </div>
          <div className="pregnancy-actions">
            <button type="button" className="hero-cta onboarding-cta onboarding-cta--outline" onClick={handleBack}>
              Back
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="onboarding-context-text">
            <strong>Current selection:</strong>{" "}
            {formData.pregnancyStatus === "pregnant" ? "Currently pregnant" : "Postpartum"}
          </p>

          <div className="onboarding-form-single">
            {formData.pregnancyStatus === "pregnant" ? (
              <>
                <fieldset className="demo-input-shell">
                  <legend className="demo-input-label">Current gestational week</legend>
                  <input
                    type="number"
                    name="currentWeek"
                    className="demo-input-field"
                    value={formData.currentWeek || ""}
                    onChange={handleChange}
                    placeholder="Type here"
                    min={0}
                  />
                </fieldset>
                <fieldset className="demo-input-shell">
                  <legend className="demo-input-label">Pregnancy type</legend>
                  <select
                    name="pregnancyType"
                    className="demo-input-field demo-input-select"
                    value={formData.pregnancyType || ""}
                    onChange={handleChange}
                  >
                    <option value="">Select…</option>
                    <option value="single">Single</option>
                    <option value="multiple">Multiple (Twins, Triplets, etc.)</option>
                  </select>
                </fieldset>
              </>
            ) : (
              <>
                <fieldset className="demo-input-shell">
                  <legend className="demo-input-label">Delivery date</legend>
                  <input
                    type="date"
                    name="deliveryDate"
                    className="demo-input-field"
                    value={formData.deliveryDate || ""}
                    onChange={handleChange}
                  />
                </fieldset>
                <fieldset className="demo-input-shell">
                  <legend className="demo-input-label">Delivery type</legend>
                  <select
                    name="deliveryType"
                    className="demo-input-field demo-input-select"
                    value={formData.deliveryType || ""}
                    onChange={handleChange}
                  >
                    <option value="">Select…</option>
                    <option value="single">Single</option>
                    <option value="multiple">Multiple (Twins, Triplets, etc.)</option>
                  </select>
                </fieldset>
              </>
            )}
          </div>

          <div className="pregnancy-actions">
            <button type="button" className="hero-cta onboarding-cta onboarding-cta--outline" onClick={handleBack}>
              Back
            </button>
            <button type="button" className="hero-cta onboarding-cta" onClick={onNext}>
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
