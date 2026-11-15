import { type ComponentPropsWithoutRef, forwardRef } from "react";

import { fieldBase } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const Textarea = forwardRef<HTMLTextAreaElement, ComponentPropsWithoutRef<"textarea">>(function Textarea(
  { className, ...props },
  ref,
) {
  return (
    <textarea
      ref={ref}
      data-slot="textarea"
      className={cn(fieldBase, "min-h-24 resize-y py-3 leading-[1.5]", className)}
      {...props}
    />
  );
});

export { Textarea };
