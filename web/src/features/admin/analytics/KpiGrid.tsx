import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { Card } from "@/components/ui/card";

const OVERVIEW_KEYS = [
  "scans",
  "failedScans",
  "activeUsers",
  "newAccounts",
  "runsStarted",
  "runsCompleted",
  "offersGranted",
  "offersRedeemed",
] as const;

const NUMBER = new Intl.NumberFormat("ru-RU");

export function KpiGrid({ overview }: { overview: Schemas["OverviewOut"] | undefined }) {
  const { t } = useTranslation();
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-[18px]">
      {OVERVIEW_KEYS.map((key) => {
        const value = overview?.[key];
        return (
          <Card key={key} className="gap-1.5 px-[18px] pt-[18px] pb-4">
            <span className="text-[14px] text-ink-muted">{t(`app.admin.overview.${key}`)}</span>
            <span className={value === undefined ? "text-metric text-ink-muted" : "text-metric"}>
              {value === undefined ? "—" : NUMBER.format(value)}
            </span>
          </Card>
        );
      })}
    </div>
  );
}
