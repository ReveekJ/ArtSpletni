import { useTranslation } from "react-i18next";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { type Language, LANGUAGES } from "@/i18n";
import { useLanguage } from "@/lib/useLanguage";
import { cn } from "@/lib/utils";

const LABELS: Record<Language, string> = { ru: "RU", en: "EN", zh: "中文" };

export function LanguageSwitcher({ compact = false, className }: { compact?: boolean; className?: string }) {
  const { i18n, t } = useTranslation();
  const current = useLanguage();
  return (
    <ToggleGroup
      type="single"
      value={current}
      aria-label={t("app.common.language")}
      onValueChange={(value) => {
        const next = LANGUAGES.find((lang) => lang === value);
        if (next) void i18n.changeLanguage(next);
      }}
      className={cn(compact && "shadow-none", className)}
    >
      {LANGUAGES.map((lang) => (
        <ToggleGroupItem
          key={lang}
          value={lang}
          lang={lang}
          className={cn(compact && "h-9 px-3 text-[13px]")}
        >
          {LABELS[lang]}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}

export default LanguageSwitcher;
