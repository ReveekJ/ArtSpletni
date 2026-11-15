import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  type Connection,
  Controls,
  type Edge,
  MarkerType,
  type Node,
  type NodeChange,
  ReactFlow,
} from "@xyflow/react";
import { type CSSProperties, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { titleOf } from "@/features/admin/api";
import { GraphNodeLabel } from "@/features/admin/routes/GraphNodeLabel";
import { type AdminRoute, stopPath, useRouteMutation } from "@/features/admin/routes/routeApi";
import { Panel } from "@/features/admin/ui/Panel";

const COLUMN_WIDTH = 260;
const ROW_HEIGHT = 110;

const FLOW_STYLE = {
  "--xy-node-background-color-default": "var(--paper-raised)",
  "--xy-node-border-default": "1.5px solid var(--ink)",
  "--xy-node-border-radius-default": "14px",
  "--xy-node-color-default": "var(--ink)",
  "--xy-node-boxshadow-hover-default": "3px 4px 0 var(--shadow-ink)",
  "--xy-node-boxshadow-selected-default": "3px 4px 0 var(--shadow-ink)",
  "--xy-handle-background-color-default": "var(--paper-raised)",
  "--xy-handle-border-color-default": "var(--ink)",
  "--xy-edge-stroke-default": "var(--ink)",
  "--xy-edge-stroke-width-default": "1.8",
  "--xy-edge-stroke-selected-default": "var(--brand)",
  "--xy-connectionline-stroke-default": "var(--brand)",
  "--xy-background-color-default": "var(--paper-sunk)",
  "--xy-background-pattern-dots-color-default": "var(--pencil)",
  "--xy-controls-button-background-color-default": "var(--paper-raised)",
  "--xy-controls-button-background-color-hover-default": "var(--wash)",
  "--xy-controls-button-color-default": "var(--ink)",
  "--xy-controls-button-border-color-default": "var(--ink)",
  "--xy-controls-box-shadow-default": "2px 3px 0 var(--shadow-ink)",
  "--xy-attribution-background-color-default": "transparent",
} as CSSProperties;

function depthOf(route: AdminRoute): Map<string, number> {
  const depends = new Map(route.stops.map((stop) => [stop.id, stop.dependsOn]));
  const memo = new Map<string, number>();
  const visit = (id: string, trail: Set<string>): number => {
    const known = memo.get(id);
    if (known !== undefined) return known;
    if (trail.has(id)) return 0;
    trail.add(id);
    const depth = Math.max(0, ...(depends.get(id) ?? []).map((dep) => visit(dep, trail) + 1));
    memo.set(id, depth);
    return depth;
  };
  route.stops.forEach((stop) => visit(stop.id, new Set()));
  return memo;
}

function buildNodes(route: AdminRoute): Node[] {
  const depths = depthOf(route);
  const rows = new Map<number, number>();
  return route.stops.map((stop, index) => {
    const depth = depths.get(stop.id) ?? 0;
    const row = rows.get(depth) ?? 0;
    rows.set(depth, row + 1);
    return {
      id: stop.id,
      position: { x: stop.graphX ?? depth * COLUMN_WIDTH, y: stop.graphY ?? row * ROW_HEIGHT },
      data: {
        label: (
          <GraphNodeLabel
            n={index + 1}
            title={titleOf(stop.point.title)}
            isStart={stop.isStart}
            isRequired={stop.isRequired}
            kind={stop.point.kind}
          />
        ),
      },
      className: stop.isRequired
        ? "!w-[220px] !p-2.5 text-left"
        : "!w-[220px] !border-dashed !p-2.5 text-left",
    };
  });
}

function buildEdges(route: AdminRoute): Edge[] {
  return route.stops.flatMap((stop) =>
    stop.dependsOn.map((dependency) => ({
      id: `${dependency}->${stop.id}`,
      source: dependency,
      target: stop.id,
      data: { stopId: stop.id, dependsOn: dependency },
      style: stop.isRequired ? undefined : { strokeDasharray: "5 5" },
      markerEnd: { type: MarkerType.ArrowClosed, color: "var(--ink)", width: 16, height: 16 },
    })),
  );
}

export function DependencyGraph({ route }: { route: AdminRoute }) {
  const { t } = useTranslation();
  const routeId = route.id;
  const [dragged, setDragged] = useState<Record<string, { x: number; y: number }>>({});
  const nodes = useMemo(
    () => buildNodes(route).map((node) => ({ ...node, position: dragged[node.id] ?? node.position })),
    [route, dragged],
  );
  const edges = useMemo(() => buildEdges(route), [route]);

  const connect = useRouteMutation(routeId, ({ stopId, dependsOn }: { stopId: string; dependsOn: string }) =>
    unwrap(
      api.POST("/api/admin/routes/{route_id}/stops/{stop_id}/dependencies", {
        params: { path: stopPath(routeId, stopId) },
        body: { dependsOnStopId: dependsOn },
      }),
    ),
  );
  const disconnect = useRouteMutation(
    routeId,
    ({ stopId, dependsOn }: { stopId: string; dependsOn: string }) =>
      unwrap(
        api.DELETE("/api/admin/routes/{route_id}/stops/{stop_id}/dependencies/{depends_on_stop_id}", {
          params: { path: { ...stopPath(routeId, stopId), depends_on_stop_id: dependsOn } },
        }),
      ),
  );
  const place = useRouteMutation(routeId, ({ stopId, x, y }: { stopId: string; x: number; y: number }) =>
    unwrap(
      api.PATCH("/api/admin/routes/{route_id}/stops/{stop_id}", {
        params: { path: stopPath(routeId, stopId) },
        body: { graphX: x, graphY: y },
      }),
    ),
  );

  const onConnect = (connection: Connection) => {
    if (connection.source && connection.target) {
      connect.mutate({ stopId: connection.target, dependsOn: connection.source });
    }
  };

  const onEdgesDelete = (removed: Edge[]) => {
    removed.forEach((edge) => disconnect.mutate({ stopId: edge.target, dependsOn: edge.source }));
  };

  return (
    <Panel title={t("app.admin.graph")} description={t("app.admin.graphHelp")}>
      <ErrorText error={connect.error ?? disconnect.error ?? place.error} />
      <div className="relative h-[560px] overflow-hidden rounded-md border-sketch font-sans [&_.react-flow__node.selected]:!bg-wash [&_.react-flow__controls-button]:border-b-[1.5px] [&_.react-flow__controls]:overflow-hidden [&_.react-flow__controls]:rounded-[10px] [&_.react-flow__controls]:border-sketch">
        <ReactFlow
          style={FLOW_STYLE}
          fitViewOptions={{ maxZoom: 1, padding: 0.3 }}
          nodes={nodes}
          edges={edges}
          onNodesChange={(changes: NodeChange[]) =>
            changes.forEach((change) => {
              if (change.type === "position" && change.position) {
                const position = change.position;
                setDragged((current) => ({ ...current, [change.id]: position }));
              }
            })
          }
          onNodeDragStop={(_, node) =>
            place.mutate({ stopId: node.id, x: node.position.x, y: node.position.y })
          }
          onConnect={onConnect}
          onEdgesDelete={onEdgesDelete}
          fitView
        >
          <Background variant={BackgroundVariant.Dots} gap={18} size={1.4} />
          <Controls showInteractive={false} />
        </ReactFlow>
        <p className="pointer-events-none absolute right-4 bottom-3 m-0 flex gap-4 text-[12px] text-ink-muted">
          <span className="inline-flex items-center gap-1.5">
            <span className="w-5 border-t-[1.8px] border-solid border-ink" />
            {t("app.admin.edgeRequired")}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="w-5 border-t-[1.8px] border-dashed border-ink" />
            {t("app.admin.edgeBonus")}
          </span>
        </p>
      </div>
    </Panel>
  );
}
