import { useState } from "react";
import heroImage from "../assets/heart2heart-hero.png";
import doctorImage from "../assets/doctor.png";
import pregnantImage from "../assets/pregnant.png";

const CONTACT_EMAIL = "contact@heart2heart.health";

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
          <h1 className="hero-heading">Be the Heart that Saves a Woman&apos;s Life.</h1>
          <p className="hero-body">
            Heart2Heart bridges the gap in women&apos;s health research by matching
            you with clinical trials that define the future of maternal cardiovascular care.
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
        </div>
      </div>

      {/* ── Our Mission ── */}
      <section className="mission-section" aria-label="Our Mission">
        <h2 className="mission-heading">Our Mission</h2>
        <br></br>
        <div className="mission-cards">
          {[
            {
              title: "Advocacy",
              text: "When women have no systems in place to advocate for themselves, cardiovascular risks go undetected. Heart2Heart empowers women to advocate for themselves and their families by connecting them with clinical trials that can define the future of maternal cardiovascular care.",
            },
            {
              title: "Research",
              text: "Women\u2019s cardiovascular health during pregnancy and postpartum is severely understudied. Better access to clinical trials improves research representation and gives physicians the data they need to consistently provide informed and accurate care.",
            },
            {
              title: "Awareness",
              text: "Many women experience symptoms that are dismissed, misdiagnosed, or unexplained. Participating in clinical trials allows women to properly monitor, evaluate, and learn new information that can improve understanding of their own health.",
            },
          ].map(({ title, text }) => (
            <div className="mission-card" key={title}>
              <div className="mission-card-circle" aria-hidden="true" />
              <div className="mission-card-body">
                <h3 className="mission-card-title">{title}</h3>
                <p className="mission-card-text">{text}</p>
              </div>
            </div>
          ))}
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
              <p className="impact-quote-text">research quote here</p>
            </div>
          </div>
          <div className="impact-copy">
            <h2 className="impact-heading">
              big important statement&nbsp;— women are not research
            </h2>
            <p className="impact-body">impact statement&nbsp;&nbsp;more important info</p>
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
