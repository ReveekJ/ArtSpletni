import type { ComponentProps } from "react";

import { Icon } from "@/components/ui/icon";
import { fieldBase } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface NativeSelectProps extends Omit<ComponentProps<"select">, "size"> {
  size?: "default" | "sm";
}

export function NativeSelect({ className, size = "default", ...props }: NativeSelectProps) {
  return (
    <span className={cn("relative inline-flex min-w-0", className)}>
      <select
        className={cn(
          fieldBase,
          "cursor-pointer appearance-none pr-10",
          size === "sm" ? "h-11 text-[15px]" : "h-[52px]",
        )}
        {...props}
      />
      <Icon
        name="chevron-down"
        size={18}
        className="pointer-events-none absolute top-1/2 right-3.5 -translate-y-1/2 text-ink"
      />
    </span>
  );
}
