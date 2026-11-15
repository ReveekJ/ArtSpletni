import { Tabs as TabsPrimitive } from "radix-ui";
import { type ComponentProps, useRef, useState } from "react";

import { cn } from "@/lib/utils";

type TabsDirection = "forward" | "back";

function ownTriggers(root: HTMLDivElement | null): HTMLElement[] {
  if (!root) return [];
  return Array.from(root.querySelectorAll<HTMLElement>("[data-slot='tabs-trigger']")).filter(
    (trigger) => trigger.closest("[data-slot='tabs']") === root,
  );
}

function Tabs({ className, onValueChange, ...props }: ComponentProps<typeof TabsPrimitive.Root>) {
  const root = useRef<HTMLDivElement>(null);
  const [direction, setDirection] = useState<TabsDirection>("forward");
  const handleValueChange = (value: string) => {
    const triggers = ownTriggers(root.current);
    const current = triggers.findIndex((trigger) => trigger.dataset.state === "active");
    const next = triggers.findIndex((trigger) => trigger.dataset.value === value);
    setDirection(next < current ? "back" : "forward");
    onValueChange?.(value);
  };
  return (
    <TabsPrimitive.Root
      ref={root}
      data-slot="tabs"
      data-direction={direction}
      className={cn("flex flex-col gap-4", className)}
      onValueChange={handleValueChange}
      {...props}
    />
  );
}

function TabsList({ className, ...props }: ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      className={cn(
        "flex items-end overflow-x-auto overflow-y-hidden pt-1.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden shadow-[inset_0_-1.5px_0_var(--ink)]",
        className,
      )}
      {...props}
    />
  );
}

function TabsTrigger({ className, ...props }: ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      data-value={props.value}
      className={cn(
        "inline-flex h-10 cursor-pointer items-center gap-2 whitespace-nowrap rounded-t-[12px] border-[1.5px] border-b-0 border-solid border-transparent bg-transparent px-[18px] font-sans text-[14px] font-semibold text-ink-muted",
        "hover:text-ink data-[state=active]:border-ink data-[state=active]:bg-paper data-[state=active]:text-ink",
        "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring disabled:cursor-not-allowed disabled:opacity-60 [&_svg]:size-4",
        className,
      )}
      {...props}
    />
  );
}

function TabsContent({ className, ...props }: ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className={cn("sk-tab-panel outline-none", className)}
      {...props}
    />
  );
}

export { Tabs, TabsContent, TabsList, TabsTrigger };
