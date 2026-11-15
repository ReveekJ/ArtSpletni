import { Switch as SwitchPrimitive } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

function Switch({ className, ...props }: ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      className={cn(
        "peer relative inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-full border-sketch bg-paper-sunk transition-colors duration-150",
        "data-[state=checked]:bg-brand focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:border-dashed disabled:border-pencil-solid",
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className="pointer-events-none block size-[19px] translate-x-[3px] rounded-full border-sketch bg-paper-raised transition-transform duration-150 data-[state=checked]:translate-x-[23px]"
      />
    </SwitchPrimitive.Root>
  );
}

export { Switch };
