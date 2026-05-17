import { commaList, formatLocation, scalarDisplay } from "../formatDisplay";

const HEART_PATH =
  "M27.5747 22.8418C37.4898 16.8229 51.7046 17.6782 67.7665 27.0267C78.2835 13.6756 90.6891 8.55244 101.63 11.1626C113.021 13.8802 121.589 24.6938 124.103 40.3421C126.656 56.2357 119.917 74.3548 110.999 88.5804C106.51 95.7414 101.384 102.054 96.4096 106.755C91.535 111.361 86.4655 114.745 82.0739 115.45C76.781 116.3 70.2554 114.881 63.5836 112.085C56.846 109.261 49.6728 104.913 42.9706 99.5378C29.6475 88.8532 17.7241 73.7282 15.1719 57.8386C12.6616 42.2103 17.2294 29.1219 27.5747 22.8418Z";

function MatchHeartBadge({ score, uid }) {
  const pct = score == null ? "—" : String(score);
  const gid = `trial-heart-grad-${uid}`;

  return (
    <div className="trial-match-heart" role="img" aria-label={`${pct}% match`}>
      <div className="trial-match-heart-visual">
        <svg
          className="trial-match-heart-svg"
          width="105.327"
          height="96.963"
          viewBox="0 0 140 135"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="500" y2="500" gradientUnits="userSpaceOnUse">
              <stop stopColor="#CA5065" />
              <stop offset="1" stopColor="#CD4E63" />
            </linearGradient>
          </defs>
          <path fill={`url(#${gid})`} stroke="#FFF0F2" strokeWidth="5" d={HEART_PATH} />
        </svg>
        <div className="trial-match-heart-caption" aria-hidden="true">
          <span className="trial-match-heart-pct">{pct}%</span>
          <span className="trial-match-heart-word">match</span>
        </div>
      </div>
    </div>
  );
}

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
        {trials.map((trial, idx) => {
          const hasTags =
            (trial.match_reasons && trial.match_reasons.length > 0) ||
            (trial.disqualifiers && trial.disqualifiers.length > 0);

          return (
            <article key={trial.nct_id || idx} className="trial-card">
              <MatchHeartBadge score={trial.match_score} uid={idx} />

              <div className="trial-card-inner">
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
                </div>

                {trial.phases && trial.phases.length > 0 && (
                  <div className="trial-meta-line">Phase: {commaList(trial.phases)}</div>
                )}

                {trial.summary && (
                  <p className="trial-summary">
                    {trial.summary.length > 200 ? `${trial.summary.slice(0, 200)}…` : trial.summary}
                  </p>
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

                {hasTags && (
                  <div className="trial-card-tags">
                    {trial.match_reasons?.map((r, i) => (
                      <span key={`r-${i}`} className="reason-pill">
                        {scalarDisplay(r)}
                      </span>
                    ))}
                    {trial.disqualifiers?.map((dq, i) => (
                      <span key={`dq-${i}`} className="dq-pill">
                        {scalarDisplay(dq)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>

      <div className="results-actions">
        <button type="button" className="hero-cta onboarding-cta" onClick={onRestart}>
          Restart
        </button>
      </div>
    </div>
  );
}
