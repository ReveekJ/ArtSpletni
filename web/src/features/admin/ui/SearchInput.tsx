import type { ComponentProps } from "react";

import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export function SearchInput({ className, ...props }: ComponentProps<"input">) {
  return (
    <span className={cn("relative flex min-w-0 flex-[1_1_280px] sm:max-w-[420px]", className)}>
      <Icon
        name="search"
        size={18}
        className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-ink-muted"
      />
      <Input type="search" className="h-12 pl-11" {...props} />
    </span>
  );
}
