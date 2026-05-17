const BASE = "http://localhost:8000/api";

export async function uploadAndParse(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload-and-parse`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
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
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Submit failed");
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
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Matching failed");
  }
  return res.json();
}

export async function getTrialsCount() {
  const res = await fetch(`${BASE}/trials/count`);
  return res.json();
}
