import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import { type ComponentPropsWithoutRef, forwardRef } from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex shrink-0 cursor-pointer items-center justify-center gap-2.5 whitespace-nowrap font-sans font-semibold no-underline border-sketch rounded-wobble " +
    "transition-[transform,box-shadow,background-color] duration-150 ease-out " +
    "hover:-translate-x-px hover:-translate-y-px active:translate-x-[3px] active:translate-y-[4px] active:shadow-none " +
    "focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-ring " +
    "disabled:pointer-events-none disabled:border-dashed disabled:border-pencil-solid disabled:bg-transparent disabled:text-ink-muted disabled:shadow-none " +
    "aria-disabled:pointer-events-none aria-disabled:border-dashed aria-disabled:border-pencil-solid aria-disabled:bg-transparent aria-disabled:text-ink-muted aria-disabled:shadow-none " +
    "[&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow-sketch-lg hover:shadow-sketch-hover",
        secondary:
          "bg-secondary text-secondary-foreground rounded-wobble-alt shadow-sketch-lg hover:shadow-sketch-hover",
        outline: "bg-paper-raised text-ink shadow-sketch hover:shadow-sketch-lg",
        ghost:
          "border-transparent bg-transparent text-ink shadow-none hover:translate-0 hover:bg-accent active:translate-0",
        link: "h-auto border-0 bg-transparent px-0 text-ink shadow-none underline decoration-1 underline-offset-6 hover:translate-0 hover:decoration-2 active:translate-0",
        destructive:
          "border-transparent bg-transparent text-destructive shadow-none hover:translate-0 hover:bg-wash active:translate-0",
      },
      size: {
        default: "h-[54px] px-[22px] text-[17px]",
        sm: "h-11 gap-2 px-4 text-[15px]",
        xs: "h-9 gap-1.5 px-3 text-[14px]",
        icon: "size-11 p-0",
        "icon-sm": "size-9 p-0",
      },
    },
    compoundVariants: [
      { variant: ["default", "secondary"], size: ["sm", "xs"], className: "shadow-sketch" },
      {
        variant: ["default", "secondary", "outline"],
        size: ["icon", "icon-sm"],
        className: "bg-paper-raised text-ink shadow-sketch",
      },
    ],
    defaultVariants: { variant: "default", size: "default" },
  },
);

type ButtonProps = ComponentPropsWithoutRef<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean; block?: boolean };

const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, size, asChild = false, block = false, ...props },
  ref,
) {
  const Comp = asChild ? Slot.Root : "button";
  return (
    <Comp
      ref={ref}
      data-slot="button"
      data-variant={variant ?? "default"}
      className={cn(buttonVariants({ variant, size }), block && "w-full", className)}
      {...props}
    />
  );
});

export { Button, buttonVariants };
