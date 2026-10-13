import { useCallback, useMemo, useRef } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  type Edge,
  type Node,
  type OnConnect,
  type Connection,
  type NodeTypes,
  type EdgeTypes,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useTranslation } from "react-i18next";
import { StopNode, type StopNodeData } from "./StopNode";
import DeletableEdge from "./DeletableEdge";
import { computeDagLayout } from "../utils/dagLayout";

export interface StopForGraph {
  id: number;
  order_index: number;
  stop_type: "track" | "checkpoint";
  track_id: number | null;
  checkpoint_id: number | null;
  completion_criteria: string;
  depends_on: number[];
  title: string;
  slug: string;
}

interface DependencyGraphProps {
  stops: StopForGraph[];
  onCriteriaChange: (stopId: number, criteria: string) => void;
  onDeleteStop: (stopId: number) => void;
  onDependencyAdd: (stopId: number, dependsOnStopId: number) => Promise<void>;
  onDependencyRemove: (stopId: number, dependsOnStopId: number) => Promise<void>;
}

const nodeTypes: NodeTypes = { stop: StopNode };
const edgeTypes: EdgeTypes = { deletable: DeletableEdge };

function buildEdgeId(stopId: number, dependsOnStopId: number): string {
  return `e-${dependsOnStopId}-${stopId}`;
}

export default function DependencyGraph(props: DependencyGraphProps) {
  return (
    <ReactFlowProvider>
      <DependencyGraphInner {...props} />
    </ReactFlowProvider>
  );
}

function DependencyGraphInner({
  stops,
  onCriteriaChange,
  onDeleteStop,
  onDependencyAdd,
  onDependencyRemove,
}: DependencyGraphProps) {
  const { t } = useTranslation();
  const { getNodes } = useReactFlow();
  const savedPositions = useRef<Map<number, { x: number; y: number }>>(new Map());
  const hasInitialized = useRef(false);

  const positions = useMemo(() => {
    if (!hasInitialized.current || savedPositions.current.size === 0) {
      const layout = computeDagLayout(
        stops.map((s) => ({ id: s.id, dependsOn: s.depends_on })),
      );
      for (const [id, pos] of Object.entries(layout)) {
        savedPositions.current.set(Number(id), pos);
      }
      hasInitialized.current = true;
    }
    const result: Record<number, { x: number; y: number }> = {};
    for (const stop of stops) {
      const saved = savedPositions.current.get(stop.id);
      if (saved) {
        result[stop.id] = saved;
      } else {
        const fallback = { x: 50 + (savedPositions.current.size % 3) * 280, y: 100 };
        savedPositions.current.set(stop.id, fallback);
        result[stop.id] = fallback;
      }
    }
    return result;
  }, [stops]);

  const nodes: Node[] = useMemo(
    () =>
      stops.map((stop) => {
        const pos = positions[stop.id] ?? { x: 0, y: 0 };
        const nodeData: StopNodeData = {
          stopId: stop.id,
          orderIndex: stop.order_index,
          title: stop.title,
          slug: stop.slug,
          stopType: stop.stop_type,
          completionCriteria: stop.completion_criteria,
          onCriteriaChange,
          onDelete: onDeleteStop,
        };
        return {
          id: String(stop.id),
          type: "stop",
          position: pos,
          data: nodeData as unknown as Record<string, unknown>,
          draggable: true,
        };
      }),
    [stops, positions, onCriteriaChange, onDeleteStop],
  );

  const edges: Edge[] = useMemo(() => {
    const result: Edge[] = [];
    for (const stop of stops) {
      for (const depId of stop.depends_on) {
        result.push({
          id: buildEdgeId(stop.id, depId),
          source: String(depId),
          target: String(stop.id),
          type: "deletable",
          animated: true,
          data: { onDelete: onDependencyRemove } as unknown as Record<string, unknown>,
        });
      }
    }
    return result;
  }, [stops, onDependencyRemove]);

  const onConnect: OnConnect = useCallback(
    async (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      const sourceId = Number(connection.source);
      const targetId = Number(connection.target);
      if (sourceId === targetId) return;
      try {
        await onDependencyAdd(targetId, sourceId);
      } catch {
        void Promise.resolve();
      }
    },
    [onDependencyAdd],
  );

  const onNodeDragStop = useCallback(() => {
    for (const node of getNodes()) {
      savedPositions.current.set(Number(node.id), node.position);
    }
  }, [getNodes]);

  return (
    <div className="dependency-graph-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onConnect={onConnect}
        onNodeDragStop={onNodeDragStop}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        deleteKeyCode={["Backspace", "Delete"]}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} size={1} color="rgba(0,0,0,0.06)" />
        <Controls showInteractive={false} />
      </ReactFlow>
      <p className="dependency-graph-hint">{t("routeBuilder.addDependencyHint")}</p>
    </div>
  );
}
