import { Icon } from "@/components/ui/icon";
import { cn } from "@/lib/utils";

interface PlayButtonProps {
  playing: boolean;
  disabled?: boolean;
  label: string;
  onClick: () => void;
  className?: string;
}

export function PlayButton({ playing, disabled = false, label, onClick, className }: PlayButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        "sk-play shrink-0 disabled:cursor-not-allowed disabled:opacity-60",
        disabled && "[&::before]:bg-transparent [&::after]:border-dashed [&::after]:border-pencil-solid",
        className,
      )}
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      aria-pressed={playing}
    >
      <Icon
        name={playing ? "pause" : "play"}
        size={26}
        strokeWidth={2.4}
        className={disabled ? "text-ink-muted" : "text-on-brand"}
      />
    </button>
  );
}
