import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";

interface DeletableEdgeData {
  onDelete: (stopId: number, dependsOnStopId: number) => void;
}

export default function DeletableEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeData = data as unknown as DeletableEdgeData;
  const parts = id.replace("e-", "").split("-");
  const dependsOnStopId = Number(parts[0]);
  const stopId = Number(parts[1]);

  return (
    <>
      <BaseEdge id={id} path={edgePath} />
      <EdgeLabelRenderer>
        <button
          className="edge-delete-button"
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: "all",
          }}
          onClick={() => edgeData.onDelete(stopId, dependsOnStopId)}
          aria-label="Delete dependency"
        >
          ✕
        </button>
      </EdgeLabelRenderer>
    </>
  );
}
