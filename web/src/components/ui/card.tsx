import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import { type ComponentProps, type ComponentPropsWithoutRef, forwardRef } from "react";

import { cn } from "@/lib/utils";

const cardVariants = cva("relative box-border flex flex-col rounded-lg text-card-foreground", {
  variants: {
    variant: {
      default: "border-sketch bg-card shadow-sketch-lg",
      pencil:
        "border-sketch bg-card shadow-sketch-lg after:pointer-events-none after:absolute after:-inset-px after:translate-x-[3px] after:-translate-y-[3px] after:rotate-[.4deg] after:rounded-[inherit] after:border after:border-pencil after:content-['']",
      todo: "border-2 border-dashed border-pencil-solid bg-transparent shadow-none",
      flat: "border-sketch bg-card",
      brand: "border-sketch bg-brand text-on-brand shadow-sketch-lg",
    },
    interactive: {
      true: "no-underline transition-[transform,box-shadow] duration-150 ease-out hover:-translate-x-px hover:-translate-y-px hover:shadow-sketch-hover",
      false: "",
    },
  },
  defaultVariants: { variant: "default", interactive: false },
});

type CardProps = ComponentPropsWithoutRef<"div"> & VariantProps<typeof cardVariants> & { asChild?: boolean };

const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { className, variant, interactive, asChild = false, ...props },
  ref,
) {
  const Comp = asChild ? Slot.Root : "div";
  return (
    <Comp
      ref={ref}
      data-slot="card"
      className={cn(cardVariants({ variant, interactive }), className)}
      {...props}
    />
  );
});

function CardHeader({ className, ...props }: ComponentProps<"div">) {
  return (
    <div data-slot="card-header" className={cn("flex flex-col gap-1.5 px-5 pt-5", className)} {...props} />
  );
}

function CardTitle({ className, ...props }: ComponentProps<"h3">) {
  return <h3 data-slot="card-title" className={cn("m-0 text-h2", className)} {...props} />;
}

function CardDescription({ className, ...props }: ComponentProps<"p">) {
  return (
    <p data-slot="card-description" className={cn("m-0 text-body-sm text-ink-muted", className)} {...props} />
  );
}

function CardContent({ className, ...props }: ComponentProps<"div">) {
  return <div data-slot="card-content" className={cn("p-5", className)} {...props} />;
}

function CardFooter({ className, ...props }: ComponentProps<"div">) {
  return (
    <div data-slot="card-footer" className={cn("flex items-center gap-3 px-5 pb-5", className)} {...props} />
  );
}

export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, cardVariants };
