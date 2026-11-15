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

export function RouteScheme({ label }: { label: string }) {
  return (
    <div
      role="img"
      aria-label={label}
      className="relative box-border h-[clamp(360px,44vw,520px)] overflow-hidden rounded-lg border-sketch bg-map-land shadow-sketch-lg"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 540 520"
        preserveAspectRatio="xMidYMid slice"
        className="absolute inset-0 h-full w-full"
      >
        <path d="M330 0 C 360 50, 420 60, 480 50 L 560 30 L 560 0 Z" fill="var(--map-park)" />
        <path
          d="M-10 90 C 180 104, 360 130, 560 150 M-10 300 C 180 284, 360 254, 560 236 M90 -10 C 98 170, 112 340, 124 540 M268 -10 C 260 170, 246 340, 234 540 M420 -10 C 428 170, 446 340, 458 540 M-10 450 C 180 440, 360 420, 560 410"
          stroke="var(--map-road)"
          strokeWidth="12"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M-10 360 C 90 352, 140 452, 256 454 S 390 380, 440 452 S 520 480, 560 474"
          stroke="var(--map-water)"
          strokeWidth="32"
          fill="none"
        />
        <path
          d="M56 440 C 100 386, 120 352, 166 330 S 256 396, 290 378 S 340 272, 372 258 S 444 226, 488 186 S 356 146, 308 122 S 444 46, 500 64"
          stroke="var(--map-route)"
          strokeWidth="3"
          strokeDasharray="8 8"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      {PINS.map(([x, y], index) => (
        <span
          key={index}
          className="absolute -translate-x-1/2 -translate-y-1/2"
          style={{ left: `${x}%`, top: `${y}%` }}
        >
          <MapPin
            n={index + 1}
            state={index === 0 ? "current" : "open"}
            className="size-[34px] text-[14px]"
          />
        </span>
      ))}
    </div>
  );
}
