import { Slot } from "radix-ui";
import type { CSSProperties, HTMLAttributes } from "react";

import { useInView } from "@/lib/useInView";
import { cn } from "@/lib/utils";

export type RevealVariant = "rise" | "place" | "stick" | "drop" | "stamp";

interface RevealProps extends HTMLAttributes<HTMLDivElement> {
  asChild?: boolean;
  variant?: RevealVariant;
  index?: number;
  delay?: number;
}

export function Reveal({
  asChild = false,
  variant = "rise",
  index = 0,
  delay = 0,
  className,
  style,
  ...props
}: RevealProps) {
  const [ref, inView] = useInView<HTMLDivElement>();
  const Comp = asChild ? Slot.Root : "div";
  const motionStyle = { "--reveal-index": index, "--reveal-delay": `${delay}ms`, ...style } as CSSProperties;
  return (
    <Comp
      ref={ref}
      data-reveal={variant}
      data-inview={inView}
      className={cn("sk-reveal", className)}
      style={motionStyle}
      {...props}
    />
  );
}
