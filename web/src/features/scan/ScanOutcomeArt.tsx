import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { Burst } from "@/components/sketch/Burst";
import { Polaroid } from "@/components/sketch/Polaroid";
import { Stamp, Sticker } from "@/components/sketch/Sticker";
import { Icon } from "@/components/ui/icon";

type Outcome = Schemas["ScanOutcome"];

const SUCCESS: Outcome[] = ["unlocked", "visited", "route_started", "revisited"];
const BROKEN: Outcome[] = ["invalid_tag", "point_unavailable"];

function LockArt() {
  return (
    <svg aria-hidden="true" width="110" height="120" viewBox="0 0 110 120">
      <rect x="25" y="56" width="68" height="54" rx="12" fill="var(--wash)" />
      <path
        d="M34 54 V38 C 34 22, 44 12, 55 12 C 66 12, 76 22, 76 38 V54"
        fill="none"
        stroke="var(--ink)"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <rect x="20" y="51" width="70" height="55" rx="12" fill="none" stroke="var(--ink)" strokeWidth="2.4" />
      <rect x="23" y="48" width="69" height="55" rx="12" fill="none" stroke="var(--pencil)" strokeWidth="1" />
      <circle cx="55" cy="74" r="6" fill="var(--brand)" stroke="var(--ink)" strokeWidth="1.6" />
      <path d="M55 80 V90" stroke="var(--ink)" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

interface ScanOutcomeArtProps {
  outcome: Outcome;
  point: Schemas["PointCard"] | null;
  run: Schemas["RunStateOut"] | null;
}

export function ScanOutcomeArt({ outcome, point, run }: ScanOutcomeArtProps) {
  const { t } = useTranslation();

  if (outcome === "route_completed") {
    return (
      <div className="relative mx-auto mt-2 h-[250px] w-full max-w-[320px]">
        <Polaroid
          src={point?.coverUrl}
          alt={point?.title ?? ""}
          tilt="lg"
          photoHeight={180}
          className="absolute top-2 left-0 w-[210px]"
        />
        <Stamp className="absolute top-6 right-2 size-[88px]">
          {run ? `${run.requiredVisited}/${run.requiredCount}` : t("app.scan.done")}
        </Stamp>
      </div>
    );
  }

  if (outcome === "locked") {
    return (
      <Polaroid
        todo
        tilt="alt"
        photoHeight={200}
        caption={t("app.scan.lockedCaption")}
        className="mx-auto mt-2 w-[270px] [&_figcaption]:text-ink-muted"
      >
        <LockArt />
      </Polaroid>
    );
  }

  if (BROKEN.includes(outcome)) {
    return (
      <div className="relative mx-auto mt-2 h-[270px] w-full max-w-[320px]">
        <Polaroid
          tilt="lg"
          tape
          photoHeight={200}
          className="absolute top-2 left-1/2 w-[230px] -translate-x-1/2 [clip-path:polygon(0_0,100%_0,100%_86%,88%_91%,74%_86%,60%_94%,44%_88%,30%_95%,14%_89%,0_94%)]"
        >
          <span className="text-[96px] leading-none font-semibold text-ink-muted" aria-hidden="true">
            ?
          </span>
        </Polaroid>
        <Sticker className="absolute right-1 bottom-2">{t("app.scan.brokenSticker")}</Sticker>
      </div>
    );
  }

  if (SUCCESS.includes(outcome) && point) {
    return (
      <div className="relative mx-auto mt-2 w-full max-w-[300px]">
        <Polaroid
          src={point.coverUrl}
          alt={point.title}
          tilt="md"
          photoHeight={220}
          caption={point.title.toLowerCase()}
        />
        {outcome === "revisited" ? null : (
          <Burst size={92} className="absolute! -top-4 -right-3">
            <Icon name="check" size={30} strokeWidth={2.6} />
          </Burst>
        )}
      </div>
    );
  }

  return (
    <div className="mx-auto mt-2 grid place-items-center">
      <Burst size={150}>
        <Icon name="route" size={44} strokeWidth={2} />
      </Burst>
    </div>
  );
}
