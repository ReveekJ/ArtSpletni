import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { AchievementForm } from "@/features/admin/achievements/AchievementForm";
import { titleOf } from "@/features/admin/api";
import { PageHeader } from "@/features/admin/ui/PageHeader";
import { Panel } from "@/features/admin/ui/Panel";
import { cn } from "@/lib/utils";

export default function AchievementsPage() {
  const { t } = useTranslation();
  const achievements = useQuery({
    queryKey: ["admin", "achievements"],
    queryFn: () => unwrap(api.GET("/api/admin/achievements")),
  });
  const [editing, setEditing] = useState<string | "new" | null>(null);

  if (achievements.isPending) return <Loader />;
  return (
    <>
      <PageHeader
        title={t("app.admin.achievements")}
        actions={
          <Button type="button" onClick={() => setEditing("new")}>
            <Icon name="plus" />
            {t("app.admin.newAchievement")}
          </Button>
        }
      />
      <ErrorText error={achievements.error} />
      {editing === "new" ? (
        <Panel title={t("app.admin.newAchievement")} className="max-w-[860px]">
          <AchievementForm onDone={() => setEditing(null)} />
        </Panel>
      ) : null}
      <ul className="m-0 flex max-w-[860px] list-none flex-col gap-3.5 p-0">
        {(achievements.data ?? []).map((item) => (
          <Card
            asChild
            key={item.id}
            variant={item.isActive ? "default" : "todo"}
            className="gap-4 px-5 py-4"
          >
            <li>
              <div className="flex flex-wrap items-center gap-3">
                <span
                  aria-hidden="true"
                  className={cn(
                    "grid size-10 shrink-0 place-items-center rounded-wobble",
                    item.isActive ? "border-sketch bg-note" : "border-todo text-ink-muted",
                  )}
                >
                  <Icon name="sparkle" />
                </span>
                <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <strong className="text-[16px]">{titleOf(item.title)}</strong>
                  <span className="text-caption text-ink-muted">
                    {t(`app.admin.rules.${item.rule}`)} {JSON.stringify(item.params)}
                  </span>
                </span>
                {item.isHidden ? <Badge variant="todo">{t("app.admin.hidden")}</Badge> : null}
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label={t("app.common.edit")}
                  aria-expanded={editing === item.id}
                  onClick={() => setEditing(editing === item.id ? null : item.id)}
                >
                  <Icon name="edit" size={18} />
                </Button>
              </div>
              {editing === item.id ? (
                <div className="border-t border-solid border-rule pt-4">
                  <AchievementForm achievement={item} onDone={() => setEditing(null)} />
                </div>
              ) : null}
            </li>
          </Card>
        ))}
      </ul>
    </>
  );
}
