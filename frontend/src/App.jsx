import { useState } from 'react'
import Home from './components/Home'
import Onboarding from './components/Onboarding'
import Results from './components/Results'

function App() {
  // THE TRAFFIC COP
  const [currentView, setCurrentView] = useState('home') 
  // STORE THE API RESULTS
  const [trials, setTrials] = useState([]) 

  // Global Styles for the background
  const containerStyle = {
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    minHeight: '100vh', width: '100vw', margin: 0, padding: '20px', boxSizing: 'border-box',
    backgroundColor: '#f8fafc', fontFamily: 'system-ui, sans-serif'
  }

  return (
    <div style={containerStyle}>
      {currentView === 'home' && (
        <Home setCurrentView={setCurrentView} />
      )}
      
      {currentView === 'onboarding' && (
        <Onboarding setCurrentView={setCurrentView} setTrials={setTrials} />
      )}
      
      {currentView === 'results' && (
        <Results setCurrentView={setCurrentView} trials={trials} />
      )}
    </div>
  )
}

export default App