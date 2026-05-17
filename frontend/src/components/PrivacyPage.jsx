export default function PrivacyPage() {
  return (
    <article className="marketing-page">
      <h1>Privacy Policy</h1>
      <p>
        This policy describes how Heart2Heart handles information when you use our web experience. Heart2Heart is designed to have no personal data stored on our servers, however please read this policy carefully before submitting health
        details or documents.
      </p>

      <h2>What we collect</h2>
      <ul>
        <li>
          <strong>Information you enter</strong> — demographics, pregnancy-related responses, health-history selections,
          and any edits you make on the review screen before matching. This data is collected but not stored anywhere, meaning if you were to close out of Heart2Heart, the data you entered would disappear.
        </li>
        <li>
          <strong>Documents you upload</strong> — PDF lab reports or medical summaries you choose to share for parsing. These documents are parsed via OCR and anonymized via Microsoft Presidio before further processing.
        </li>
        <li>
          <strong>Technical data</strong> — standard browser metadata needed to load the app (e.g., IP address visible to
          hosting infrastructure), which we do not use for any purpose.
        </li>
      </ul>

      <h2>How we use it</h2>
      <p>
        Data you submit is used to extract structured fields, run eligibility-style matching against a catalog of
        trials from ClinicalTrials.gov, and display results to you in the browser session. We do not sell your personal information, and no data is stored on our servers.
      </p>

      <h2>Third-party processing</h2>
      <p>
        Depending on deployment configuration, text extracted from PDFs may be processed by a cloud language model provider
        after aggressive local redaction of common personally identifiable patterns.
      </p>

      <h2>Your choices</h2>
      <ul>
        <li>You may skip document uploads and enter only what you choose manually.</li>
        <li>You can leave the experience at any time; refreshing the page clears in-memory state.</li>
      </ul>
    </article>
  )
}
