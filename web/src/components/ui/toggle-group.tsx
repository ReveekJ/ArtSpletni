import { ToggleGroup as ToggleGroupPrimitive } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

function ToggleGroup({ className, ...props }: ComponentProps<typeof ToggleGroupPrimitive.Root>) {
  return (
    <ToggleGroupPrimitive.Root
      data-slot="toggle-group"
      className={cn(
        "inline-grid w-fit auto-cols-fr grid-flow-col overflow-hidden rounded-md border-sketch shadow-sketch",
        className,
      )}
      {...props}
    />
  );
}

function ToggleGroupItem({ className, ...props }: ComponentProps<typeof ToggleGroupPrimitive.Item>) {
  return (
    <ToggleGroupPrimitive.Item
      data-slot="toggle-group-item"
      className={cn(
        "inline-flex h-11 cursor-pointer items-center justify-center gap-2 whitespace-nowrap border-0 border-r-[1.5px] border-solid border-ink bg-paper-raised px-4 font-sans text-[14px] font-semibold text-ink last:border-r-0",
        "data-[state=on]:bg-ink data-[state=on]:text-paper focus-visible:z-10 focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-brand",
        "disabled:cursor-not-allowed disabled:text-ink-muted [&_svg]:size-4 [&_svg]:shrink-0",
        className,
      )}
      {...props}
    />
  );
}

export { ToggleGroup, ToggleGroupItem };
