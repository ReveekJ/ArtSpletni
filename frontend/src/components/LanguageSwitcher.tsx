import { useLanguage } from "../i18n/useLanguage";
import { SUPPORTED_LANGUAGES, type SupportedLanguage } from "../i18n/config";

const LANGUAGE_LABELS: Record<SupportedLanguage, string> = {
  ru: "RU",
  en: "EN",
  zh: "中文",
};

export default function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { language, setLanguage } = useLanguage();

  if (compact) {
    return (
    <div className="lang-switcher compact">
        {SUPPORTED_LANGUAGES.map((lang) => (
          <button
            key={lang}
            className={`lang-btn ${lang === language ? "active" : ""}`}
            onClick={() => setLanguage(lang)}
            aria-label={LANGUAGE_LABELS[lang]}
          >
            {LANGUAGE_LABELS[lang]}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="lang-switcher">
      {SUPPORTED_LANGUAGES.map((lang) => (
        <button
          key={lang}
          className={`lang-btn ${lang === language ? "active" : ""}`}
          onClick={() => setLanguage(lang)}
        >
          {LANGUAGE_LABELS[lang]}
        </button>
      ))}
    </div>
  );
}
