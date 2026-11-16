import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api, type Schemas, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Panel } from "@/features/admin/ui/Panel";
import { GossipBadges, GossipSources } from "@/features/points/GossipParts";
import { isGossipInProgress } from "@/features/points/api";
import { LANGUAGES } from "@/i18n";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

const POLL_MS = 4000;

function ItemRow({
  item,
  busy,
  onToggle,
}: {
  item: Schemas["AdminGossipItemOut"];
  busy: boolean;
  onToggle: () => void;
}) {
  const { t } = useTranslation();
  return (
    <li
      className={cn(
        "flex flex-col gap-2 border-b border-solid border-rule py-3 last:border-b-0",
        item.isHidden && "opacity-60",
      )}
    >
      <div className="flex items-start gap-3">
        <span className="flex min-w-0 flex-1 flex-col gap-1">
          <GossipBadges category={item.category} veracity={item.veracity} />
          <span className="text-[15px] font-semibold">{item.title}</span>
          {item.placeName ? <span className="text-caption text-ink-muted">{item.placeName}</span> : null}
        </span>
        {item.isHidden ? <Badge variant="todo">{t("app.gossip.adminHidden")}</Badge> : null}
        <Button type="button" variant="outline" size="xs" disabled={busy} onClick={onToggle}>
          <Icon name="eye" size={16} />
          {item.isHidden ? t("app.gossip.adminShow") : t("app.gossip.adminHide")}
        </Button>
      </div>
      <details className="text-body-sm">
        <summary className="cursor-pointer text-caption text-ink-muted">
          {t("app.gossip.adminDetails")}
        </summary>
        <div className="mt-2 flex flex-col gap-3">
          {LANGUAGES.map((lang) => {
            const translation = item.translations[lang];
            return (
              <div key={lang} className="flex flex-col gap-1">
                <Badge className="self-start">{lang.toUpperCase()}</Badge>
                {translation ? (
                  <>
                    <strong>{translation.title}</strong>
                    <p className="m-0 whitespace-pre-line">{translation.text}</p>
                  </>
                ) : (
                  <span className="text-caption text-ink-muted">—</span>
                )}
              </div>
            );
          })}
          <GossipSources sources={item.sources} />
        </div>
      </details>
    </li>
  );
}

export function GossipPanel({ pointId }: { pointId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const queryKey = ["admin", "gossip", pointId];
  const path = { params: { path: { point_id: pointId } } };
  const feed = useQuery({
    queryKey,
    queryFn: () => unwrap(api.GET("/api/admin/points/{point_id}/gossip", path)),
    refetchInterval: (query) => (isGossipInProgress(query.state.data?.status) ? POLL_MS : false),
  });
  const refresh = () => void queryClient.invalidateQueries({ queryKey });
  const regenerate = useMutation({
    mutationFn: () => unwrap(api.POST("/api/admin/points/{point_id}/gossip/regenerate", path)),
    onSuccess: refresh,
  });
  const toggle = useMutation({
    mutationFn: (item: Schemas["AdminGossipItemOut"]) =>
      unwrap(
        api.PATCH("/api/admin/gossip/{item_id}", {
          params: { path: { item_id: item.id } },
          body: { isHidden: !item.isHidden },
        }),
      ),
    onSuccess: refresh,
  });

  const data = feed.data;
  const inProgress = isGossipInProgress(data?.status);

  return (
    <Panel
      title={t("app.gossip.adminTitle")}
      description={t("app.gossip.adminDescription")}
      actions={
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!data?.enabled || inProgress || regenerate.isPending}
          onClick={() => regenerate.mutate()}
        >
          <Icon name="sparkle" size={18} />
          {t("app.gossip.adminRegenerate")}
        </Button>
      }
    >
      <ErrorText error={feed.error ?? regenerate.error ?? toggle.error} />
      {data && !data.enabled ? (
        <Alert>
          <Icon name="info" />
          <AlertDescription>{t("app.gossip.adminDisabled")}</AlertDescription>
        </Alert>
      ) : null}
      {data ? (
        <p className="m-0 flex flex-wrap items-center gap-2 text-caption text-ink-muted">
          <Badge variant={data.status === "failed" ? "danger" : "default"}>
            {t("app.gossip.adminStatus")}: {t(`app.gossip.status.${data.status}`)}
          </Badge>
          {data.finishedAt ? (
            <span>{t("app.gossip.adminFinishedAt", { date: formatDateTime(data.finishedAt) })}</span>
          ) : null}
        </p>
      ) : null}
      {data?.error ? <p className="m-0 text-caption break-words text-danger">{data.error}</p> : null}
      {data && data.items.length === 0 ? (
        <p className="m-0 text-body-sm text-ink-muted">{t("app.gossip.adminEmpty")}</p>
      ) : null}
      <ul className="m-0 flex list-none flex-col p-0">
        {(data?.items ?? []).map((item) => (
          <ItemRow
            key={item.id}
            item={item}
            busy={toggle.isPending && toggle.variables?.id === item.id}
            onToggle={() => toggle.mutate(item)}
          />
        ))}
      </ul>
    </Panel>
  );
}
