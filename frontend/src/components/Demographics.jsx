import { useState } from "react";

const RACE_OPTIONS = [
  { id: "white", label: "White" },
  { id: "black", label: "Black or African American" },
  { id: "hispanic", label: "Hispanic or Latino" },
  { id: "asian", label: "Asian" },
  { id: "native_american", label: "American Indian or Alaska Native" },
  { id: "pacific_islander", label: "Native Hawaiian or Pacific Islander" },
  { id: "other", label: "Other" },
];

export default function Demographics({ formData, setFormData, onNext }) {
  const [raceSelections, setRaceSelections] = useState(formData.race_ethnicity || []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const toggleRace = (id) => {
    const updated = raceSelections.includes(id)
      ? raceSelections.filter((r) => r !== id)
      : [...raceSelections, id];
    setRaceSelections(updated);
    setFormData({ ...formData, race_ethnicity: updated });
  };

  return (
    <>
      <h2 className="screen-heading">Patient Information</h2>

      <label className="field">
        Age
        <input type="number" name="age" value={formData.age || ""} onChange={handleChange} />
      </label>

      <fieldset className="field" style={{ border: "none", padding: 0, margin: 0 }}>
        <legend style={{ fontWeight: 500, color: "#475569", marginBottom: 6 }}>Race / Ethnicity</legend>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 16px" }}>
          {RACE_OPTIONS.map((opt) => (
            <label key={opt.id} style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: 14 }}>
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

      <div style={{ display: "flex", gap: 10 }}>
        <label className="field" style={{ flex: 1 }}>
          Height (ft)
          <input type="number" name="heightFeet" value={formData.heightFeet || ""} onChange={handleChange} />
        </label>
        <label className="field" style={{ flex: 1 }}>
          Height (in)
          <input type="number" name="heightInches" value={formData.heightInches || ""} onChange={handleChange} />
        </label>
        <label className="field" style={{ flex: 1 }}>
          Weight (lbs)
          <input type="number" name="weight" value={formData.weight || ""} onChange={handleChange} />
        </label>
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <label className="field" style={{ flex: 1 }}>
          Zip Code
          <input type="text" name="zipCode" value={formData.zipCode || ""} onChange={handleChange} maxLength={5} />
        </label>
        <label className="field" style={{ flex: 1 }}>
          Search Radius (miles)
          <input type="number" name="searchRadius" value={formData.searchRadius || ""} onChange={handleChange} />
        </label>
      </div>

      <button className="btn-primary" onClick={onNext}>Next</button>
    </>
  );
}
