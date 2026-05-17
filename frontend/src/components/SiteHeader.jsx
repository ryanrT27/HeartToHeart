export default function SiteHeader({ activePage, onNavigate }) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <button type="button" className="site-logo" onClick={() => onNavigate("home")}>
          heart2heart
        </button>
        <nav className="site-nav" aria-label="Primary">
          <button
            type="button"
            className={activePage === "home" ? "site-nav-active" : ""}
            onClick={() => onNavigate("home")}
          >
            Home
          </button>
          <button
            type="button"
            className={activePage === "about" ? "site-nav-active" : ""}
            onClick={() => onNavigate("about")}
          >
            About Us
          </button>
          <button
            type="button"
            className={activePage === "privacy" ? "site-nav-active" : ""}
            onClick={() => onNavigate("privacy")}
          >
            Privacy
          </button>
        </nav>
      </div>
    </header>
  )
}
