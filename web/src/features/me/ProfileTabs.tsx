import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { DrawnSvg } from "@/components/motion/DrawnSvg";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { useMyAchievements, useMySubmissions } from "@/features/me/api";
import { useCollection } from "@/features/points/api";
import { RunProgress } from "@/features/routes/RunProgress";
import { useMyRuns } from "@/features/routes/api";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

export function EmptyNote() {
  const { t } = useTranslation();
  return (
    <Card variant="todo" className="items-center gap-2 px-4 py-6 text-center text-body-sm text-ink-muted">
      <DrawnSvg
        aria-hidden="true"
        width={72}
        height={48}
        viewBox="0 0 72 48"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.6}
        strokeLinecap="round"
        strokeLinejoin="round"
        delay={200}
      >
        <path d="M6 42 C 16 30, 28 46, 40 34" strokeDasharray="3 4" />
        <path d="M54 33 C 50 28, 44 21, 44 15 A 10 10 0 0 1 64 15 C 64 21, 58 28, 54 33 Z" />
        <circle cx="54" cy="15" r="3.5" />
      </DrawnSvg>
      {t("app.common.empty")}
    </Card>
  );
}

export function CollectionTab() {
  const collection = useCollection(true);
  if (collection.isPending) return <Loader />;
  if (collection.error) return <ErrorText error={collection.error} />;
  if (collection.data.length === 0) return <EmptyNote />;
  return (
    <div className="sk-stagger grid grid-cols-2 gap-4">
      {collection.data.map((item) => (
        <Card key={item.point.id} asChild interactive className="gap-1.5 p-2.5 text-ink">
          <Link to={`/points/${item.point.id}`}>
            <span className="grid h-[120px] place-items-center overflow-hidden rounded-xs border border-solid border-ink bg-paper-sunk">
              {item.point.coverUrl ? (
                <img
                  src={item.point.coverUrl}
                  alt=""
                  className="block h-full w-full object-cover dark:brightness-90"
                />
              ) : (
                <Icon name="image" size={24} className="text-ink-muted" />
              )}
            </span>
            <span className="px-0.5 text-[15px] leading-[1.3] font-semibold">{item.point.title}</span>
            <span className="px-0.5 text-caption text-ink-muted">{formatDate(item.unlockedAt)}</span>
          </Link>
        </Card>
      ))}
    </div>
  );
}

export function RunsTab() {
  const runs = useMyRuns(true);
  if (runs.isPending) return <Loader />;
  if (runs.error) return <ErrorText error={runs.error} />;
  if (runs.data.length === 0) return <EmptyNote />;
  return (
    <ul className="sk-stagger m-0 flex list-none flex-col gap-4 p-0">
      {runs.data.map((run) => (
        <li key={run.runId}>
          <Card asChild interactive className="px-4 py-3.5 text-ink">
            <Link to={`/routes/${run.routeSlug}`}>
              <RunProgress run={run} />
            </Link>
          </Card>
        </li>
      ))}
    </ul>
  );
}

export function AchievementsTab() {
  const { t } = useTranslation();
  const achievements = useMyAchievements(true);
  if (achievements.isPending) return <Loader />;
  if (achievements.error) return <ErrorText error={achievements.error} />;
  if (achievements.data.length === 0) return <EmptyNote />;
  return (
    <div className="sk-stagger grid grid-cols-2 gap-4">
      {achievements.data.map((item) => {
        const earned = Boolean(item.earnedAt);
        const percent = item.progress?.target
          ? Math.min(100, Math.round((item.progress.current / item.progress.target) * 100))
          : 0;
        return (
          <Card key={item.id} variant={earned ? "default" : "todo"} className="gap-2 p-3.5">
            <span
              className={cn(
                "grid size-12 place-items-center overflow-hidden rounded-wobble",
                earned ? "border-sketch bg-wash" : "border-todo text-ink-muted",
              )}
            >
              {item.iconUrl ? (
                <img
                  src={item.iconUrl}
                  alt=""
                  className={cn("size-full object-cover", !earned && "opacity-50")}
                />
              ) : (
                <Icon name="sparkle" size={22} />
              )}
            </span>
            <span className="text-[15px] leading-[1.3] font-semibold">{item.title}</span>
            {item.description ? (
              <span className="text-caption text-ink-muted">{item.description}</span>
            ) : null}
            {item.progress && !earned ? (
              <span className="flex items-center gap-2">
                <span className="sk-bar flex-1">
                  <span style={{ width: `${percent}%` }} />
                </span>
                <span className="text-caption tabular">
                  {item.progress.current} / {item.progress.target}
                </span>
              </span>
            ) : null}
            {item.earnedAt ? (
              <span className="inline-flex items-center gap-1 text-caption font-semibold text-success">
                <Icon name="check" size={14} />
                {formatDate(item.earnedAt)}
              </span>
            ) : null}
            {item.hasReward ? (
              <Badge variant="note" className="mt-auto">
                <Icon name="gift" size={14} />
                {t("app.profile.reward")}
              </Badge>
            ) : null}
          </Card>
        );
      })}
    </div>
  );
}

export function SubmissionsTab() {
  const { t } = useTranslation();
  const submissions = useMySubmissions(true);
  if (submissions.isPending) return <Loader />;
  if (submissions.error) return <ErrorText error={submissions.error} />;
  if (submissions.data.length === 0) return <EmptyNote />;
  return (
    <Card asChild className="px-4 py-0.5">
      <ul className="sk-stagger m-0 list-none">
        {submissions.data.map((item) => (
          <li
            key={item.id}
            className="flex flex-col gap-1 border-b border-solid border-rule py-3 last:border-b-0"
          >
            <span className="flex items-center justify-between gap-3">
              <span className="min-w-0 text-[15px] font-semibold">{item.title}</span>
              <Badge
                variant={item.status === "approved" ? "ink" : item.status === "rejected" ? "danger" : "todo"}
              >
                {t(`app.profile.submissionStatus.${item.status}`)}
              </Badge>
            </span>
            {item.moderatorComment ? (
              <span className="text-body-sm text-ink-muted">{item.moderatorComment}</span>
            ) : null}
          </li>
        ))}
      </ul>
    </Card>
  );
}
