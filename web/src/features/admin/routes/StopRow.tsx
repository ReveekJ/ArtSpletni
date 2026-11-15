import { useId, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Icon } from "@/components/ui/icon";
import { Label } from "@/components/ui/label";
import { titleOf } from "@/features/admin/api";
import { fromLocalized } from "@/features/admin/localized";
import { LocalizedInput } from "@/features/admin/LocalizedInput";
import { cn } from "@/lib/utils";

interface StopRowProps {
  n: number;
  stop: Schemas["AdminStopOut"];
  onMove: (delta: number) => void;
  onUpdate: (body: Schemas["StopUpdate"]) => void;
  onRemove: () => void;
}

export function StopRow({ n, stop, onMove, onUpdate, onRemove }: StopRowProps) {
  const { t } = useTranslation();
  const id = useId();
  const [hint, setHint] = useState(fromLocalized(stop.hint));
  const published = stop.point.isPublished;
  return (
    <li className="flex flex-col gap-2.5 border-b border-solid border-rule px-5 py-3 last:border-b-0">
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={cn(
            "sk-pin size-7 shrink-0 text-[12px] shadow-none",
            stop.isStart && "sk-pin--done",
            !published && "sk-pin--locked",
          )}
        >
          {n}
        </span>
        <span
          className={cn("min-w-0 flex-1 truncate text-[15px] font-semibold", !published && "text-ink-muted")}
        >
          {titleOf(stop.point.title)}
        </span>
        <span className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label={t("app.admin.moveUp")}
            onClick={() => onMove(-1)}
          >
            <Icon name="chevron-down" size={18} className="rotate-180" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label={t("app.admin.moveDown")}
            onClick={() => onMove(1)}
          >
            <Icon name="chevron-down" size={18} />
          </Button>
          <Button
            type="button"
            variant="destructive"
            size="icon-sm"
            aria-label={t("app.common.delete")}
            onClick={onRemove}
          >
            <Icon name="trash" size={18} />
          </Button>
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 pl-10">
        <Label htmlFor={`${id}-start`} className="text-[14px] font-medium">
          <Checkbox
            id={`${id}-start`}
            checked={stop.isStart}
            onCheckedChange={(checked) => onUpdate({ isStart: checked === true })}
          />
          {t("app.admin.isStart")}
        </Label>
        <Label htmlFor={`${id}-required`} className="text-[14px] font-medium">
          <Checkbox
            id={`${id}-required`}
            checked={stop.isRequired}
            onCheckedChange={(checked) => onUpdate({ isRequired: checked === true })}
          />
          {t("app.admin.isRequired")}
        </Label>
        <details className="group w-full">
          <summary className="flex w-fit cursor-pointer list-none items-center gap-1.5 text-[14px] font-semibold">
            <Icon name="chevron-right" size={16} className="transition-transform group-open:rotate-90" />
            {t("app.admin.hint")}
          </summary>
          <div className="mt-3 flex flex-col gap-3">
            <LocalizedInput
              label={t("app.admin.hint")}
              value={hint}
              original={stop.hint}
              onChange={setHint}
            />
            <Button
              type="button"
              variant="outline"
              size="xs"
              className="self-start"
              onClick={() => onUpdate({ hint })}
            >
              {t("app.common.save")}
            </Button>
          </div>
        </details>
      </div>
    </li>
  );
}
