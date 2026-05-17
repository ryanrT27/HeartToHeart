import heroImage from "../assets/heart2heart-hero.png";

const CONTACT_EMAIL = "contact@heart2heart.health";

export default function LandingHero({ onFindMatch }) {
  return (
    <>
      <div className="hero-grid">
        <div className="hero-copy">
          <h1 className="hero-heading">Be the Heart that Saves a Woman&apos;s Life.</h1>
          <p className="hero-body">
            Heart2Heart bridges the gap in women&apos;s health
            research by matching you with clinical trials that define the future of maternal cardiovascular care.
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
      {/* <footer className="home-footer" id="contact" aria-label="Contact">
        <a href={`mailto:${CONTACT_EMAIL}`} className="home-footer-link">
          Contact us
        </a>
      </footer> */}
    </>
  )
}
