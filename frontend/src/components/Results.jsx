export default function Results({ setCurrentView, trials }) {
  if (!trials || trials.length === 0) {
    return (
      <div style={{ width: '100%', maxWidth: 800 }}>
        <h2 style={{ color: '#d6336c' }}>No Matches Found</h2>
        <p style={{ color: '#475569' }}>
          We couldn't find any matching clinical trials for your profile. Try adjusting your information and searching again.
        </p>
        <button className="btn-primary" onClick={() => setCurrentView('home')} style={{ marginTop: 20 }}>Start Over</button>
      </div>
    )
  }

  return (
    <div style={{ width: '100%', maxWidth: 800 }}>
      <h1 style={{ color: '#d6336c', marginBottom: 10 }}>Your Clinical Trial Matches</h1>
      <p style={{ color: '#475569', marginBottom: 24, fontSize: 14 }}>
        Top {trials.length} trials ranked by relevance to your profile.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {trials.map((trial, idx) => (
          <div key={trial.nct_id || idx} className="trial-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: '0 0 4px', fontSize: 16, color: '#1e293b' }}>{trial.title}</h3>
                <a
                  href={`https://clinicaltrials.gov/study/${trial.nct_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ fontSize: 12, color: '#3b82f6' }}
                >
                  {trial.nct_id}
                </a>
              </div>
              <div className="score-badge">{trial.match_score}%</div>
            </div>

            {trial.phases && trial.phases.length > 0 && (
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                Phase: {trial.phases.join(', ')}
              </div>
            )}

            {trial.summary && (
              <p style={{ fontSize: 13, color: '#475569', margin: '8px 0 0', lineHeight: 1.4 }}>
                {trial.summary.length > 200 ? trial.summary.slice(0, 200) + '...' : trial.summary}
              </p>
            )}

            {trial.match_reasons && trial.match_reasons.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
                {trial.match_reasons.map((r, i) => (
                  <span key={i} className="reason-pill">{r}</span>
                ))}
              </div>
            )}

            {trial.disqualifiers && trial.disqualifiers.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                {trial.disqualifiers.map((dq, i) => (
                  <span key={i} className="dq-pill">{dq}</span>
                ))}
              </div>
            )}

            {trial.locations && trial.locations.length > 0 && (
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 8 }}>
                📍 {trial.locations.slice(0, 3).map((loc, i) => (
                  <span key={i}>
                    {[loc.city, loc.state, loc.country].filter(Boolean).join(', ')}
                    {i < Math.min(trial.locations.length, 3) - 1 ? ' · ' : ''}
                  </span>
                ))}
                {trial.locations.length > 3 && ` +${trial.locations.length - 3} more`}
              </div>
            )}
          </div>
        ))}
      </div>

      <button className="btn-primary" onClick={() => setCurrentView('home')} style={{ marginTop: 24 }}>
        Start Over
      </button>
    </div>
  )
}
