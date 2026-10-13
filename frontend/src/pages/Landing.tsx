import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "../components/LanguageSwitcher";
import "../styles/landing.css";

export default function Landing() {
  const { t } = useTranslation();
  const landingRef = useRef<HTMLElement>(null);

  const stops = t("landing.stops", { returnObjects: true }) as Array<{
    name: string;
    story: string;
    area: string;
  }>;

  const handleShare = async () => {
    const shareData = {
      title: t("landing.shareTitle"),
      text: t("landing.shareText"),
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        throw error;
      }
      return;
    }

    await navigator.clipboard.writeText(shareData.url);
    window.alert(t("landing.shareCopied"));
  };

  useEffect(() => {
    const landing = landingRef.current;
    if (!landing) return;

    landing.classList.add("reveal-ready");
    const revealItems = landing.querySelectorAll<HTMLElement>("[data-reveal]");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -7%" },
    );

    revealItems.forEach((item) => observer.observe(item));
    return () => observer.disconnect();
  }, []);

  return (
    <main className="landing" ref={landingRef}>
      <header className="landing-header">
        <a className="landing-logo" href="#top" aria-label={t("landing.logoAria")}>
          <span className="logo-mark">А</span>
          <span>{t("common.brand")}</span>
        </a>
        <nav aria-label={t("landing.navAria")}>
          <a href="#idea">{t("landing.navIdea")}</a>
          <a href="#route">{t("landing.navRoute")}</a>
          <a href="/predlozhenie">{t("landing.navSubmit")}</a>
        </nav>
        <div className="header-actions">
          <LanguageSwitcher compact />
          <a className="header-link" href="#route">{t("landing.headerLink")} <span aria-hidden="true">↘</span></a>
        </div>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span className="live-dot" /> {t("landing.heroEyebrow")}</p>
          <h1>{t("landing.heroTitle")}<br />{t("landing.heroTitleLine2")} <em>{t("landing.heroTitleEm")}</em></h1>
          <p className="hero-intro">{t("landing.heroIntro")}</p>
          <p className="hero-description">{t("landing.heroDescription")}</p>
          <a className="primary-link" href="#idea">{t("landing.heroCta")} <span aria-hidden="true">↓</span></a>
          <p className="hero-note">{t("landing.heroNote")}</p>
        </div>
        <div className="hero-art" aria-label={t("landing.heroArtAria")}>
          <div className="art-topline"><span>{t("landing.artToplineLeft")}</span><span>56°50′ N / 60°36′ E</span></div>
          <img className="hero-map-img" src="/route.jpeg" alt={t("landing.heroArtAria")} />
          <div className="art-bottomline"><span>{t("landing.artBottomlineLeft")}</span><span>{t("landing.artBottomlineRight")}</span></div>
        </div>
        <div className="hero-index">{t("landing.heroIndex")}</div>
      </section>

      <section className="idea-section" id="idea">
        <div className="section-label" data-reveal><span>{t("landing.ideaLabel1")}</span><span>{t("landing.ideaLabel2")}</span></div>
        <div className="idea-grid" data-reveal>
          <h2>{t("landing.ideaTitle")}{t("landing.ideaTitle") && <br />}<em>{t("landing.ideaTitleEm")}</em>{t("landing.ideaTitleLine2")}</h2>
          <div className="idea-text">
            <p>{t("landing.ideaText1")}</p>
            <p>{t("landing.ideaText2")}</p>
            <button className="margin-note" type="button" onClick={handleShare}>
              {t("landing.shareButton")} <b aria-hidden="true">↗</b>
            </button>
          </div>
        </div>
        <div className="principles" data-reveal>
          <article><span>01</span><h3>{t("landing.principle1Title")}</h3><p>{t("landing.principle1Text")}</p></article>
          <article><span>02</span><h3>{t("landing.principle2Title")}</h3><p>{t("landing.principle2Text")}</p></article>
          <article><span>03</span><h3>{t("landing.principle3Title")}</h3><p>{t("landing.principle3Text")}</p></article>
        </div>
      </section>

      <section className="how-section" aria-labelledby="how-title">
        <div className="section-label" data-reveal><span>{t("landing.howLabel1")}</span><span>{t("landing.howLabel2")}</span></div>
        <div className="how-heading" data-reveal><h2 id="how-title">{t("landing.howTitle")}<br /><em>{t("landing.howTitleEm")}</em></h2><p>{t("landing.howText")}</p></div>
        <div className="steps" data-reveal>
          <article><span className="step-number">01</span><span className="step-icon nfc-icon" aria-hidden="true">✦</span><h3>{t("landing.step1Title")}</h3><p>{t("landing.step1Text")}</p></article>
          <span className="step-arrow" aria-hidden="true">→</span>
          <article><span className="step-number">02</span><span className="step-icon audio-icon" aria-hidden="true">▶</span><h3>{t("landing.step2Title")}</h3><p>{t("landing.step2Text")}</p></article>
          <span className="step-arrow" aria-hidden="true">→</span>
          <article><span className="step-number">03</span><span className="step-icon share-icon" aria-hidden="true">↗</span><h3>{t("landing.step3Title")}</h3><p>{t("landing.step3Text")}</p></article>
        </div>
      </section>

      <section className="route-section" id="route">
        <div className="section-label" data-reveal><span>{t("landing.routeLabel1")}</span><span>{t("landing.routeLabel2")}</span></div>
        <div className="route-heading" data-reveal><h2>{t("landing.routeTitle")}<br /><em>{t("landing.routeTitleEm")}</em></h2><p>{t("landing.routeText")}</p></div>
        <div className="stops-list" data-reveal>
          {stops.map((stop, index) => (
            <article className="stop-row" key={stop.name}>
              <span className="stop-index">{String(index + 1).padStart(2, "0")}</span>
              <div className="stop-name"><h3>{stop.name}</h3><span>{stop.area}</span></div>
              <p className="stop-story">{stop.story}</p>
              <span className="stop-mark" aria-hidden="true">↗</span>
            </article>
          ))}
        </div>
        <div className="route-foot"><span>{t("landing.routeFootLeft")}</span><span>{t("landing.routeFootRight")}</span></div>
      </section>

      <footer className="landing-footer">
        <p className="footer-kicker">{t("landing.footerKicker")}</p>
        <h2>{t("landing.footerTitle")} <em>{t("landing.footerTitleEm")}</em></h2>
        <a href="/predlozhenie" className="footer-link">{t("landing.footerLink")} <span aria-hidden="true">↗</span></a>
        <div className="footer-partners">
          <div className="footer-partner">
            <span className="footer-partner-role">{t("landing.footerPartnerCreated")}</span>
            <a className="footer-media" href="https://vk.ru/lyceum.urfu" target="_blank" rel="noreferrer" aria-label={t("landing.footerMediaAria")}>
              SESC <span>MEDIA</span>
            </a>
          </div>
          <div className="footer-partner">
            <span className="footer-partner-role">{t("landing.footerPartnerSupported")}</span>
            <a className="footer-wordmark" href="https://sesc-it-team.ru/" target="_blank" rel="noreferrer" aria-label={t("landing.footerWordmarkAria")}>
              <img src="/image.png" alt="SESC IT Team" width="1042" height="161" />
            </a>
          </div>
        </div>
        <div className="footer-bottom">
          <span>{t("landing.footerBottomLeft")}</span>
          <span>{t("landing.footerBottomRight")}</span>
        </div>
      </footer>
    </main>
  );
}
