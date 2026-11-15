import type { ReactNode } from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface PanelProps {
  title?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

export function Panel({ title, description, actions, className, bodyClassName, children }: PanelProps) {
  return (
    <Card className={cn("min-w-0", className)}>
      {title || actions ? (
        <div className="flex flex-wrap items-start justify-between gap-3 px-5 pt-[18px]">
          <div className="flex min-w-0 flex-col gap-1">
            {title ? <h2 className="m-0 text-[17px] font-semibold leading-[1.3]">{title}</h2> : null}
            {description ? <p className="m-0 text-caption text-ink-muted">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
        </div>
      ) : null}
      <div className={cn("flex flex-col gap-4 px-5 pt-4 pb-5", bodyClassName)}>{children}</div>
    </Card>
  );
}
