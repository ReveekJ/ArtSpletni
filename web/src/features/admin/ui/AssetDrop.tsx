import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { UploadButton } from "@/components/UploadButton";
import { Icon, type IconName } from "@/components/ui/icon";
import type { UploadScope } from "@/lib/upload";
import { cn } from "@/lib/utils";

interface AssetDropProps {
  assetId: string | null;
  accept: string;
  scope: UploadScope;
  isPublic?: boolean;
  icon?: IconName;
  onUploaded: (asset: Schemas["MediaAssetOut"]) => void;
}

export function AssetDrop({ assetId, accept, scope, isPublic, icon = "image", onUploaded }: AssetDropProps) {
  const { t } = useTranslation();
  return (
    <div
      className={cn(
        "flex min-h-[72px] flex-wrap items-center gap-3 rounded-md px-3.5 py-3",
        assetId
          ? "border-sketch bg-paper-raised"
          : "border-2 border-dashed border-pencil-solid bg-transparent",
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "grid size-12 shrink-0 place-items-center rounded-[10px]",
          assetId ? "border-sketch bg-paper-sunk text-ink" : "border-todo text-ink-muted",
        )}
      >
        <Icon name={assetId ? "check" : icon} size={22} />
      </span>
      <span className="flex min-w-0 flex-1 flex-col">
        <span className={cn("truncate text-[14px]", assetId ? "font-semibold" : "text-ink-muted")}>
          {assetId ?? t("app.admin.noFile")}
        </span>
      </span>
      <UploadButton accept={accept} scope={scope} isPublic={isPublic} onUploaded={onUploaded} />
    </div>
  );
}
