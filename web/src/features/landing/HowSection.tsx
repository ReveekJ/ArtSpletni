import { useTranslation } from "react-i18next";

import { Reveal } from "@/components/motion/Reveal";
import { Card } from "@/components/ui/card";
import { Section, SectionHeading } from "@/features/landing/Section";
import { StepArt, type StepArtKind } from "@/features/landing/StepArt";
import { useLandingList } from "@/features/landing/useLandingList";

interface Step {
  title: string;
  text: string;
}

const ARTS: StepArtKind[] = ["stand", "phone", "listen"];
const TILTS = ["4deg", "-3deg", "5deg"];

export function HowSection() {
  const { t } = useTranslation();
  const steps = useLandingList<Step>("landing.how.steps");
  return (
    <Section id="how" band labelledBy="how-title" innerClassName="flex flex-col gap-12">
      <SectionHeading id="how-title" kicker={t("landing.how.kicker")} title={t("landing.how.title")} />
      <ol className="m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(min(300px,100%),1fr))] gap-7 p-0">
        {steps.map((step, index) => (
          <Reveal asChild key={step.title} variant="place" index={index * 2}>
            <Card asChild variant="pencil" className="gap-3.5 px-[22px] pt-[22px] pb-[26px]">
              <li>
                <Reveal asChild variant="stick" delay={500} index={index * 3}>
                  <span
                    className="sk-note absolute -top-4 right-[18px] z-10 px-3 pt-0.5 pb-1 text-[24px]"
                    style={{ transform: `rotate(${TILTS[index] ?? "3deg"})` }}
                  >
                    {String(index + 1).padStart(2, "0")}
                  </span>
                </Reveal>
                <div
                  aria-hidden="true"
                  className="grid h-[150px] place-items-center rounded-[10px] border border-solid border-ink bg-paper-sunk text-ink"
                >
                  <StepArt kind={ARTS[index] ?? "listen"} delay={250 + index * 260} />
                </div>
                <h3 className="m-0 text-h2">{step.title}</h3>
                <p className="m-0 text-body leading-[1.55] text-ink-muted">{step.text}</p>
              </li>
            </Card>
          </Reveal>
        ))}
      </ol>
    </Section>
  );
}
