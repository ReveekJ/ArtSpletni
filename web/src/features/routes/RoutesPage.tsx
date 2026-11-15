import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import type { Schemas } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { RunProgress } from "@/features/routes/RunProgress";
import { useRoutes } from "@/features/routes/api";
import { formatDate } from "@/lib/format";

type RouteSummary = Schemas["RouteSummaryOut"];

function isLive(route: RouteSummary): boolean {
  return route.run?.status === "active" || route.run?.status === "paused";
}

export default function RoutesPage() {
  const { t } = useTranslation();
  const routes = useRoutes();
  if (routes.isPending) return <Loader />;
  if (routes.error) return <ErrorText error={routes.error} />;
  const primaryId = routes.data.find(isLive)?.id ?? routes.data[0]?.id;

  return (
    <section className="flex flex-col gap-5">
      <header className="flex flex-col gap-1.5 pt-1.5">
        <h1 className="m-0 text-display-sm">{t("app.routes.title")}</h1>
        <p className="m-0 text-body text-ink-muted">{t("app.routes.lead")}</p>
      </header>

      {routes.data.map((route) => (
        <RouteCard key={route.id} route={route} primary={route.id === primaryId} />
      ))}

      <div className="flex items-center gap-3.5 rounded-lg border-2 border-dashed border-pencil-solid px-4 py-[18px]">
        <span
          aria-hidden="true"
          className="grid size-11 shrink-0 place-items-center rounded-wobble border-todo text-ink-muted"
        >
          <Icon name="plus" />
        </span>
        <span className="flex flex-col gap-0.5">
          <span className="text-[16px] font-semibold">{t("app.routes.emptyTitle")}</span>
          <span className="text-[14px] text-ink-muted">{t("app.routes.emptyText")}</span>
        </span>
      </div>
    </section>
  );
}

function RouteCard({ route, primary }: { route: RouteSummary; primary: boolean }) {
  const { t } = useTranslation();
  const live = isLive(route);
  return (
    <Card asChild variant={primary ? "pencil" : "default"}>
      <article>
        {route.coverUrl ? (
          <div className="mx-3 mt-3 h-[150px] overflow-hidden rounded-[10px] border border-solid border-ink bg-map-land">
            <img
              src={route.coverUrl}
              alt=""
              className="block h-full w-full object-cover dark:brightness-90"
            />
          </div>
        ) : null}
        <div className="flex flex-col gap-2.5 px-4 pt-3.5 pb-4">
          <h2 className="m-0 text-[20px] leading-[1.25] font-semibold">{route.title}</h2>
          {route.description ? <p className="m-0 text-body-sm text-ink-muted">{route.description}</p> : null}
          <p className="m-0 flex flex-wrap gap-x-3.5 gap-y-1 text-[14px] text-ink-muted">
            <span className="inline-flex items-center gap-1.5">
              <Icon name="pin" size={16} />
              {t("app.routes.stops", { count: route.stopCount })}
            </span>
            {route.activeUntil ? (
              <span className="inline-flex items-center gap-1.5">
                <Icon name="clock" size={16} />
                {t("app.routes.until", { date: formatDate(route.activeUntil) })}
              </span>
            ) : null}
          </p>
          {route.run ? <RunProgress run={route.run} showTitle={false} /> : null}
          <Button asChild variant={primary ? "default" : "secondary"} className="mt-1" block>
            <Link to={`/routes/${route.slug}`}>
              {live ? t("app.routes.continue") : t("app.routes.open")}
              <Icon name="arrow-right" />
            </Link>
          </Button>
        </div>
      </article>
    </Card>
  );
}
