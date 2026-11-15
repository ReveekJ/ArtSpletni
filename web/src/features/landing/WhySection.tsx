import { useTranslation } from "react-i18next";

import { Card } from "@/components/ui/card";
import { Icon, type IconName } from "@/components/ui/icon";
import { Section, SectionHeading } from "@/features/landing/Section";
import { useLandingList } from "@/features/landing/useLandingList";
import { cn } from "@/lib/utils";

interface Reason {
  title: string;
  text: string;
}

const MARKS: ReadonlyArray<{ icon: IconName; tone: string }> = [
  { icon: "pin", tone: "bg-wash" },
  { icon: "lock", tone: "bg-note" },
  { icon: "globe", tone: "bg-paper-raised" },
];

export function WhySection() {
  const { t } = useTranslation();
  const reasons = useLandingList<Reason>("landing.why.items");
  return (
    <Section
      id="why"
      band
      labelledBy="why-title"
      innerClassName="grid grid-cols-[repeat(auto-fit,minmax(min(440px,100%),1fr))] items-start gap-x-16 gap-y-12"
    >
      <div className="flex flex-col gap-[18px]">
        <SectionHeading id="why-title" kicker={t("landing.why.kicker")} title={t("landing.why.title")} />
        <p className="m-0 text-body-lg leading-[1.6]">{t("landing.why.text")}</p>
        <blockquote className="sk-note sk-note--left m-0 mt-2.5 max-w-[360px] self-start px-[18px] pt-3.5 pb-4 text-[23px] leading-[1.15] [transform:rotate(-2deg)]">
          {t("landing.why.quote")}
          <cite className="mt-1.5 block font-sans text-[13px] font-medium not-italic text-ink-muted">
            {t("landing.why.quoteSource")}
          </cite>
        </blockquote>
      </div>
      <ul className="m-0 flex list-none flex-col gap-[18px] p-0">
        {reasons.map((reason, index) => {
          const mark = MARKS[index] ?? MARKS[0];
          return (
            <Card asChild key={reason.title} className="flex-row items-start gap-[18px] px-[22px] py-5">
              <li>
                <span
                  aria-hidden="true"
                  className={cn(
                    "grid size-12 shrink-0 place-items-center rounded-wobble border-sketch text-ink",
                    mark?.tone,
                  )}
                >
                  <Icon name={mark?.icon ?? "pin"} size={22} />
                </span>
                <span className="flex flex-col gap-1">
                  <span className="text-h3">{reason.title}</span>
                  <span className="text-body text-ink-muted">{reason.text}</span>
                </span>
              </li>
            </Card>
          );
        })}
      </ul>
    </Section>
  );
}
