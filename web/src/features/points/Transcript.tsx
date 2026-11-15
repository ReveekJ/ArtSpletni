import { useTranslation } from "react-i18next";

import { Icon } from "@/components/ui/icon";

interface TranscriptProps {
  text: string;
}

export function Transcript({ text }: TranscriptProps) {
  const { t } = useTranslation();
  return (
    <details className="group rounded-md border-todo px-3.5 py-2.5">
      <summary className="flex cursor-pointer list-none items-center gap-2 text-label [&::-webkit-details-marker]:hidden">
        <Icon name="text" size={16} />
        <span className="flex-1">{t("app.point.transcript")}</span>
        <Icon name="chevron-right" size={16} className="transition-transform group-open:rotate-90" />
      </summary>
      <p className="m-0 pt-3 text-body-sm whitespace-pre-line">{text}</p>
    </details>
  );
}
