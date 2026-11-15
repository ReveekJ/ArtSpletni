import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";

import { api, type Schemas, unwrap } from "@/api/client";
import { BackButton } from "@/components/BackButton";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { titleOf } from "@/features/admin/api";
import { DependencyGraph } from "@/features/admin/routes/DependencyGraph";
import { RouteSettingsForm } from "@/features/admin/routes/RouteSettingsForm";
import {
  type AdminRoute,
  routePath,
  useAdminRoute,
  useRouteMutation,
} from "@/features/admin/routes/routeApi";
import { StopsPanel } from "@/features/admin/routes/StopsPanel";
import { PageHeader } from "@/features/admin/ui/PageHeader";
import { Panel } from "@/features/admin/ui/Panel";
import { StatusChip } from "@/features/admin/ui/StatusChip";

export { RoutesListPage } from "@/features/admin/routes/RoutesListPage";

export default function RouteBuilderPage() {
  const { routeId = "new" } = useParams();
  const isNew = routeId === "new";
  const route = useAdminRoute(routeId, !isNew);
  if (isNew) return <NewRoute />;
  if (route.isPending) return <Loader />;
  if (route.error) return <ErrorText error={route.error} />;
  return <RouteBuilder route={route.data} />;
}

function BackLink() {
  const { t } = useTranslation();
  return <BackButton fallback="/admin/routes" label={t("app.admin.backToRoutes")} />;
}

function NewRoute() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: (body: Schemas["RouteInput"]) => unwrap(api.POST("/api/admin/routes", { body })),
    onSuccess: (route) => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "routes"] });
      navigate(`/admin/routes/${route.id}`, { replace: true });
    },
  });
  return (
    <>
      <div className="flex items-center gap-3">
        <BackLink />
        <PageHeader title={t("app.admin.newRoute")} />
      </div>
      <Panel className="max-w-[760px]">
        <RouteSettingsForm
          pending={create.isPending}
          error={create.error}
          onSubmit={(input) => create.mutate(input)}
        />
      </Panel>
    </>
  );
}

function RouteBuilder({ route }: { route: AdminRoute }) {
  const { t } = useTranslation();
  const routeId = route.id;
  const update = useRouteMutation(routeId, (body: Schemas["RouteInput"]) =>
    unwrap(api.PUT("/api/admin/routes/{route_id}", { params: { path: routePath(routeId) }, body })),
  );
  const publish = useRouteMutation(routeId, (published: boolean) =>
    published
      ? unwrap(api.POST("/api/admin/routes/{route_id}/publish", { params: { path: routePath(routeId) } }))
      : unwrap(api.POST("/api/admin/routes/{route_id}/unpublish", { params: { path: routePath(routeId) } })),
  );
  const stopTitles = new Map(route.stops.map((stop) => [stop.id, titleOf(stop.point.title)]));

  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <BackLink />
        <div className="min-w-0 flex-1">
          <PageHeader
            eyebrow={`${t("app.admin.routeEyebrow")} · ${t("app.admin.orderingModes." + route.orderingMode)} · ${route.stops.length}`}
            title={titleOf(route.title)}
            badge={<StatusChip published={route.isPublished} />}
            actions={
              <Button
                type="button"
                variant={route.isPublished ? "secondary" : "default"}
                size="sm"
                disabled={publish.isPending || (!route.isPublished && route.issues.length > 0)}
                onClick={() => publish.mutate(!route.isPublished)}
              >
                {route.isPublished ? t("app.admin.unpublish") : t("app.admin.publish")}
              </Button>
            }
          />
        </div>
      </div>
      <ErrorText error={publish.error} />
      {route.issues.length > 0 ? (
        <Alert variant="danger">
          <Icon name="alert" />
          <AlertDescription>
            <AlertTitle>{t("app.admin.issues")}</AlertTitle>
            <ul className="m-0 flex list-disc flex-col gap-1 pl-5">
              {route.issues.map((issue, index) => (
                <li key={index}>
                  {t(`app.admin.issueCodes.${issue.code}`)}
                  {issue.stopId ? `: ${stopTitles.get(issue.stopId) ?? ""}` : ""}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      ) : null}
      {route.orderingMode === "graph" ? <DependencyGraph route={route} /> : null}
      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <StopsPanel route={route} />
        <Panel title={t("app.admin.routeSettings")}>
          <RouteSettingsForm
            key={route.slug + route.orderingMode}
            route={route}
            pending={update.isPending}
            error={update.error}
            onSubmit={(input) => update.mutate(input)}
          />
        </Panel>
      </div>
    </>
  );
}
