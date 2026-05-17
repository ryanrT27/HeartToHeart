/** Turn arrays or nested LLM junk into readable comma-separated text. */
export function commaList(value) {
  if (value == null) return "";
  if (!Array.isArray(value)) return scalarDisplay(value);
  return value.map(scalarDisplay).filter(Boolean).join(", ");
}

export function scalarDisplay(v) {
  if (v == null || v === "") return "";
  const t = typeof v;
  if (t === "string" || t === "number" || t === "boolean") return String(v);
  if (t === "object") {
    const pick =
      v.label ??
      v.name ??
      v.value ??
      v.text ??
      v.race ??
      v.ethnicity ??
      v.phase;
    if (pick != null && typeof pick !== "object") return String(pick);
    const firstStr = Object.values(v).find((x) => typeof x === "string" || typeof x === "number");
    if (firstStr != null) return String(firstStr);
    return "";
  }
  return String(v);
}

export function formatLocation(loc) {
  if (!loc || typeof loc !== "object") return "";
  return [loc.city, loc.state, loc.country].map(scalarDisplay).filter(Boolean).join(", ");
}
