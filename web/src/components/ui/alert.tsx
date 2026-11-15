import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

const alertVariants = cva(
  "flex w-full items-start gap-3 rounded-md border-sketch px-4 py-3.5 text-body-sm text-ink [&>svg]:mt-0.5 [&>svg]:size-[18px] [&>svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-note",
        danger: "border-danger bg-paper-raised [&>svg]:text-danger",
        success: "bg-paper-raised [&>svg]:text-success",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

function Alert({ className, variant, ...props }: ComponentProps<"div"> & VariantProps<typeof alertVariants>) {
  return (
    <div data-slot="alert" role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
  );
}

function AlertTitle({ className, ...props }: ComponentProps<"div">) {
  return <div data-slot="alert-title" className={cn("font-semibold", className)} {...props} />;
}

function AlertDescription({ className, ...props }: ComponentProps<"div">) {
  return <div data-slot="alert-description" className={cn("flex flex-col gap-1", className)} {...props} />;
}

export { Alert, AlertDescription, AlertTitle };
