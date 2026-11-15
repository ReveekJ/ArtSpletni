import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { Icon } from "@/components/ui/icon";
import { cn } from "@/lib/utils";

interface GraphNodeLabelProps {
  n: number;
  title: string;
  kind: Schemas["PointKind"];
  isStart: boolean;
  isRequired: boolean;
}

export function GraphNodeLabel({ n, title, kind, isStart, isRequired }: GraphNodeLabelProps) {
  const { t } = useTranslation();
  return (
    <span className="flex items-center gap-2.5">
      <span
        className={cn(
          "grid size-7 shrink-0 place-items-center rounded-wobble text-[12px] font-bold",
          isStart
            ? "border-sketch bg-ink text-paper"
            : kind === "partner"
              ? "border-todo bg-note"
              : "border-sketch bg-paper-sunk",
        )}
      >
        {isStart ? <Icon name="play" size={12} strokeWidth={2.6} /> : n}
      </span>
      <span className="flex min-w-0 flex-col">
        <span className="truncate text-[14px] font-semibold leading-[1.3]">{title}</span>
        <span className="text-[12px] leading-[1.3] text-ink-muted">
          {t(`app.admin.kinds.${kind}`)} · {isRequired ? t("app.admin.isRequired") : t("app.admin.edgeBonus")}
        </span>
      </span>
    </span>
  );
}
