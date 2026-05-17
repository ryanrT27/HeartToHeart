import { useState } from 'react'

export default function Onboarding({ setCurrentView, setTrials }) {
  const [screen, setScreen] = useState(1)
  const [formData, setFormData] = useState({
    age: '', race: '', heightFeet: '', heightInches: '', weight: '', zipCode: '',
    searchRadius: '', pregnancyStatus: '', weeks: '', babyCount: '', breastfeeding: '', smoking: '',
  })

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setScreen(5) // Show loading screen

    const uploadData = new FormData()
    uploadData.append("file", file)
    uploadData.append("patient_info", JSON.stringify(formData))

    try {
      const response = await fetch("http://localhost:8000/api/upload-and-parse", {
        method: "POST", body: uploadData
      })
      const data = await response.json()
      
      setTrials(data.trials || [
        { title: "Mock Trial: Postpartum Preeclampsia Study", link: "#", location: "Los Angeles, CA" },
        { title: "Mock Trial: Gestational Diabetes Follow-up", link: "#", location: "Irvine, CA" }
      ])
      setCurrentView('results') 
      
    } catch (error) {
      console.error("Backend error:", error)
      setCurrentView('results')
    }
  }

  // Styles just for the card
  const cardStyle = {
    backgroundColor: '#ffffff', padding: '40px', borderRadius: '16px',
    boxShadow: '0 10px 25px rgba(0,0,0,0.05)', width: '100%', maxWidth: '500px',
    display: 'flex', flexDirection: 'column', gap: '20px'
  }
  const headingStyle = { margin: 0, color: '#1e293b', fontSize: '24px', paddingBottom: '10px' }
  const labelStyle = { display: 'flex', flexDirection: 'column', fontWeight: '500', color: '#475569', gap: '6px', flex: 1 }
  const inputStyle = { padding: '12px', borderRadius: '8px', border: '1px solid #cbd5e1', width: '100%', boxSizing: 'border-box', fontSize: '16px' }
  const buttonStyle = { padding: '14px', backgroundColor: '#d6336c', color: 'white', border: 'none', borderRadius: '8px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' }

  return (
    <div style={cardStyle}>
      <h1 style={{ color: '#d6336c', margin: '0 0 10px 0', textAlign: 'center' }}>Heart2Heart</h1>
      
      {screen === 1 && (
        <>
          <h2 style={headingStyle}>Patient Information</h2>
          <label style={labelStyle}>Age: <input type="number" name="age" onChange={handleInputChange} style={inputStyle} /></label>
          <label style={labelStyle}>Race/Ethnicity: <input type="text" name="race" onChange={handleInputChange} style={inputStyle} /></label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <label style={labelStyle}>Height (ft): <input type="number" name="heightFeet" onChange={handleInputChange} style={inputStyle}/></label>
            <label style={labelStyle}>Height (in): <input type="number" name="heightInches" onChange={handleInputChange} style={inputStyle}/></label>
            <label style={labelStyle}>Weight (lbs): <input type="number" name="weight" onChange={handleInputChange} style={inputStyle}/></label>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <label style={labelStyle}>Zip Code: <input type="text" name="zipCode" onChange={handleInputChange} style={inputStyle}/></label>
            <label style={labelStyle}>Radius: <input type="number" name="searchRadius" onChange={handleInputChange} style={inputStyle}/></label>
          </div>
          <button onClick={() => setScreen(2)} style={buttonStyle}>Next</button>
        </>
      )}

      {screen === 2 && (
        <>
          <h2 style={headingStyle}>Pregnancy Status</h2>
          {!formData.pregnancyStatus ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button onClick={() => setFormData({ ...formData, pregnancyStatus: 'pregnant' })} style={{...buttonStyle, backgroundColor: '#4f46e5'}}>Currently Pregnant</button>
              <button onClick={() => setFormData({ ...formData, pregnancyStatus: 'delivered' })} style={{...buttonStyle, backgroundColor: '#4f46e5'}}>Recently Delivered</button>
            </div>
          ) : (
            <>
              <p><strong>Status:</strong> {formData.pregnancyStatus === 'pregnant' ? "Currently Pregnant" : "Postpartum"}</p>
              <label style={labelStyle}>Timeframe:<input type="text" name="weeks" onChange={handleInputChange} style={inputStyle} /></label>
              <label style={labelStyle}>Pregnancy Type:
                <select name="babyCount" onChange={handleInputChange} style={inputStyle}>
                  <option value="">Select...</option><option value="single">Single Baby</option><option value="multiple">Multiple</option>
                </select>
              </label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={() => setScreen(1)} style={{...buttonStyle, backgroundColor: '#94a3b8', flex: 1}}>Back</button>
                <button onClick={() => setScreen(3)} style={{...buttonStyle, flex: 1}}>Next</button>
              </div>
            </>
          )}
        </>
      )}

      {screen === 3 && (
        <>
          <h2 style={headingStyle}>Health History</h2>
          <label style={labelStyle}>Breastfeeding Status:
            <select name="breastfeeding" onChange={handleInputChange} style={inputStyle}>
              <option value="">Select...</option><option value="yes">Yes</option><option value="no">No</option><option value="partial">Partial</option>
            </select>
          </label>
          <label style={labelStyle}>Smoking History:
            <select name="smoking" onChange={handleInputChange} style={inputStyle}>
              <option value="">Select...</option><option value="never">Never</option><option value="former">Former</option><option value="current">Current</option>
            </select>
          </label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => setScreen(2)} style={{...buttonStyle, backgroundColor: '#94a3b8', flex: 1}}>Back</button>
            <button onClick={() => setScreen(4)} style={{...buttonStyle, flex: 1}}>Next: Documents</button>
          </div>
        </>
      )}

      {screen === 4 && (
        <>
          <h2 style={headingStyle}>Upload Documents</h2>
          <input type="file" onChange={handleFileUpload} style={{ padding: '40px 20px', border: '2px dashed #cbd5e1', borderRadius: '8px', textAlign: 'center', cursor: 'pointer' }} />
          <button onClick={() => setScreen(3)} style={{...buttonStyle, backgroundColor: '#94a3b8'}}>Back</button>
        </>
      )}

      {screen === 5 && (
        <div style={{ textAlign: 'center' }}>
          <h2 style={headingStyle}>Processing...</h2>
          <p style={{ color: '#475569' }}>Securely parsing documents.</p>
        </div>
      )}
    </div>
  )
}