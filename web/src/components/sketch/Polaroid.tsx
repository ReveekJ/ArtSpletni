import type { CSSProperties, ReactNode } from "react";

import { Icon } from "@/components/ui/icon";
import { cn } from "@/lib/utils";

const TILTS = {
  none: "0deg",
  sm: "var(--tilt-sm)",
  md: "var(--tilt-md)",
  lg: "var(--tilt-lg)",
  alt: "var(--tilt-alt)",
} as const;

interface PolaroidProps {
  src?: string | null;
  alt?: string;
  caption?: ReactNode;
  tilt?: keyof typeof TILTS;
  tape?: boolean;
  todo?: boolean;
  photoHeight?: number;
  className?: string;
  children?: ReactNode;
}

export function Polaroid({
  src,
  alt = "",
  caption,
  tilt = "md",
  tape = true,
  todo = false,
  photoHeight = 220,
  className,
  children,
}: PolaroidProps) {
  const style = { transform: `rotate(${TILTS[tilt]})` } satisfies CSSProperties;
  return (
    <figure className={cn("sk-polaroid", todo && "sk-polaroid--todo", className)} style={style}>
      {tape && !todo ? <span className="sk-tape" aria-hidden="true" /> : null}
      <div className="sk-polaroid__photo" style={{ height: photoHeight }}>
        {children ??
          (src ? (
            <img src={src} alt={alt} className="block h-full w-full object-contain" />
          ) : (
            <Icon name="image" size={28} className="text-ink-muted" />
          ))}
      </div>
      {caption ? <figcaption className="sk-polaroid__caption">{caption}</figcaption> : null}
    </figure>
  );
}
