import { useTranslation } from "react-i18next";

import { currentLanguage, type Language } from "@/i18n";

export function useLanguage(): Language {
  useTranslation();
  return currentLanguage();
}
