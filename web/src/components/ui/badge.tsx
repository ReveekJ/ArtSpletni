import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import { type ComponentPropsWithoutRef, forwardRef } from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex w-fit shrink-0 items-center gap-1.5 whitespace-nowrap rounded-wobble border-sketch px-3 py-1 text-[13px] leading-[1.2] font-semibold text-ink [&>svg]:pointer-events-none [&>svg]:size-3.5",
  {
    variants: {
      variant: {
        default: "bg-paper-raised",
        now: "bg-wash",
        note: "bg-note",
        todo: "border-dashed border-pencil-solid bg-transparent text-ink-muted",
        ink: "bg-ink text-paper",
        brand: "bg-brand text-on-brand",
        success: "border-transparent bg-transparent pl-0 text-success",
        danger: "border-transparent bg-transparent pl-0 text-danger",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

type BadgeProps = ComponentPropsWithoutRef<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean };

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(function Badge(
  { className, variant, asChild = false, ...props },
  ref,
) {
  const Comp = asChild ? Slot.Root : "span";
  return (
    <Comp ref={ref} data-slot="badge" className={cn(badgeVariants({ variant }), className)} {...props} />
  );
});

export { Badge, badgeVariants };
