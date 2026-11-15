import { useTranslation } from "react-i18next";

import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

interface LogoProps {
  height?: number;
  onBrand?: boolean;
  className?: string;
}

export function Logo({ height = 30, onBrand = false, className }: LogoProps) {
  const { t } = useTranslation();
  const { resolved } = useTheme();
  const light = onBrand || resolved === "dark";
  return (
    <img
      src={light ? "/brand/logo-light.png" : "/brand/logo-ink.png"}
      alt={t("common.brand")}
      height={height}
      width={Math.round((height * 1200) / 660)}
      className={cn("block w-auto select-none", className)}
      style={{ height }}
      draggable={false}
    />
  );
}
