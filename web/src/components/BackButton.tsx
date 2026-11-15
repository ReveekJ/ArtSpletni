import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { useGoBack } from "@/lib/useGoBack";

interface BackButtonProps {
  fallback: string;
  label?: string;
  className?: string;
}

export function BackButton({ fallback, label, className }: BackButtonProps) {
  const { t } = useTranslation();
  const goBack = useGoBack(fallback);
  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      className={className}
      aria-label={label ?? t("app.common.back")}
      onClick={goBack}
    >
      <Icon name="arrow-left" />
    </Button>
  );
}
