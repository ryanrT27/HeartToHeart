export default function AboutPage() {
  return (
    <article className="marketing-page">
      <h1>The Research Gap</h1>
      <p>
      Over the last 15 years, only <a 
        href="https://www.sciencedirect.com/science/article/pii/S0002937825000031" 
        target="_blank" 
        rel="noopener noreferrer"
        className="content-inline-link"
      >
        0.8% 
      </a> of clinical trials included pregnant participants.
      Out of nearly 91,000 randomized trials, 75% explicitly excluded pregnancy, leaving a massive data void in maternal care. 
      When we don't study pregnant bodies, we don't have the data to save them.
      </p>
      <p>
        Cardiovascular disease, in particular, remains a leading cause of serious illness during and after pregnancy. Many patients
        never hear about trials that could advance care for conditions such as preeclampsia, gestational hypertension,
        peripartum cardiomyopathy, and related complications. To address this, we built <strong>Heart2Heart</strong>, a digital pathway designed to connect people who are pregnant, postpartum, or living with
        pregnancy-related cardiovascular risk with clinical studies focused on maternal heart health.
      </p>
      <h2>Who we serve</h2>
      <p>
      Our platform is built for all individuals navigating maternal or postpartum health journeys, with a specific commitment
       to underrepresented people who are disproportionately impacted by cardiovascular disparities. 
       We designed our onboarding and OCR technology to bridge the medical literacy gap, 
       so you don't need a medical degree to understand your options. 
       Whether you are seeking trials for cutting-edge care, financial compensation, or simply 
       to take back control of your health data, Heart2Heart empowers you to explore what's next on your own terms. 
       We also serve clinicians looking for a streamlined, equitable way to connect their patients with life-saving research.
      </p>
      <h2>Disclaimer</h2>
      <p>
        Heart2Heart does not provide medical advice, diagnosis, or treatment. Trial listings and match scores are
        informational only. Enrollment decisions always belong to you and your licensed providers. Always verify details
        on ClinicalTrials.gov or directly with the study team before participating.
      </p>
    </article>
  )
}
