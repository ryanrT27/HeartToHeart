/** Persist in-flight onboarding answers (sessionStorage — cleared when the tab closes). */

export const ASSESSMENT_STORAGE_KEY = "heart2heart-assessment-v1";

export const DEFAULT_ASSESSMENT_FORM = {
  age: "",
  race_ethnicity: [],
  heightFeet: "",
  heightInches: "",
  weight: "",
  country: "",
  subdivision: "",
  genderIdentity: "",
  pregnancyStatus: "",
  currentWeek: "",
  pregnancyType: "",
  deliveryDate: "",
  deliveryType: "",
  breastfeeding: "",
  smoking: "",
};

const VERSION = 1;

function normalizeUploadState(raw) {
  const filesIn = Array.isArray(raw?.files) ? raw.files : [];
  const extractionsIn = Array.isArray(raw?.extractions) ? raw.extractions : [];

  const files = filesIn
    .filter((f) => f && f.status !== "uploading")
    .map((f, i) => ({
      id: f.id ?? `restored-${i}-${f.name ?? "file"}`,
      name: f.name ?? "file",
      status: f.status === "done" || f.status === "error" ? f.status : "error",
      error: f.error ?? (f.status === "uploading" ? "Upload was interrupted. Select the file again if needed." : null),
    }));

  const doneCount = files.filter((f) => f.status === "done").length;
  const extractions = extractionsIn.slice(0, doneCount);

  return { files, extractions };
}

function sanitizeLoaded(data) {
  if (!data || data.v !== VERSION) return null;

  let screen = Number(data.screen);
  if (!Number.isFinite(screen) || screen < 1 || screen > 6) return null;

  if (screen === 6) screen = 5;
  if (screen === 5 && !data.profile) screen = 4;

  const formData = { ...DEFAULT_ASSESSMENT_FORM, ...(data.formData || {}) };
  if (!Array.isArray(formData.race_ethnicity)) formData.race_ethnicity = [];

  const uploadState = normalizeUploadState(data.uploadState);

  return {
    screen,
    formData,
    profile: data.profile ?? null,
    uploadState,
  };
}

export function loadAssessmentSession() {
  try {
    const raw = sessionStorage.getItem(ASSESSMENT_STORAGE_KEY);
    if (!raw) return null;
    return sanitizeLoaded(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function saveAssessmentSession(payload) {
  try {
    sessionStorage.setItem(
      ASSESSMENT_STORAGE_KEY,
      JSON.stringify({
        v: VERSION,
        screen: payload.screen,
        formData: payload.formData,
        profile: payload.profile,
        uploadState: payload.uploadState,
      }),
    );
  } catch {
    /* quota / private mode */
  }
}

export function clearAssessmentSession() {
  try {
    sessionStorage.removeItem(ASSESSMENT_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}
