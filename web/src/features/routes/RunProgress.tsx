import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { ProgressDots, type StopState } from "@/components/sketch/Route";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const MAX_DOTS = 14;

function dotStates(done: number, total: number, live: boolean): StopState[] {
  return Array.from({ length: total }, (_, index) =>
    index < done ? "done" : index === done && live ? "current" : "locked",
  );
}

interface RunProgressProps {
  run: Schemas["RunStateOut"];
  showTitle?: boolean;
  className?: string;
}

export function RunProgress({ run, showTitle = true, className }: RunProgressProps) {
  const { t } = useTranslation();
  const total = run.requiredCount;
  const done = Math.min(run.requiredVisited, total);
  const percent = total ? Math.round((done / total) * 100) : 0;
  const live = run.status === "active" || run.status === "paused";
  const label = t("app.routes.progress", { done, total });

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex items-center justify-between gap-3">
        {showTitle ? <span className="min-w-0 truncate text-label">{run.routeTitle}</span> : <span />}
        <Badge variant={run.status === "completed" ? "ink" : live ? "now" : "todo"}>
          {t(`app.routes.status.${run.status}`)}
        </Badge>
      </div>
      <div
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
        className="flex items-center gap-2"
      >
        {total > 0 && total <= MAX_DOTS ? (
          <ProgressDots states={dotStates(done, total, live)} />
        ) : (
          <span className="sk-bar min-w-0 flex-1">
            <span style={{ width: `${percent}%` }} />
          </span>
        )}
        <span className="ml-1 text-caption font-semibold tabular">
          {t("app.routes.progressShort", { done, total })}
        </span>
      </div>
    </div>
  );
}
