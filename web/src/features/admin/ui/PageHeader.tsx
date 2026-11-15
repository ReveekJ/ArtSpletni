import type { ReactNode } from "react";

interface PageHeaderProps {
  title: ReactNode;
  eyebrow?: ReactNode;
  subtitle?: ReactNode;
  badge?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ title, eyebrow, subtitle, badge, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex min-w-0 flex-col gap-1">
        {eyebrow ? <span className="text-caption text-ink-muted">{eyebrow}</span> : null}
        <div className="flex flex-wrap items-center gap-3.5">
          <h1 className="m-0 text-h1">{title}</h1>
          {badge}
        </div>
        {subtitle ? <p className="m-0 max-w-[640px] text-body-sm text-ink-muted">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </div>
  );
}
