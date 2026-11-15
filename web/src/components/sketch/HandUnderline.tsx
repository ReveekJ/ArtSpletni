import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function HandUnderline({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span className={cn("sk-underline", className)}>
      {children}
      <svg aria-hidden="true" viewBox="0 0 100 8" preserveAspectRatio="none">
        <path
          d="M1 5.2 C 22 3.4, 48 6.4, 99 3.6"
          fill="none"
          stroke="var(--ink)"
          strokeWidth="1.9"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        <path
          d="M6 7 C 30 5.6, 60 7.4, 94 5.8"
          fill="none"
          stroke="var(--pencil)"
          strokeWidth="1"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </span>
  );
}
