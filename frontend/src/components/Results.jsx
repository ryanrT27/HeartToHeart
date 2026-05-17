import { commaList, formatLocation, scalarDisplay } from "../formatDisplay";

export default function Results({ onGoHome, trials }) {
  if (!trials || trials.length === 0) {
    return (
      <div className="demographics-screen results-screen">
        <h2 className="demographics-screen-title">No Matches Found</h2>
        <p className="onboarding-lead">
          We couldn&apos;t find any clinical trials that match your profile yet. Try adjusting your information and
          searching again.
        </p>
        <div className="results-actions">
          <button type="button" className="hero-cta onboarding-cta" onClick={onGoHome}>
            Start over
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="demographics-screen results-screen">
      <h2 className="demographics-screen-title">Your Clinical Trial Matches</h2>
      <p className="onboarding-lead">
        Top {trials.length} {trials.length === 1 ? "trial" : "trials"} ranked by relevance to your profile.
      </p>

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
        <button type="button" className="hero-cta onboarding-cta" onClick={onGoHome}>
          Start over
        </button>
      </div>
    </div>
  );
}
