import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import type { Schemas } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { type StopItem, StopList, type StopState } from "@/components/sketch/Route";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { type MapMarker, MapView } from "@/components/YandexMap";
import { RunProgress } from "@/features/routes/RunProgress";
import { useAbandonRun, useRouteMap } from "@/features/routes/api";

type MapStop = Schemas["MapStopOut"];

const STATE: Record<MapStop["state"], StopState> = { visited: "done", available: "open", locked: "locked" };

export default function RouteMapPage() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const map = useRouteMap(slug);
  const abandon = useAbandonRun();

  const markers = useMemo<MapMarker[]>(
    () =>
      (map.data?.stops ?? []).flatMap((stop) =>
        stop.latitude != null && stop.longitude != null
          ? [
              {
                id: stop.stopId,
                latitude: stop.latitude,
                longitude: stop.longitude,
                title: stop.title,
                label: String(stop.position + 1),
                muted: stop.state !== "visited",
                state: STATE[stop.state],
              },
            ]
          : [],
      ),
    [map.data],
  );

  if (map.isPending) return <Loader />;
  if (map.error) return <ErrorText error={map.error} />;
  const { route, stops } = map.data;
  const live = route.run && (route.run.status === "active" || route.run.status === "paused");

  const items: StopItem[] = stops.map((stop) => ({
    key: stop.stopId,
    n: stop.position + 1,
    state: STATE[stop.state],
    name: <StopName stop={stop} />,
    onSelect:
      stop.pointId && stop.state === "visited" ? () => navigate(`/points/${stop.pointId}`) : undefined,
  }));

  return (
    <section className="flex flex-col gap-5">
      <header className="flex items-center gap-3">
        <Button asChild variant="outline" size="icon">
          <Link to="/routes" aria-label={t("app.routes.back")}>
            <Icon name="arrow-left" />
          </Link>
        </Button>
        <h1 className="m-0 min-w-0 flex-1 text-h1">{route.title}</h1>
        {route.run ? (
          <Badge className="tabular">
            {route.run.requiredVisited} / {route.run.requiredCount}
          </Badge>
        ) : null}
      </header>

      {route.description ? <p className="m-0 text-body text-ink-muted">{route.description}</p> : null}

      {markers.length > 0 ? (
        <MapView markers={markers} polyline={route.orderingMode === "sequential"} />
      ) : null}

      {route.run ? (
        <Card className="px-4 py-3.5">
          <RunProgress run={route.run} />
        </Card>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="m-0 text-h2">{t("app.routes.stopsTitle")}</h2>
        <Card>
          <StopList stops={items} />
        </Card>
      </section>

      {live && route.run ? (
        <Button
          type="button"
          variant="destructive"
          size="sm"
          className="self-start"
          disabled={abandon.isPending}
          onClick={() => route.run && abandon.mutate(route.run.runId)}
        >
          <Icon name="x" size={18} />
          {t("app.routes.abandon")}
        </Button>
      ) : null}
      <ErrorText error={abandon.error} />
    </section>
  );
}

function StopName({ stop }: { stop: MapStop }) {
  const { t } = useTranslation();
  const flags = [stop.isStart ? t("app.routes.start") : "", stop.isRequired ? "" : t("app.routes.optional")]
    .filter(Boolean)
    .join(" · ");
  return (
    <span className="flex flex-col gap-0.5 py-2">
      <span className={stop.state === "visited" ? "font-semibold" : undefined}>
        {stop.title ?? t("app.routes.hidden")}
      </span>
      {stop.hint ? <span className="text-caption text-ink-muted">{stop.hint}</span> : null}
      {flags ? <span className="text-caption text-ink-muted">{flags}</span> : null}
    </span>
  );
}
