import { useState } from 'react'
import Demographics from './Demographics'
import Pregnancy from './Pregnancy'
import HealthHistory from './HealthHistory'
import FileUpload from './FileUpload'
import ReviewEdit from './ReviewEdit'
import { submitData, matchTrials } from '../api'

function buildProfile(formData, extractions) {
  const ft = parseFloat(formData.heightFeet) || 0
  const inches = parseFloat(formData.heightInches) || 0
  const height_cm = (ft * 12 + inches) * 2.54 || null
  const weight_kg = formData.weight ? parseFloat(formData.weight) / 2.205 : null
  const age = formData.age ? parseInt(formData.age) : null

  let bmi = null
  if (height_cm && weight_kg) {
    bmi = Math.round((weight_kg / (height_cm / 100) ** 2) * 10) / 10
  }

  const profile = {
    demographics: {
      age,
      race_ethnicity: formData.race_ethnicity || [],
      height_cm,
      weight_kg,
      bmi,
      zip_code: formData.zipCode || null,
      radius_miles: formData.searchRadius ? parseInt(formData.searchRadius) : null,
    },
    pregnancy: {
      currently_pregnant: formData.pregnancyStatus === 'pregnant' ? true : formData.pregnancyStatus === 'delivered' ? false : null,
      current_week: formData.currentWeek ? parseInt(formData.currentWeek) : null,
      pregnancy_type: formData.pregnancyStatus === 'pregnant' ? (formData.pregnancyType || null) : null,
      delivery_date: formData.deliveryDate || null,
      delivery_type: formData.pregnancyStatus === 'delivered' ? (formData.deliveryType || null) : null,
    },
    health_history: {
      currently_breastfeeding: formData.breastfeeding === 'yes' ? true : formData.breastfeeding === 'no' ? false : null,
      smoking_status: formData.smoking || null,
    },
    diagnoses: {
      preeclampsia: false, preeclampsia_onset: null, hellp_syndrome: false,
      gestational_hypertension: false, peripartum_cardiomyopathy: false,
      gestational_diabetes: false, preterm_delivery: false, delivery_week: null,
    },
    biomarkers: Object.fromEntries(
      ['sflt1_plgf_ratio','nt_probnp','troponin_t','proteinuria','hba1c','hemoglobin','fasting_glucose','total_cholesterol']
        .map(k => [k, { value: null, unit: null, high_risk: null }])
    ),
    vitals: {
      systolic_bp: { value: null, unit: null, flag: null, severe: null },
      diastolic_bp: { value: null, unit: null, flag: null, severe: null },
      resting_heart_rate: { value: null, unit: null, flag: null },
    },
  }

  for (const ext of extractions) {
    if (!ext) continue
    const ed = ext.diagnoses || {}
    for (const key of Object.keys(profile.diagnoses)) {
      if (typeof profile.diagnoses[key] === 'boolean') {
        if (ed[key] === true) profile.diagnoses[key] = true
      } else if (profile.diagnoses[key] == null && ed[key] != null) {
        profile.diagnoses[key] = ed[key]
      }
    }
    const eb = ext.biomarkers || {}
    for (const key of Object.keys(profile.biomarkers)) {
      if (profile.biomarkers[key].value == null && eb[key]?.value != null)
        profile.biomarkers[key] = { ...eb[key] }
    }
    const ev = ext.vitals || {}
    for (const key of Object.keys(profile.vitals)) {
      if (profile.vitals[key].value == null && ev[key]?.value != null)
        profile.vitals[key] = { ...ev[key] }
    }
    const edemo = ext.demographics || {}
    for (const key of Object.keys(profile.demographics)) {
      if (profile.demographics[key] == null && edemo[key] != null)
        profile.demographics[key] = edemo[key]
    }
    const epreg = ext.pregnancy || {}
    for (const key of Object.keys(profile.pregnancy)) {
      if (profile.pregnancy[key] == null && epreg[key] != null)
        profile.pregnancy[key] = epreg[key]
    }
    const ehh = ext.health_history || {}
    for (const key of Object.keys(profile.health_history)) {
      if (profile.health_history[key] == null && ehh[key] != null)
        profile.health_history[key] = ehh[key]
    }
  }

  return profile
}

export default function Onboarding({ setCurrentView, setTrials }) {
  const [screen, setScreen] = useState(1)
  const [formData, setFormData] = useState({
    age: '', race_ethnicity: [], heightFeet: '', heightInches: '', weight: '',
    zipCode: '', searchRadius: '', pregnancyStatus: '', currentWeek: '',
    pregnancyType: '', deliveryDate: '', deliveryType: '', breastfeeding: '', smoking: '',
  })
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleFilesDone = (extractions) => {
    setProfile(buildProfile(formData, extractions))
    setScreen(5)
  }

  const handleSubmit = async () => {
    setError(null)
    setLoading(true)
    setScreen(6)
    try {
      const submitRes = await submitData(profile)
      const matchRes = await matchTrials(submitRes.confirmed_data)
      setTrials(matchRes.trials)
      setCurrentView('results')
    } catch (err) {
      setError(err.message)
      setScreen(5)
    } finally {
      setLoading(false)
    }
  }

  const errorBanner = error && (
    <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '10px 14px', borderRadius: 8, fontSize: 14, marginBottom: 8, display: 'flex', alignItems: 'center' }}>
      {error}
      <button onClick={() => setError(null)} style={{ marginLeft: 8, background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>×</button>
    </div>
  )

  const cardStyle = {
    backgroundColor: '#ffffff', padding: '40px', borderRadius: '16px',
    boxShadow: '0 10px 25px rgba(0,0,0,0.05)', width: '100%', maxWidth: '560px',
    display: 'flex', flexDirection: 'column', gap: '16px',
  }

  return (
    <div style={cardStyle}>
      {errorBanner}
      {screen === 1 && <Demographics formData={formData} setFormData={setFormData} onNext={() => setScreen(2)} />}
      {screen === 2 && <Pregnancy formData={formData} setFormData={setFormData} onNext={() => setScreen(3)} onBack={() => setScreen(1)} />}
      {screen === 3 && <HealthHistory formData={formData} setFormData={setFormData} onNext={() => setScreen(4)} onBack={() => setScreen(2)} />}
      {screen === 4 && <FileUpload onComplete={handleFilesDone} onBack={() => setScreen(3)} />}
      {screen === 5 && profile && <ReviewEdit profile={profile} setProfile={setProfile} onSubmit={handleSubmit} onBack={() => setScreen(4)} />}
      {screen === 6 && (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <div className="spinner" />
          <p style={{ color: '#475569', marginTop: 16 }}>Finding matching trials...</p>
        </div>
      )}
    </div>
  )
}
