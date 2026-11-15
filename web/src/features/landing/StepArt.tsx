import { DrawnSvg } from "@/components/motion/DrawnSvg";

export type StepArtKind = "stand" | "phone" | "listen";

const SVG_PROPS = {
  width: 120,
  height: 120,
  viewBox: "0 0 120 120",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
} as const;

export function StepArt({ kind, delay = 0 }: { kind: StepArtKind; delay?: number }) {
  if (kind === "stand") {
    return (
      <DrawnSvg {...SVG_PROPS} delay={delay}>
        <rect x="33" y="14" width="54" height="72" rx="6" fill="var(--paper-raised)" />
        <circle cx="62" cy="52" r="14" fill="var(--brand)" stroke="none" />
        <circle cx="60" cy="50" r="14" />
        <path d="M44 24 H76" />
        <path d="M52 86 L46 110 M68 86 L74 110 M40 110 H80" />
      </DrawnSvg>
    );
  }
  if (kind === "phone") {
    return (
      <DrawnSvg {...SVG_PROPS} delay={delay}>
        <circle cx="38" cy="66" r="22" fill="var(--wash)" stroke="none" />
        <circle cx="36" cy="64" r="22" />
        <rect
          x="62"
          y="20"
          width="38"
          height="76"
          rx="8"
          fill="var(--paper-raised)"
          transform="rotate(-12 81 58)"
        />
        <path d="M54 46 a10 10 0 0 1 0 14 M48 40 a18 18 0 0 1 0 26" />
      </DrawnSvg>
    );
  }
  return (
    <DrawnSvg {...SVG_PROPS} delay={delay}>
      <path d="M28 78 V62 a32 32 0 0 1 64 0 V78" />
      <rect x="22" y="66" width="18" height="30" rx="6" fill="var(--brand)" />
      <rect x="80" y="66" width="18" height="30" rx="6" fill="var(--paper-raised)" />
      <path d="M50 40 C 54 36, 66 36, 70 40" strokeDasharray="3 4" />
    </DrawnSvg>
  );
}
