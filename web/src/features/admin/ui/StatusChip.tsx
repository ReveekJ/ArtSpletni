import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { LANGUAGES } from "@/i18n";
import { cn } from "@/lib/utils";

export function StatusChip({ published }: { published: boolean }) {
  const { t } = useTranslation();
  return (
    <Badge variant={published ? "ink" : "todo"}>
      {published ? t("app.admin.published") : t("app.admin.draft")}
    </Badge>
  );
}

export function LangChips({ filled }: { filled: Record<string, unknown> }) {
  const { t } = useTranslation();
  return (
    <span className="flex gap-1.5">
      {LANGUAGES.map((lang) => {
        const ready = Boolean(filled[lang]);
        return (
          <span
            key={lang}
            title={ready ? undefined : t("app.admin.untranslated")}
            className={cn("sk-lang", ready ? "sk-lang--ready" : "sk-lang--missing")}
          >
            {lang.toUpperCase()}
          </span>
        );
      })}
    </span>
  );
}

export function NumberMark({ value }: { value: number | string }) {
  return (
    <span
      aria-hidden="true"
      className="grid size-9 shrink-0 place-items-center rounded-wobble border-sketch bg-paper-sunk text-[14px] font-bold tabular"
    >
      {value}
    </span>
  );
}
