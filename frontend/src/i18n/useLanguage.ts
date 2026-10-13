import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  DEFAULT_LANGUAGE,
  LANGUAGE_STORAGE_KEY,
  SUPPORTED_LANGUAGES,
  type SupportedLanguage,
} from "./config";

const LOCALE_MAP: Record<SupportedLanguage, string> = {
  ru: "ru-RU",
  en: "en-US",
  zh: "zh-CN",
};

export function useLanguage() {
  const { i18n } = useTranslation();
  const [language, setLanguageState] = useState<SupportedLanguage>(
    () => (i18n.language as SupportedLanguage) || DEFAULT_LANGUAGE,
  );

  useEffect(() => {
    const handler = (lng: string) => {
      const normalized = lng.slice(0, 2) as SupportedLanguage;
      if (SUPPORTED_LANGUAGES.includes(normalized)) {
        setLanguageState(normalized);
      }
    };
    i18n.on("languageChanged", handler);
    return () => {
      i18n.off("languageChanged", handler);
    };
  }, [i18n]);

  const setLanguage = useCallback(
    (lang: SupportedLanguage) => {
      void i18n.changeLanguage(lang);
      localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
    },
    [i18n],
  );

  const locale = LOCALE_MAP[language];

  return { language, setLanguage, locale };
}
