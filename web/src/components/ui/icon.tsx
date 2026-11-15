import type { SVGProps } from "react";

import { ICON_PATHS, type IconName } from "@/components/ui/iconPaths";

interface IconProps extends Omit<SVGProps<SVGSVGElement>, "name"> {
  name: IconName;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function Icon({ name, size = 20, strokeWidth = 1.8, label, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      dangerouslySetInnerHTML={{ __html: ICON_PATHS[name] }}
      {...props}
    />
  );
}

export type { IconName };
