import { type ChangeEvent, useId, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { buttonVariants } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { type UploadScope, uploadFile } from "@/lib/upload";
import { cn } from "@/lib/utils";

interface UploadButtonProps {
  accept: string;
  scope: UploadScope;
  isPublic?: boolean;
  label?: string;
  onUploaded: (asset: Schemas["MediaAssetOut"]) => void;
}

export function UploadButton({ accept, scope, isPublic = false, label, onUploaded }: UploadButtonProps) {
  const { t } = useTranslation();
  const id = useId();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const onChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      onUploaded(await uploadFile(file, scope, isPublic));
    } catch (caught) {
      setError(caught);
    } finally {
      setBusy(false);
    }
  };

  return (
    <span className="inline-flex flex-col items-start gap-2">
      <input
        id={id}
        type="file"
        accept={accept}
        className="peer sr-only"
        disabled={busy}
        onChange={(event) => void onChange(event)}
      />
      <label
        htmlFor={id}
        aria-disabled={busy || undefined}
        className={cn(
          buttonVariants({ variant: "outline", size: "sm" }),
          "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-3 peer-focus-visible:outline-ring",
        )}
      >
        <Icon name="upload" size={18} />
        {busy ? t("app.admin.uploading") : (label ?? t("app.admin.upload"))}
      </label>
      <ErrorText error={error} />
    </span>
  );
}
