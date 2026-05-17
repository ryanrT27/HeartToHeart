export default function Pregnancy({ formData, setFormData, onNext, onBack }) {
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const setStatus = (status) => {
    setFormData({ ...formData, pregnancyStatus: status });
  };

  return (
    <>
      <h2 className="screen-heading">Pregnancy Status</h2>

      {!formData.pregnancyStatus ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <button className="btn-secondary" onClick={() => setStatus("pregnant")}>
            Currently Pregnant
          </button>
          <button className="btn-secondary" onClick={() => setStatus("delivered")}>
            Recently Delivered
          </button>
        </div>
      ) : (
        <>
          <p>
            <strong>Status:</strong>{" "}
            {formData.pregnancyStatus === "pregnant" ? "Currently Pregnant" : "Postpartum"}
          </p>

          {formData.pregnancyStatus === "pregnant" ? (
            <>
              <label className="field">
                Current gestational week
                <input type="number" name="currentWeek" value={formData.currentWeek || ""} onChange={handleChange} />
              </label>
              <label className="field">
                Pregnancy type
                <select name="pregnancyType" value={formData.pregnancyType || ""} onChange={handleChange}>
                  <option value="">Select...</option>
                  <option value="single">Single</option>
                  <option value="multiple">Multiple (Twins, Triplets, etc.)</option>
                </select>
              </label>
            </>
          ) : (
            <>
              <label className="field">
                Delivery date
                <input type="date" name="deliveryDate" value={formData.deliveryDate || ""} onChange={handleChange} />
              </label>
              <label className="field">
                Delivery type
                <select name="deliveryType" value={formData.deliveryType || ""} onChange={handleChange}>
                  <option value="">Select...</option>
                  <option value="single">Single</option>
                  <option value="multiple">Multiple (Twins, Triplets, etc.)</option>
                </select>
              </label>
            </>
          )}

          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn-back" onClick={onBack}>Back</button>
            <button className="btn-primary" onClick={onNext}>Next</button>
          </div>
        </>
      )}
    </>
  );
}
