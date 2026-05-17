const BASE = "http://localhost:8000/api";

function detailMessage(body, fallback) {
  const d = body?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join("; ") || fallback;
  if (d && typeof d === "object") return JSON.stringify(d);
  return fallback;
}

export async function uploadAndParse(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload-and-parse`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(detailMessage(err, res.statusText || "Upload failed"));
  }
  return res.json();
}

export async function submitData(profile) {
  const res = await fetch(`${BASE}/submit-data`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(detailMessage(err, res.statusText || "Submit failed"));
  }
  return res.json();
}

export async function matchTrials(profile) {
  const res = await fetch(`${BASE}/match-trials`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(detailMessage(err, res.statusText || "Matching failed"));
  }
  return res.json();
}

export async function getTrialsCount() {
  const res = await fetch(`${BASE}/trials/count`);
  return res.json();
}
