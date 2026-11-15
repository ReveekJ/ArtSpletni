import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { KpiGrid } from "@/features/admin/analytics/KpiGrid";
import { Meter } from "@/features/admin/analytics/Meter";
import { titleOf, useAdminRoutes } from "@/features/admin/api";
import { NativeSelect } from "@/features/admin/ui/NativeSelect";
import { PageHeader } from "@/features/admin/ui/PageHeader";
import { Panel } from "@/features/admin/ui/Panel";
import { Segmented } from "@/features/admin/ui/Segmented";

const PERIODS = ["7", "30", "90", "365"] as const;

export default function AnalyticsPage() {
  const { t } = useTranslation();
  const [days, setDays] = useState(30);
  const [routeId, setRouteId] = useState("");
  const query = { params: { query: { days } } };
  const overview = useQuery({
    queryKey: ["admin", "analytics", "overview", days],
    queryFn: () => unwrap(api.GET("/api/admin/analytics/overview", query)),
  });
  const points = useQuery({
    queryKey: ["admin", "analytics", "points", days],
    queryFn: () => unwrap(api.GET("/api/admin/analytics/points", query)),
  });
  const playback = useQuery({
    queryKey: ["admin", "analytics", "playback", days],
    queryFn: () => unwrap(api.GET("/api/admin/analytics/playback", query)),
  });
  const routes = useAdminRoutes();
  const funnel = useQuery({
    queryKey: ["admin", "analytics", "funnel", routeId],
    queryFn: () =>
      unwrap(
        api.GET("/api/admin/analytics/routes/{route_id}/funnel", { params: { path: { route_id: routeId } } }),
      ),
    enabled: routeId !== "",
  });

  const pointRows = points.data ?? [];
  const maxScans = Math.max(1, ...pointRows.map((row) => row.scans));

  return (
    <>
      <PageHeader
        title={t("app.admin.analytics")}
        actions={
          <Segmented
            label={t("app.admin.days")}
            value={String(days) as (typeof PERIODS)[number]}
            options={PERIODS.map((value) => ({
              value,
              label: t("app.admin.periodDays", { count: Number(value) }),
            }))}
            onChange={(value) => setDays(Number(value))}
          />
        }
      />
      <ErrorText error={overview.error ?? points.error ?? playback.error ?? funnel.error} />
      <KpiGrid overview={overview.data} />

      <div className="grid items-start gap-[18px] xl:grid-cols-2">
        <Panel title={t("app.admin.topPoints")} bodyClassName="px-0 pt-2 pb-2">
          <Table className="min-w-[480px]">
            <TableHeader>
              <TableRow>
                <TableHead className="pl-5">{t("app.admin.point")}</TableHead>
                <TableHead className="text-right">{t("app.admin.overview.scans")}</TableHead>
                <TableHead className="text-right">{t("app.admin.uniqueUsers")}</TableHead>
                <TableHead className="w-[34%] pr-5">{t("app.admin.share")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pointRows.map((row) => (
                <TableRow key={row.pointId}>
                  <TableCell className="pl-5">{row.title}</TableCell>
                  <TableCell className="text-right tabular">{row.scans}</TableCell>
                  <TableCell className="text-right tabular">{row.uniqueUsers}</TableCell>
                  <TableCell className="pr-5">
                    <Meter ratio={row.scans / maxScans} label={row.title} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Panel>

        <Panel
          title={t("app.admin.funnel")}
          actions={
            <NativeSelect
              size="sm"
              aria-label={t("app.admin.funnel")}
              value={routeId}
              onChange={(event) => setRouteId(event.target.value)}
            >
              <option value="">—</option>
              {(routes.data ?? []).map((route) => (
                <option key={route.id} value={route.id}>
                  {titleOf(route.title)}
                </option>
              ))}
            </NativeSelect>
          }
        >
          {funnel.data ? (
            <>
              <p className="m-0 text-body-sm text-ink-muted tabular">
                {t("app.admin.overview.runsStarted")}: {funnel.data.started} ·{" "}
                {t("app.admin.overview.runsCompleted")}: {funnel.data.completed}
              </p>
              <ul className="m-0 flex list-none flex-col gap-3 p-0">
                {funnel.data.stops.map((stop) => (
                  <li key={stop.stopId} className="flex flex-col gap-1.5">
                    <span className="flex justify-between gap-3 text-[14px]">
                      <span className="font-semibold">
                        {stop.position + 1}. {stop.title}
                      </span>
                      <span className="tabular">{stop.visits}</span>
                    </span>
                    <Meter
                      ratio={funnel.data.started ? stop.visits / funnel.data.started : 0}
                      label={stop.title}
                      tone={stop.position === 0 ? "brand" : "ink"}
                    />
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="m-0 rounded-md border-todo px-4 py-6 text-center text-body-sm text-ink-muted">
              {t("app.admin.funnelPick")}
            </p>
          )}
        </Panel>
      </div>

      <Panel title={t("app.admin.playback")} bodyClassName="px-0 pt-2 pb-2">
        <Table className="min-w-[640px]">
          <TableHeader>
            <TableRow>
              <TableHead className="pl-5">{t("app.admin.point")}</TableHead>
              <TableHead className="text-right">{t("app.admin.sessions")}</TableHead>
              <TableHead className="text-right">{t("app.admin.completedSessions")}</TableHead>
              <TableHead className="w-[34%] pr-5">{t("app.admin.averageRatio")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(playback.data ?? []).map((row) => {
              const title = pointRows.find((point) => point.pointId === row.pointId)?.title ?? row.pointId;
              return (
                <TableRow key={`${row.pointId}-${row.assetId}`}>
                  <TableCell className="pl-5">{title}</TableCell>
                  <TableCell className="text-right tabular">{row.sessions}</TableCell>
                  <TableCell className="text-right tabular">{row.completed}</TableCell>
                  <TableCell className="pr-5">
                    <Meter ratio={row.averageRatio} label={title} />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Panel>
    </>
  );
}
