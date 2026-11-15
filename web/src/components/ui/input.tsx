import { type ComponentPropsWithoutRef, forwardRef } from "react";

import { cn } from "@/lib/utils";

const fieldBase =
  "w-full min-w-0 box-border rounded-md border-sketch bg-paper-raised px-4 font-sans text-[16px] text-ink placeholder:text-ink-muted " +
  "focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-ring focus-visible:shadow-sketch " +
  "disabled:cursor-not-allowed disabled:border-dashed disabled:border-pencil-solid disabled:text-ink-muted " +
  "aria-invalid:border-2 aria-invalid:border-danger";

const Input = forwardRef<HTMLInputElement, ComponentPropsWithoutRef<"input">>(function Input(
  { className, type, ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      data-slot="input"
      className={cn(
        fieldBase,
        "h-[52px] file:mr-3 file:border-0 file:bg-transparent file:font-semibold file:text-ink",
        className,
      )}
      {...props}
    />
  );
});

export { fieldBase, Input };
