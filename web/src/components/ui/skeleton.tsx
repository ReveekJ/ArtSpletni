import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      aria-hidden="true"
      className={cn(
        "rounded-md border-todo bg-[repeating-linear-gradient(-38deg,var(--paper-sunk)_0_6px,transparent_6px_12px)]",
        className,
      )}
      {...props}
    />
  );
}

export { Skeleton };
