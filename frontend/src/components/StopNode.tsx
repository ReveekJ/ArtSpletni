import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { useTranslation } from "react-i18next";

export interface StopNodeData {
  stopId: number;
  orderIndex: number;
  title: string;
  slug: string;
  stopType: "track" | "checkpoint";
  completionCriteria: string;
  onCriteriaChange: (stopId: number, criteria: string) => void;
  onDelete: (stopId: number) => void;
}

const COMPLETION_CRITERIA_KEYS = [
  { value: "scan", labelKey: "routeBuilder.criteriaScan" },
  { value: "listen_any", labelKey: "routeBuilder.criteriaListenAny" },
  { value: "listen_95", labelKey: "routeBuilder.criteriaListen95" },
  { value: "listen_100", labelKey: "routeBuilder.criteriaListen100" },
  { value: "open", labelKey: "routeBuilder.criteriaOpen" },
] as const;

function StopNodeComponent({ data }: NodeProps) {
  const { t } = useTranslation();
  const nodeData = data as unknown as StopNodeData;

  return (
    <div className="stop-node">
      <Handle type="target" position={Position.Left} />

      <div className="stop-node-header">
        <span className="stop-node-index">{nodeData.orderIndex + 1}</span>
        <span className={`stop-node-badge ${nodeData.stopType}`}>
          {nodeData.stopType === "track"
            ? t("routeBuilder.stopAudio")
            : t("routeBuilder.stopCheckpoint")}
        </span>
        <button
          className="stop-node-delete"
          onClick={() => nodeData.onDelete(nodeData.stopId)}
          aria-label={t("routeBuilder.deleteAria")}
        >
          ✕
        </button>
      </div>

      <div className="stop-node-body">
        <strong className="stop-node-title">{nodeData.title}</strong>
        {nodeData.slug ? <span className="stop-node-slug">{nodeData.slug}</span> : null}
      </div>

      <select
        className="stop-node-criteria"
        value={nodeData.completionCriteria}
        onChange={(e) => nodeData.onCriteriaChange(nodeData.stopId, e.target.value)}
      >
        {COMPLETION_CRITERIA_KEYS.map((c) => (
          <option key={c.value} value={c.value}>
            {t(c.labelKey)}
          </option>
        ))}
      </select>

      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export const StopNode = memo(StopNodeComponent);
