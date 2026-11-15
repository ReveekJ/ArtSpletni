import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

interface SegmentedProps<T extends string> {
  label: string;
  value: T;
  options: readonly { value: T; label: string }[];
  onChange: (value: T) => void;
}

export function Segmented<T extends string>({ label, value, options, onChange }: SegmentedProps<T>) {
  return (
    <ToggleGroup
      type="single"
      aria-label={label}
      value={value}
      onValueChange={(next) => {
        const match = options.find((option) => option.value === next);
        if (match) onChange(match.value);
      }}
    >
      {options.map((option) => (
        <ToggleGroupItem key={option.value} value={option.value} className="h-10">
          {option.label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}
