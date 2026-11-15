import type { ReactNode } from "react";

import { Reveal } from "@/components/motion/Reveal";
import { cn } from "@/lib/utils";

interface SectionProps {
  id?: string;
  band?: boolean;
  labelledBy?: string;
  className?: string;
  innerClassName?: string;
  children: ReactNode;
}

export function Section({ id, band = false, labelledBy, className, innerClassName, children }: SectionProps) {
  return (
    <section
      id={id}
      aria-labelledby={labelledBy}
      className={cn(
        "relative scroll-mt-6 py-[clamp(64px,8vw,112px)]",
        band && "border-y-[1.5px] border-solid border-ink bg-paper-band",
        className,
      )}
    >
      <div className={cn("mx-auto box-border max-w-[1184px] px-[clamp(20px,4.5vw,64px)]", innerClassName)}>
        {children}
      </div>
    </section>
  );
}

interface SectionHeadingProps {
  id: string;
  kicker: string;
  title: string;
  text?: string;
  className?: string;
}

export function SectionHeading({ id, kicker, title, text, className }: SectionHeadingProps) {
  return (
    <div className={cn("flex max-w-[640px] flex-col gap-2.5", className)}>
      <Reveal asChild variant="stick">
        <p className="sk-kicker m-0 self-start">{kicker}</p>
      </Reveal>
      <Reveal asChild index={1}>
        <h2 id={id} className="m-0 text-display">
          {title}
        </h2>
      </Reveal>
      {text ? (
        <Reveal asChild index={2}>
          <p className="m-0 text-body-lg text-ink-muted">{text}</p>
        </Reveal>
      ) : null}
    </div>
  );
}
