import { useTranslation } from "react-i18next";

import { ApiError } from "@/api/client";
import { Icon } from "@/components/ui/icon";

interface ErrorTextProps {
  error?: unknown;
  code?: string | null;
}

export function ErrorText({ error, code }: ErrorTextProps) {
  const { t } = useTranslation();
  const resolvedCode = error instanceof ApiError ? error.code : code;
  if (!error && !code) return null;
  const fallback = error instanceof ApiError ? error.message : t("app.common.error");
  return (
    <p className="sk-error" role="alert">
      <Icon name="alert" size={16} />
      {resolvedCode ? t(`app.errors.${resolvedCode}`, { defaultValue: fallback }) : fallback}
    </p>
  );
}
