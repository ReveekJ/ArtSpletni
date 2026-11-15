import { cn } from "@/lib/utils";

interface MeterProps {
  ratio: number;
  label: string;
  tone?: "ink" | "brand";
}

export function Meter({ ratio, label, tone = "ink" }: MeterProps) {
  const percent = Math.max(0, Math.min(100, Math.round(ratio * 100)));
  return (
    <span className="flex min-w-0 items-center gap-2.5">
      <span
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className={cn("sk-bar min-w-[60px] flex-1", tone === "brand" && "sk-bar--brand")}
      >
        <span style={{ width: `${percent}%` }} />
      </span>
      <span className="w-11 shrink-0 text-right tabular">{percent}%</span>
    </span>
  );
}
