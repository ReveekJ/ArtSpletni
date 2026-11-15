import { CheckIcon } from "lucide-react";
import { Checkbox as CheckboxPrimitive } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

function Checkbox({ className, ...props }: ComponentProps<typeof CheckboxPrimitive.Root>) {
  return (
    <CheckboxPrimitive.Root
      data-slot="checkbox"
      className={cn(
        "peer size-5 shrink-0 cursor-pointer rounded-[5px] border-sketch bg-paper-raised text-paper",
        "data-[state=checked]:bg-ink focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:border-dashed disabled:border-pencil-solid",
        className,
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator data-slot="checkbox-indicator" className="grid place-content-center">
        <CheckIcon className="size-3.5" strokeWidth={2.6} />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}

export { Checkbox };
