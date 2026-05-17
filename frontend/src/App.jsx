import { useState } from "react";
import SiteHeader from "./components/SiteHeader";
import LandingHero from "./components/LandingHero";
import AboutPage from "./components/AboutPage";
import PrivacyPage from "./components/PrivacyPage";
import Onboarding from "./components/Onboarding";
import Results from "./components/Results";
import { clearAssessmentSession } from "./assessmentSession";

const ONBOARDING_LEAVE_WARNING =
  "You have matching information in progress. If you leave this page, your progress will be lost. Continue?";

function App() {
  const [currentView, setCurrentView] = useState("marketing");
  const [marketingPage, setMarketingPage] = useState("home");
  const [trials, setTrials] = useState([]);

  const goToMarketing = (page) => {
    setMarketingPage(page);
    setCurrentView("marketing");
  };

  const exitAssessmentWithConfirm = (page = "home") => {
    if (!window.confirm(ONBOARDING_LEAVE_WARNING)) return;
    clearAssessmentSession();
    setMarketingPage(page);
    setCurrentView("marketing");
  };

  const navigateMarketingFromOnboarding = (page) => exitAssessmentWithConfirm(page);

  return (
    <div className="app-root">
      {currentView === "marketing" && (
        <div className="site-shell">
          <div className="site-shell-inner">
            <SiteHeader activePage={marketingPage} onNavigate={setMarketingPage} />
            <main
              className={
                marketingPage === "home"
                  ? "site-main"
                  : "site-main site-main--marketing-subpage"
              }
            >
              {marketingPage === "home" && (
                <LandingHero onFindMatch={() => setCurrentView("onboarding")} />
              )}
              {marketingPage === "about" && <AboutPage />}
              {marketingPage === "privacy" && <PrivacyPage />}
            </main>
          </div>
        </div>
      )}

      {currentView === "onboarding" && (
        <div className="site-shell">
          <div className="site-shell-inner">
            <SiteHeader activePage={null} onNavigate={navigateMarketingFromOnboarding} />
            <main className="site-main site-main--onboarding">
              <div className="app-flow app-flow--onboarding">
                <Onboarding
                  setCurrentView={setCurrentView}
                  setTrials={setTrials}
                  onExitAssessment={() => exitAssessmentWithConfirm("home")}
                />
              </div>
            </main>
          </div>
        </div>
      )}

      {currentView === "results" && (
        <div className="site-shell">
          <div className="site-shell-inner">
            <SiteHeader activePage={null} onNavigate={goToMarketing} />
            <main className="site-main site-main--results">
              <Results onGoHome={() => goToMarketing("home")} trials={trials} />
            </main>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
