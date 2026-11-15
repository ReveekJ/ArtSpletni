import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type Schemas, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { titleOf, useAdminPoints } from "@/features/admin/api";
import { type AdminRoute, routePath, stopPath, useRouteMutation } from "@/features/admin/routes/routeApi";
import { StopRow } from "@/features/admin/routes/StopRow";
import { NativeSelect } from "@/features/admin/ui/NativeSelect";
import { Panel } from "@/features/admin/ui/Panel";

export function StopsPanel({ route }: { route: AdminRoute }) {
  const { t } = useTranslation();
  const points = useAdminPoints();
  const [pointId, setPointId] = useState("");
  const routeId = route.id;
  const add = useRouteMutation(routeId, (body: Schemas["StopInput"]) =>
    unwrap(api.POST("/api/admin/routes/{route_id}/stops", { params: { path: routePath(routeId) }, body })),
  );
  const update = useRouteMutation(
    routeId,
    ({ stopId, body }: { stopId: string; body: Schemas["StopUpdate"] }) =>
      unwrap(
        api.PATCH("/api/admin/routes/{route_id}/stops/{stop_id}", {
          params: { path: stopPath(routeId, stopId) },
          body,
        }),
      ),
  );
  const remove = useRouteMutation(routeId, (stopId: string) =>
    unwrap(
      api.DELETE("/api/admin/routes/{route_id}/stops/{stop_id}", {
        params: { path: stopPath(routeId, stopId) },
      }),
    ),
  );
  const reorder = useRouteMutation(routeId, (stopIds: string[]) =>
    unwrap(
      api.PUT("/api/admin/routes/{route_id}/stops/order", {
        params: { path: routePath(routeId) },
        body: { stopIds },
      }),
    ),
  );

  const used = new Set(route.stops.map((stop) => stop.point.id));
  const move = (index: number, delta: number) => {
    const ids = route.stops.map((stop) => stop.id);
    const target = index + delta;
    if (target < 0 || target >= ids.length) return;
    const [item] = ids.splice(index, 1);
    if (item) ids.splice(target, 0, item);
    reorder.mutate(ids);
  };

  return (
    <Panel title={t("app.admin.stops")} bodyClassName="gap-3 px-0">
      <div className="px-5">
        <ErrorText error={add.error ?? update.error ?? remove.error ?? reorder.error} />
      </div>
      <ol className="m-0 list-none p-0">
        {route.stops.map((stop, index) => (
          <StopRow
            key={stop.id}
            n={index + 1}
            stop={stop}
            onMove={(delta) => move(index, delta)}
            onUpdate={(body) => update.mutate({ stopId: stop.id, body })}
            onRemove={() => remove.mutate(stop.id)}
          />
        ))}
      </ol>
      <div className="flex gap-2 px-5">
        <NativeSelect
          size="sm"
          className="flex-1"
          aria-label={t("app.admin.addStop")}
          value={pointId}
          onChange={(event) => setPointId(event.target.value)}
        >
          <option value="">{t("app.admin.addStop")}</option>
          {(points.data ?? [])
            .filter((point) => !used.has(point.id))
            .map((point) => (
              <option key={point.id} value={point.id}>
                {titleOf(point.title)} · {t(`app.admin.kinds.${point.kind}`)}
              </option>
            ))}
        </NativeSelect>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!pointId}
          onClick={() =>
            add.mutate(
              { pointId, isStart: route.stops.length === 0, isRequired: true },
              { onSuccess: () => setPointId("") },
            )
          }
        >
          <Icon name="plus" size={18} />
          {t("app.common.create")}
        </Button>
      </div>
    </Panel>
  );
}
