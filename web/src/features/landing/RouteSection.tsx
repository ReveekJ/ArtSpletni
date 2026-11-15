import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { MapPin } from "@/components/sketch/Route";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { RouteScheme } from "@/features/landing/RouteScheme";
import { Section, SectionHeading } from "@/features/landing/Section";
import { useLandingList } from "@/features/landing/useLandingList";

interface Stop {
  name: string;
  story: string;
  area: string;
}

export function RouteSection() {
  const { t } = useTranslation();
  const stops = useLandingList<Stop>("landing.route.stops");
  return (
    <Section id="route" labelledBy="route-title" innerClassName="flex flex-col gap-11">
      <div className="flex flex-wrap items-end justify-between gap-5">
        <SectionHeading
          id="route-title"
          kicker={t("landing.route.kicker")}
          title={t("landing.route.title")}
          text={t("landing.route.text")}
        />
        <Button asChild>
          <Link to="/routes">
            <Icon name="map" />
            {t("landing.route.cta")}
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(420px,100%),1fr))] items-start gap-8">
        <RouteScheme label={t("landing.route.mapAria")} />
        <Card asChild className="m-0 list-none px-5 py-1">
          <ol>
            {stops.map((stop, index) => (
              <li
                key={stop.name}
                className="flex items-center gap-4 border-b border-solid border-rule py-3.5 last:border-b-0"
              >
                <MapPin
                  n={index + 1}
                  state={index === 0 ? "current" : "open"}
                  className="size-[34px] shrink-0 text-[14px] shadow-none"
                />
                <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <span className="text-[17px] font-semibold">{stop.name}</span>
                  <span className="text-body-sm text-ink-muted">{stop.story}</span>
                </span>
                <span className="hidden rounded-wobble border-[1.5px] border-solid border-rule px-3 py-1 text-[13px] font-medium min-[721px]:inline-flex">
                  {stop.area}
                </span>
              </li>
            ))}
          </ol>
        </Card>
      </div>
    </Section>
  );
}
