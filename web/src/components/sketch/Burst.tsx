import type { ReactNode } from "react";

import { DrawnSvg } from "@/components/motion/DrawnSvg";

const BURST =
  "M96.2 10.1 L115.1 55.6 L153.6 38.6 L140.5 72.2 L182.6 82.1 L144.3 111.5 L174.4 148.5 L126.8 133.4 L130.8 190.6 L99.8 148.2 L70.0 175.8 L68.4 134.6 L31.3 142.7 L54.6 105.3 L6.2 80.1 L57.7 73.6 L38.1 28.6 L82.5 53.2Z";

const SUN =
  "M95.8 19.7 Q102.6 62.1 111.0 61.5 Q117.8 66.4 146.5 33.1 Q125.3 71.6 131.1 74.8 Q133.0 81.1 179.4 66.3 Q136.5 89.5 140.0 99.9 Q136.5 110.4 186.7 136.4 Q133.0 118.8 130.7 125.7 Q124.3 129.2 145.0 169.4 Q116.7 134.1 111.2 138.4 Q104.3 137.8 99.4 183.8 Q95.2 137.7 88.8 138.4 Q83.7 134.3 57.1 168.1 Q76.0 129.5 69.1 125.4 Q66.5 117.9 10.0 135.0 Q63.2 109.4 60.0 99.8 Q63.3 90.2 12.5 65.1 Q66.7 81.8 69.2 74.5 Q75.9 70.6 55.8 30.7 Q83.5 65.8 87.8 61.9 Q93.5 62.6 95.8 19.7 Z";

interface ArtProps {
  size?: number;
  className?: string;
  children?: ReactNode;
  drawn?: boolean;
  delay?: number;
}

function BurstShapes() {
  return (
    <>
      <path transform="translate(4 5)" d={BURST} fill="var(--wash)" stroke="none" />
      <path d={BURST} fill="var(--brand)" stroke="var(--ink)" strokeWidth="2" strokeLinejoin="round" />
    </>
  );
}

export function Burst({ size = 200, className, children, drawn = false, delay = 0 }: ArtProps) {
  const svgProps = {
    "aria-hidden": true,
    viewBox: "-4 -4 210 210",
    width: size,
    height: size,
    style: { position: "absolute", inset: 0 },
  } as const;
  return (
    <span
      className={className}
      style={{ position: "relative", display: "inline-block", width: size, height: size }}
    >
      {drawn ? (
        <DrawnSvg {...svgProps} delay={delay}>
          <BurstShapes />
        </DrawnSvg>
      ) : (
        <svg {...svgProps}>
          <BurstShapes />
        </svg>
      )}
      {children ? (
        <span
          style={{
            position: "absolute",
            inset: 0,
            display: "grid",
            placeItems: "center",
            color: "var(--on-brand)",
          }}
        >
          {children}
        </span>
      ) : null}
    </span>
  );
}

function SunShapes() {
  return (
    <>
      <path transform="translate(3 4)" d={SUN} fill="var(--wash)" stroke="none" />
      <path d={SUN} fill="none" stroke="var(--ink)" strokeWidth="1.2" strokeLinejoin="round" />
      <circle cx="102.5" cy="102.5" r="25" fill="var(--brand)" stroke="none" />
      <circle cx="100" cy="100" r="25" fill="none" stroke="var(--ink)" strokeWidth="1.2" />
    </>
  );
}

export function Sun({ size = 200, className, drawn = false, delay = 0 }: ArtProps) {
  const svgProps = {
    "aria-hidden": true,
    viewBox: "0 0 206 206",
    width: size,
    height: size,
    className,
  } as const;
  if (drawn)
    return (
      <DrawnSvg {...svgProps} delay={delay}>
        <SunShapes />
      </DrawnSvg>
    );
  return (
    <svg {...svgProps}>
      <SunShapes />
    </svg>
  );
}
