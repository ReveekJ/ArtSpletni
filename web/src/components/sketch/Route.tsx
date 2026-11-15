import type { CSSProperties, ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type StopState = "done" | "current" | "open" | "locked";

export function ProgressDots({ states, className }: { states: StopState[]; className?: string }) {
  return (
    <span className={cn("sk-dots", className)} aria-hidden="true">
      {states.map((state, index) => (
        <span
          key={index}
          className={cn(
            "sk-dot",
            state === "done" && "sk-dot--done",
            state === "current" && "sk-dot--now",
            state === "locked" && "sk-dot--todo",
          )}
        />
      ))}
    </span>
  );
}

interface MapPinProps {
  state: StopState;
  n?: number | string;
  className?: string;
  style?: CSSProperties;
}

export function MapPin({ state, n, className, style }: MapPinProps) {
  return (
    <span
      className={cn(
        "sk-pin",
        state === "done" && "sk-pin--done",
        state === "current" && "sk-pin--now",
        state === "locked" && "sk-pin--locked",
        className,
      )}
      style={style}
    >
      {state === "locked" ? null : n}
    </span>
  );
}

export interface StopItem {
  key: string;
  n: number;
  name: ReactNode;
  state: StopState;
  href?: string;
  onSelect?: () => void;
}

export function StopList({ stops, className }: { stops: StopItem[]; className?: string }) {
  const { t } = useTranslation();
  return (
    <ul className={cn("sk-stops", className)}>
      {stops.map((stop) => {
        const body = (
          <>
            <span
              className={cn(
                "sk-pin",
                stop.state === "done" && "sk-pin--done",
                stop.state === "current" && "sk-pin--now !size-[26px]",
                stop.state === "locked" && "sk-pin--locked",
              )}
            >
              {stop.n}
            </span>
            <span className="sk-stops__name">{stop.name}</span>
            {stop.state === "current" ? (
              <Badge variant="now">{t("app.stop.current")}</Badge>
            ) : (
              <span className="sk-stops__status">{t(`app.stop.${stop.state}`)}</span>
            )}
          </>
        );
        return (
          <li key={stop.key} data-state={stop.state}>
            {stop.onSelect && stop.state !== "locked" ? (
              <button
                type="button"
                onClick={stop.onSelect}
                className="flex w-full cursor-pointer items-center gap-3 border-0 bg-transparent p-0 text-left font-[inherit] text-[inherit]"
              >
                {body}
              </button>
            ) : stop.href && stop.state !== "locked" ? (
              <Link to={stop.href} className="flex w-full items-center gap-3 text-inherit no-underline">
                {body}
              </Link>
            ) : (
              body
            )}
          </li>
        );
      })}
    </ul>
  );
}
