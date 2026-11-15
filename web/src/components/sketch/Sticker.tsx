import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

interface StickerProps extends ComponentProps<"span"> {
  side?: "right" | "left";
}

export function Sticker({ side = "right", className, ...props }: StickerProps) {
  return <span className={cn("sk-note", side === "left" && "sk-note--left", className)} {...props} />;
}

export function Tape({ className, ...props }: ComponentProps<"span">) {
  return <span aria-hidden="true" className={cn("sk-tape", className)} {...props} />;
}

export function Stamp({ className, ...props }: ComponentProps<"span">) {
  return <span className={cn("sk-stamp", className)} {...props} />;
}

export function Kicker({ className, ...props }: ComponentProps<"p">) {
  return <p className={cn("sk-kicker m-0", className)} {...props} />;
}

export function ScriptWord({ className, ...props }: ComponentProps<"span">) {
  return (
    <span
      className={cn("sk-script [:lang(zh)_&]:font-sans [:lang(zh)_&]:font-semibold", className)}
      {...props}
    />
  );
}
