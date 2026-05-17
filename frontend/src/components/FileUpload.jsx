import { useRef } from "react";
import { uploadAndParse } from "../api";

export default function FileUpload({ uploadState, setUploadState, onComplete, onBack }) {
  const inputRef = useRef(null);
  const { files, extractions } = uploadState;

  const handleFiles = async (e) => {
    const selected = Array.from(e.target.files || []);
    if (!selected.length) return;

    const batchId = Date.now();
    const newEntries = selected.map((file, i) => ({
      id: `${batchId}-${i}-${file.name}`,
      name: file.name,
      status: "uploading",
      error: null,
    }));

    setUploadState((prev) => ({
      ...prev,
      files: [...prev.files, ...newEntries],
    }));

    for (let i = 0; i < selected.length; i++) {
      const file = selected[i];
      const entryId = newEntries[i].id;
      try {
        const result = await uploadAndParse(file);
        setUploadState((prev) => ({
          ...prev,
          files: prev.files.map((f) => (f.id === entryId ? { ...f, status: "done", error: null } : f)),
          extractions: [...prev.extractions, result.data],
        }));
      } catch (err) {
        setUploadState((prev) => ({
          ...prev,
          files: prev.files.map((f) =>
            f.id === entryId ? { ...f, status: "error", error: err.message } : f,
          ),
        }));
      }
    }
    if (inputRef.current) inputRef.current.value = "";
  };

  const hasSuccess = files.some((f) => f.status === "done");
  const uploading = files.some((f) => f.status === "uploading");

  return (
    <div className="demographics-screen">
      <h2 className="demographics-screen-title">Upload your documents below!</h2>
      <p className="onboarding-lead">
        Upload discharge summaries, lab reports, or triage notes (PDF). You can upload multiple files.
      </p>

      <div className="onboarding-upload-panel">
        <fieldset className="demo-input-shell">
          <legend className="demo-input-label">PDF reports</legend>
          <div className="demo-upload-zone" onClick={() => inputRef.current?.click()} role="presentation">
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFiles}
              style={{ display: "none" }}
            />
            <p>Click to select PDF files</p>
          </div>

          {files.length > 0 && (
            <ul className="file-status-list">
              {files.map((f) => (
                <li key={f.id}>
                  {f.status === "uploading" && <span style={{ color: "#3b82f6" }}>⏳ </span>}
                  {f.status === "done" && <span style={{ color: "#16a34a" }}>✓ </span>}
                  {f.status === "error" && <span style={{ color: "#dc2626" }}>✗ </span>}
                  <span>{f.name}</span>
                  {f.error && (
                    <span style={{ color: "#dc2626", fontSize: "0.8125rem" }}> — {f.error}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </fieldset>
      </div>

      <div className="onboarding-upload-actions">
        <button
          type="button"
          className="hero-cta onboarding-cta"
          disabled={uploading || !hasSuccess}
          onClick={() => onComplete(extractions)}
        >
          {uploading ? "Processing..." : "Continue to Review"}
        </button>
        <button
          type="button"
          className="hero-cta onboarding-cta onboarding-cta--outline"
          onClick={() => onComplete([])}
          disabled={uploading}
        >
          Skip, I have no documents
        </button>
        <button type="button" className="hero-cta onboarding-cta onboarding-cta--outline" onClick={onBack} disabled={uploading}>
          Back
        </button>
      </div>
    </div>
  );
}
