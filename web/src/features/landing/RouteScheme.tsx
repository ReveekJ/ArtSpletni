import { type CSSProperties, useId } from "react";

import { DrawnSvg } from "@/components/motion/DrawnSvg";
import { Reveal } from "@/components/motion/Reveal";
import { MapPin } from "@/components/sketch/Route";

const PINS: ReadonlyArray<readonly [number, number]> = [
  [10.4, 84.6],
  [30.7, 63.5],
  [53.7, 72.7],
  [68.9, 49.6],
  [90.4, 35.8],
  [57, 23.5],
  [92.6, 12.3],
];

const ROADS = [
  "M-10 90 C 180 104, 360 130, 560 150",
  "M90 -10 C 98 170, 112 340, 124 540",
  "M-10 300 C 180 284, 360 254, 560 236",
  "M268 -10 C 260 170, 246 340, 234 540",
  "M420 -10 C 428 170, 446 340, 458 540",
  "M-10 450 C 180 440, 360 420, 560 410",
];

const ROUTE =
  "M56 440 C 100 386, 120 352, 166 330 S 256 396, 290 378 S 340 272, 372 258 S 444 226, 488 186 S 356 146, 308 122 S 444 46, 500 64";

const ROUTE_DRAW_STYLE = { "--i": 9, "--draw-duration": "2.4s" } as CSSProperties;
const PIN_DELAY_MS = 1350;
const PIN_STEP_MS = 380;

export function RouteScheme({ label }: { label: string }) {
  const maskId = useId();
  return (
    <Reveal
      variant="place"
      role="img"
      aria-label={label}
      className="relative box-border h-[clamp(360px,44vw,520px)] overflow-hidden rounded-lg border-sketch bg-map-land shadow-sketch-lg"
    >
      <DrawnSvg
        aria-hidden="true"
        viewBox="0 0 540 520"
        preserveAspectRatio="xMidYMid slice"
        pencil={false}
        delay={200}
        className="absolute inset-0 h-full w-full [--draw-duration:1.1s] [--ink-lag:0ms]"
      >
        <defs>
          <mask id={maskId} maskUnits="userSpaceOnUse" x="-20" y="-20" width="600" height="580">
            <path d={ROUTE} stroke="#fff" strokeWidth="10" fill="none" style={ROUTE_DRAW_STYLE} />
          </mask>
        </defs>
        <path d="M330 0 C 360 50, 420 60, 480 50 L 560 30 L 560 0 Z" fill="var(--map-park)" stroke="none" />
        {ROADS.map((road) => (
          <path
            key={road}
            d={road}
            stroke="var(--map-road)"
            strokeWidth="12"
            fill="none"
            strokeLinecap="round"
          />
        ))}
        <path
          d="M-10 360 C 90 352, 140 452, 256 454 S 390 380, 440 452 S 520 480, 560 474"
          stroke="var(--map-water)"
          strokeWidth="32"
          fill="none"
        />
        <path
          d={ROUTE}
          mask={`url(#${maskId})`}
          stroke="var(--map-route)"
          strokeWidth="3"
          strokeDasharray="8 8"
          strokeLinecap="round"
          fill="none"
          style={{ "--i": 0 } as CSSProperties}
        />
      </DrawnSvg>
      {PINS.map(([x, y], index) => (
        <span
          key={index}
          className="sk-pop absolute -translate-x-1/2 -translate-y-1/2"
          style={
            {
              left: `${x}%`,
              top: `${y}%`,
              "--reveal-index": index,
              "--pop-delay": `${PIN_DELAY_MS}ms`,
              "--pop-step": `${PIN_STEP_MS}ms`,
            } as CSSProperties
          }
        >
          <MapPin
            n={index + 1}
            state={index === 0 ? "current" : "open"}
            className="size-[34px] text-[14px]"
          />
        </span>
      ))}
    </Reveal>
  );
}
