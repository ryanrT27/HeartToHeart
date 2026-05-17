export default function Results({ setCurrentView, trials }) {
  const buttonStyle = {
    padding: '14px', backgroundColor: '#d6336c', color: 'white', border: 'none', 
    borderRadius: '8px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer'
  }

  return (
    <div style={{ width: '100%', maxWidth: '800px' }}>
      <h1 style={{ color: '#d6336c', marginBottom: '10px' }}>Your Clinical Trial Matches</h1>
      <p style={{ color: '#475569', marginBottom: '30px' }}>Based on your demographics and medical documents, we found these active studies:</p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {trials.map((trial, index) => (
          <div key={index} style={{ backgroundColor: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', borderLeft: '6px solid #d6336c' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#1e293b' }}>{trial.title}</h3>
            <p style={{ margin: '0 0 15px 0', color: '#64748b' }}>📍 {trial.location || "Location not specified"}</p>
            <button style={{...buttonStyle, backgroundColor: '#4f46e5', padding: '10px 20px'}}>View Details</button>
          </div>
        ))}
      </div>

      <button onClick={() => setCurrentView('home')} style={{...buttonStyle, backgroundColor: '#94a3b8', marginTop: '40px'}}>
        Start Over
      </button>
    </div>
  )
}