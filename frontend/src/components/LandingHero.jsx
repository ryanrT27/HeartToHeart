import { useState } from "react";
import heroImage from "../assets/heart2heart-hero.png";
import doctorImage from "../assets/doctor.png";
import pregnantImage from "../assets/pregnant.png";
import megaphone1 from "../assets/megaphone 1.png";
import chartLine1 from "../assets/chart-line 1.png";
import pregnant1 from "../assets/pregnant 1.png";

const CONTACT_EMAIL = "contact@heart2heart.health";

const MISSION_CARD_IMAGES = {
  Advocacy: megaphone1,
  Research: chartLine1,
  Awareness: pregnant1,
};

export default function LandingHero({ onFindMatch }) {
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");

  const handleContactSubmit = (e) => {
    e.preventDefault();
    const subject = encodeURIComponent(`Question from ${contactName}`);
    const body = encodeURIComponent(`From: ${contactName} <${contactEmail}>`);
    window.location.href = `mailto:${CONTACT_EMAIL}?subject=${subject}&body=${body}`;
  };

  return (
    <>
      {/* ── Hero ── */}
      <div className="hero-grid">
        <div className="hero-copy">
          <h1 className="hero-heading">Empowering the <br /> Hearts that Give Life.</h1>
          <p className="hero-body">
            Heart2Heart is closing the gap in maternal health research. Whether you're pregnant or postpartum,
             we match you with clinical trials built to protect your cardiovascular future.
          </p>
          <div className="hero-cta-stack">
            <button type="button" className="hero-cta" onClick={onFindMatch}>
              Find My Match
            </button>
            <p className="hero-assist-blurb">
              Unsure how to fill out your medical profile? Ask your provider for assistance!
            </p>
          </div>
        </div>
        <div className="hero-image-wrap">
          <img
            className="hero-image"
            src={heroImage}
            alt="Three women smiling together"
          />
          {/* baby image */}
          <img
            className="hero-floating-image"
            src={pregnantImage} 
            alt="Pregnant woman reading"
          />
        </div>
      </div>

      {/* ── Our Mission ── */}
      <section className="mission-section" aria-label="Our Mission">
        <h2 className="mission-heading">Our Mission</h2>
        <div className="mission-cards">
          {[
            {
              title: "Advocacy",
              text: "Cardiovascular risks often go undetected when support systems are missing. We empower you to take charge by connecting you with trials that shape the future of maternal heart care.",
            },
            {
              title: "Research",
              text: "Maternal heart health is critically understudied. By increasing representation and participation, we provide physicians with the data needed for informed, accurate, and life-saving care.",
            },
            {
              title: "Awareness",
              text: "Your symptoms deserve answers. Participating in research allows you to monitor your own health while deepening our collective understanding of the postpartum heart.",
            },
          ].map(({ title, text }) => {
            const iconSrc = MISSION_CARD_IMAGES[title];
            return (
            <div className="mission-card" key={title}>
              <div className="mission-card-circle" aria-hidden="true">
                {iconSrc ? (
                  <img src={iconSrc} alt="" className="mission-card-circle-icon" width={34} height={34} />
                ) : null}
              </div>
              <div className="mission-card-body">
                <h3 className="mission-card-title">{title}</h3>
                <p className="mission-card-text">{text}</p>
              </div>
            </div>
            );
          })}
        </div>
      </section>

      {/* ── Impact / Quote ── */}
      <section className="impact-section" aria-label="Our impact">
        <div className="impact-inner">
          <div className="impact-media">
          <img
            className="doctor-image"
            src={doctorImage}
            alt="Doctor with arms crossed."
          />
            <div className="impact-quote-box">
              <p className="impact-quote-text">According to the <a 
                href="https://cdc.gov/maternal-mortality/php/data-research/mmrc/index.html?cove-tab=4" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-red-600 underline hover:text-red-800 transition-colors">
                CDC, </a> 85.7% of pregnancy-related deaths in 2022 were preventable.</p>
            </div>
          </div>
          <div className="impact-copy">
            <h2 className="impact-quote-heading">Our Solution</h2>
            <p className="impact-body">With gaps in clinical care and patient knowledge identified as the leading causes of these preventable deaths, Heart2Heart exists to empower women to advocate for each other by connecting them with clinical trials that can define the future of maternal cardiovascular care.</p>
          </div>
        </div>
      </section>

      {/* ── Footer / Contact ── */}
      <footer className="lp-footer" aria-label="Contact">
        <div className="lp-footer-inner">
          <div className="lp-footer-left">
            <p className="lp-footer-question">Have a Question?</p>
            <a href={`mailto:${CONTACT_EMAIL}`} className="lp-footer-contact-link">
              <em>Contact us!</em>&nbsp;&gt;
            </a>
          </div>
          <form
            className="lp-footer-form"
            onSubmit={handleContactSubmit}
            aria-label="Contact form"
          >
            <input
              className="lp-footer-input"
              type="text"
              placeholder="name"
              value={contactName}
              onChange={(e) => setContactName(e.target.value)}
              aria-label="Your name"
            />
            <input
              className="lp-footer-input"
              type="email"
              placeholder="email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
              aria-label="Your email"
            />
            <button type="submit" className="lp-footer-submit">
              Submit &gt;
            </button>
          </form>
        </div>
        <p className="lp-footer-copy">heart2heart 2026.</p>
      </footer>
    </>
  );
}
