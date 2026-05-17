import { useRef, useState } from "react";
import { uploadAndParse } from "../api";

export default function FileUpload({ onComplete, onBack }) {
  const [files, setFiles] = useState([]);
  const [extractions, setExtractions] = useState([]);
  const inputRef = useRef(null);

  const handleFiles = async (e) => {
    const selected = Array.from(e.target.files);
    if (!selected.length) return;

    const newFiles = selected.map((f) => ({ name: f.name, status: "uploading", error: null }));
    setFiles((prev) => [...prev, ...newFiles]);

    for (let i = 0; i < selected.length; i++) {
      const file = selected[i];
      const idx = files.length + i;
      try {
        const result = await uploadAndParse(file);
        setFiles((prev) => prev.map((f, j) => (j === idx ? { ...f, status: "done" } : f)));
        setExtractions((prev) => [...prev, result.data]);
      } catch (err) {
        setFiles((prev) =>
          prev.map((f, j) => (j === idx ? { ...f, status: "error", error: err.message } : f))
        );
      }
    }
    if (inputRef.current) inputRef.current.value = "";
  };

  const hasSuccess = files.some((f) => f.status === "done");
  const uploading = files.some((f) => f.status === "uploading");

  return (
    <>
      <h2 className="screen-heading">Upload Documents</h2>
      <p style={{ color: "#475569", margin: 0 }}>
        Upload discharge summaries, lab reports, or triage notes (PDF). You can upload multiple files.
      </p>

      <div
        style={{
          padding: "40px 20px",
          border: "2px dashed #cbd5e1",
          borderRadius: 8,
          textAlign: "center",
          cursor: "pointer",
        }}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFiles}
          style={{ display: "none" }}
        />
        <p style={{ margin: 0, color: "#64748b" }}>Click to select PDF files</p>
      </div>

      {files.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 }}>
          {files.map((f, i) => (
            <li key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14 }}>
              {f.status === "uploading" && <span style={{ color: "#3b82f6" }}>⏳</span>}
              {f.status === "done" && <span style={{ color: "#16a34a" }}>✓</span>}
              {f.status === "error" && <span style={{ color: "#dc2626" }}>✗</span>}
              <span>{f.name}</span>
              {f.error && <span style={{ color: "#dc2626", fontSize: 12 }}>— {f.error}</span>}
            </li>
          ))}
        </ul>
      )}

      <div style={{ display: "flex", gap: 10, flexDirection: "column" }}>
        <button
          className="btn-primary"
          disabled={uploading || !hasSuccess}
          onClick={() => onComplete(extractions)}
        >
          {uploading ? "Processing..." : "Continue to Review"}
        </button>
        <button
          className="btn-link"
          onClick={() => onComplete([])}
          disabled={uploading}
        >
          Skip — I have no documents
        </button>
        <button className="btn-back" onClick={onBack} disabled={uploading}>Back</button>
      </div>
    </>
  );
}
