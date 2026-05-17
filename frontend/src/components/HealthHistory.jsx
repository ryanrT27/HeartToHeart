export default function HealthHistory({ formData, setFormData, onNext, onBack }) {
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <>
      <h2 className="screen-heading">Health History</h2>

      <label className="field">
        Currently breastfeeding?
        <select name="breastfeeding" value={formData.breastfeeding || ""} onChange={handleChange}>
          <option value="">Select...</option>
          <option value="yes">Yes</option>
          <option value="no">No</option>
        </select>
      </label>

      <label className="field">
        Smoking history
        <select name="smoking" value={formData.smoking || ""} onChange={handleChange}>
          <option value="">Select...</option>
          <option value="never">Never</option>
          <option value="former">Former</option>
          <option value="current">Current</option>
        </select>
      </label>

      <div style={{ display: "flex", gap: 10 }}>
        <button className="btn-back" onClick={onBack}>Back</button>
        <button className="btn-primary" onClick={onNext}>Next: Documents</button>
      </div>
    </>
  );
}
