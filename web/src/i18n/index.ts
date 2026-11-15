import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import appEn from "@/i18n/app/en.json";
import appRu from "@/i18n/app/ru.json";
import appZh from "@/i18n/app/zh.json";
import landingEn from "@/i18n/landing/en.json";
import landingRu from "@/i18n/landing/ru.json";
import landingZh from "@/i18n/landing/zh.json";

export const LANGUAGES = ["ru", "en", "zh"] as const;
export type Language = (typeof LANGUAGES)[number];

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      ru: { translation: { ...landingRu, app: appRu } },
      en: { translation: { ...landingEn, app: appEn } },
      zh: { translation: { ...landingZh, app: appZh } },
    },
    fallbackLng: "ru",
    supportedLngs: [...LANGUAGES],
    interpolation: { escapeValue: false },
    detection: { order: ["localStorage", "navigator"], lookupLocalStorage: "spletni_lang" },
  });

function syncDocumentLanguage(lng: string): void {
  document.documentElement.lang = lng.slice(0, 2);
}

i18n.on("languageChanged", syncDocumentLanguage);
syncDocumentLanguage(i18n.resolvedLanguage ?? "ru");

export function currentLanguage(): Language {
  const code = i18n.resolvedLanguage?.slice(0, 2);
  return LANGUAGES.find((lang) => lang === code) ?? "ru";
}

export default i18n;
