import { type ReactNode, useId } from "react";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";

interface FormFieldProps {
  label: ReactNode;
  hint?: ReactNode;
  className?: string;
  children: (id: string) => ReactNode;
}

export function FormField({ label, hint, className, children }: FormFieldProps) {
  const id = useId();
  return (
    <div className={cn("flex min-w-0 flex-col gap-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      {children(id)}
      {hint ? <p className="sk-hint">{hint}</p> : null}
    </div>
  );
}

interface SwitchFieldProps {
  label: ReactNode;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  className?: string;
}

export function SwitchField({ label, checked, onCheckedChange, className }: SwitchFieldProps) {
  const id = useId();
  return (
    <div className={cn("flex min-h-11 items-center justify-between gap-3", className)}>
      <Label htmlFor={id} className="text-[15px] font-medium">
        {label}
      </Label>
      <Switch id={id} checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  );
}
