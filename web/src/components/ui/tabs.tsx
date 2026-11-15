import { Tabs as TabsPrimitive } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

function Tabs({ className, ...props }: ComponentProps<typeof TabsPrimitive.Root>) {
  return <TabsPrimitive.Root data-slot="tabs" className={cn("flex flex-col gap-4", className)} {...props} />;
}

function TabsList({ className, ...props }: ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      className={cn(
        "flex items-end overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden border-b-[1.5px] border-solid border-ink",
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
      className={cn(
        "-mb-[1.5px] inline-flex h-10 cursor-pointer items-center gap-2 whitespace-nowrap rounded-t-[12px] border-[1.5px] border-b-0 border-solid border-transparent bg-transparent px-[18px] font-sans text-[14px] font-semibold text-ink-muted",
        "hover:text-ink data-[state=active]:border-ink data-[state=active]:bg-paper data-[state=active]:text-ink data-[state=active]:shadow-[0_1.5px_0_var(--paper)]",
        "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring disabled:cursor-not-allowed disabled:opacity-60 [&_svg]:size-4",
        className,
      )}
      {...props}
    />
  );
}

function TabsContent({ className, ...props }: ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content data-slot="tabs-content" className={cn("outline-none", className)} {...props} />
  );
}

export { Tabs, TabsContent, TabsList, TabsTrigger };
