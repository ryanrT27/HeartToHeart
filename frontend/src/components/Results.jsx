import { commaList, formatLocation, scalarDisplay } from "../formatDisplay";

function csvEscape(value) {
  const s = value == null ? "" : String(value);
  return `"${s.replace(/"/g, '""')}"`;
}

function downloadMatchListCsv(trials) {
  const headers = ["NCT ID", "Title", "Match %", "Phases", "Summary", "ClinicalTrials.gov URL"];
  const rows = trials.map((t) => [
    t.nct_id ?? "",
    t.title ?? "",
    t.match_score ?? "",
    Array.isArray(t.phases) ? t.phases.join("; ") : "",
    (t.summary ?? "").replace(/\s+/g, " ").trim(),
    t.nct_id ? `https://clinicaltrials.gov/study/${t.nct_id}` : "",
  ]);
  const lines = [headers.join(","), ...rows.map((r) => r.map(csvEscape).join(","))];
  const csv = `\uFEFF${lines.join("\n")}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `heart2heart-trial-matches-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function Results({ onRestart, trials }) {
  if (!trials || trials.length === 0) {
    return (
      <div className="demographics-screen results-screen">
        <h2 className="demographics-screen-title results-match-headline">
          We&apos;ve found <span className="results-match-emphasis results-match-num">0</span>{" "}
          <span className="results-match-emphasis">matches</span> for you!
        </h2>
        <p className="onboarding-lead">
          None of the strongest matches for your profile scored above 70%, or your profile needs a bit more detail.
          Try adjusting your information and searching again.
        </p>
        <p className="results-score-explainer">
          We rank trials using weighted factors (age, pregnancy or postpartum timing, diagnoses, biomarkers, vitals,
          trial inclusion/exclusion wording, and whether sites run in your country). Each factor adds partial credit when
          your data lines up with the trial; certain exclusions set the match to zero. We take your top 20 candidates,
          then show only those scoring above 70%.
        </p>
        <div className="results-actions">
          <button type="button" className="hero-cta onboarding-cta" onClick={onRestart}>
            Restart
          </button>
        </div>
      </div>
    );
  }

  const n = trials.length;

  return (
    <div className="demographics-screen results-screen">
      <h2 className="demographics-screen-title results-match-headline">
        We&apos;ve found <span className="results-match-emphasis results-match-num">{n}</span>{" "}
        <span className="results-match-emphasis">{n === 1 ? "match" : "matches"}</span> for you!
      </h2>

      <div className="results-export-row">
        <button type="button" className="results-export-btn" onClick={() => downloadMatchListCsv(trials)}>
          <svg className="results-export-icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path
              fill="currentColor"
              d="M11 3v10.17l-2.59-2.58L7 12l5 5 5-5-1.41-1.41L13 13.17V3h-2zm8 16H5v2h14v-2z"
            />
          </svg>
          Export match list
        </button>
      </div>

      <div className="results-trial-list">
        {trials.map((trial, idx) => (
          <article key={trial.nct_id || idx} className="trial-card">
            <div className="trial-card-header">
              <div className="trial-card-main">
                <h3 className="trial-card-title">{trial.title}</h3>
                <a
                  className="trial-nct-link"
                  href={`https://clinicaltrials.gov/study/${trial.nct_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {trial.nct_id}
                </a>
              </div>
              <div className="score-badge">{trial.match_score}%</div>
            </div>

            {trial.phases && trial.phases.length > 0 && (
              <div className="trial-meta-line">Phase: {commaList(trial.phases)}</div>
            )}

            {trial.summary && (
              <p className="trial-summary">
                {trial.summary.length > 200 ? `${trial.summary.slice(0, 200)}…` : trial.summary}
              </p>
            )}

            {trial.match_reasons && trial.match_reasons.length > 0 && (
              <div className="trial-pill-row">
                {trial.match_reasons.map((r, i) => (
                  <span key={i} className="reason-pill">
                    {scalarDisplay(r)}
                  </span>
                ))}
              </div>
            )}

            {trial.disqualifiers && trial.disqualifiers.length > 0 && (
              <div className="trial-pill-row">
                {trial.disqualifiers.map((dq, i) => (
                  <span key={i} className="dq-pill">
                    {scalarDisplay(dq)}
                  </span>
                ))}
              </div>
            )}

            {trial.locations && trial.locations.length > 0 && (
              <div className="trial-location-line">
                <strong className="trial-location-label">Locations: </strong>
                {trial.locations.slice(0, 3).map((loc, i) => (
                  <span key={i}>
                    {formatLocation(loc)}
                    {i < Math.min(trial.locations.length, 3) - 1 ? " · " : ""}
                  </span>
                ))}
                {trial.locations.length > 3 && ` +${trial.locations.length - 3} more`}
              </div>
            )}
          </article>
        ))}
      </div>

      <div className="results-actions">
        <button type="button" className="hero-cta onboarding-cta" onClick={onRestart}>
          Restart
        </button>
      </div>
    </div>
  );
}
