export default function Home({ setCurrentView }) {
  const buttonStyle = {
    padding: '16px 32px', backgroundColor: '#d6336c', color: 'white', border: 'none', 
    borderRadius: '8px', fontSize: '18px', fontWeight: 'bold', cursor: 'pointer'
  }

  return (
    <div style={{ textAlign: 'center', maxWidth: '600px' }}>
      <h1 style={{ color: '#d6336c', fontSize: '48px', marginBottom: '10px' }}>❤️ Heart2Heart</h1>
      <p style={{ fontSize: '20px', color: '#475569', marginBottom: '30px', lineHeight: '1.6' }}>
        Connecting maternal health patients to life-saving clinical trials using advanced document parsing.
      </p>
      <button onClick={() => setCurrentView('onboarding')} style={buttonStyle}>
        Find Trials Now
      </button>
    </div>
  )
}