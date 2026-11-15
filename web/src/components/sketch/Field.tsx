import { type ReactNode, useId } from "react";

import { Icon } from "@/components/ui/icon";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface FieldRenderProps {
  id: string;
  describedBy?: string;
  invalid: boolean;
}

interface FieldProps {
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  className?: string;
  children: (props: FieldRenderProps) => ReactNode;
}

export function Field({ label, hint, error, className, children }: FieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      {children({ id, describedBy, invalid: Boolean(error) })}
      {hint ? (
        <p id={hintId} className="sk-hint">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className="sk-error" role="alert">
          <Icon name="alert" size={16} />
          {error}
        </p>
      ) : null}
    </div>
  );
}
