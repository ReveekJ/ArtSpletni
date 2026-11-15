import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { DrawnSvg } from "@/components/motion/DrawnSvg";
import { Reveal } from "@/components/motion/Reveal";
import { Polaroid } from "@/components/sketch/Polaroid";
import { ScriptWord, Tape } from "@/components/sketch/Sticker";
import { Sun } from "@/components/sketch/Burst";
import { Button } from "@/components/ui/button";

function SloganWord({ word }: { word: string }) {
  return (
    <ScriptWord className="relative inline-block pr-[.14em] text-[1.3em] [:lang(zh)_&]:pr-0 [:lang(zh)_&]:text-[1em]">
      {word}
      <DrawnSvg
        aria-hidden="true"
        viewBox="0 0 240 20"
        preserveAspectRatio="none"
        pencil={false}
        delay={650}
        className="absolute bottom-[.04em] left-0 h-[.14em] w-full overflow-visible [--draw-duration:.8s] [--ink-lag:0ms]"
      >
        <path
          d="M4 12 C 60 4, 130 16, 232 6"
          fill="none"
          stroke="var(--ink)"
          strokeWidth="2.2"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        <path
          d="M20 17 C 90 11, 160 18, 226 13"
          fill="none"
          stroke="var(--pencil)"
          strokeWidth="1.2"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </DrawnSvg>
    </ScriptWord>
  );
}

export function HeroSection() {
  const { t } = useTranslation();
  return (
    <section
      aria-labelledby="hero-title"
      className="relative px-5 pt-[clamp(56px,7vw,96px)] pb-[260px] min-[721px]:pb-[360px]"
    >
      <Sun
        drawn
        delay={300}
        className="pointer-events-none [--draw-duration:2.2s] [--pencil-duration:1.6s] [--ink-lag:700ms] absolute bottom-[-430px] left-1/2 ml-[-320px] h-[640px] w-[640px] min-[721px]:bottom-[-620px] min-[721px]:ml-[-490px] min-[721px]:h-[980px] min-[721px]:w-[980px] [&_path]:[stroke-width:.32] [&_circle]:[stroke-width:.32]"
      />

      <div className="relative mx-auto flex max-w-[1000px] flex-col items-center gap-[26px] text-center">
        <Reveal asChild>
          <p className="m-0 text-[15px] font-medium text-ink-muted">{t("landing.hero.tagline")}</p>
        </Reveal>
        <Reveal asChild index={1}>
          <h1 id="hero-title" className="m-0 text-display-xl">
            <span className="block">{t("landing.hero.sloganStart")}</span>
            <span className="block">
              <SloganWord word={t("landing.hero.sloganWord")} />
              {t("landing.hero.sloganEnd")}
            </span>
          </h1>
        </Reveal>
        <Reveal asChild index={2}>
          <p className="m-0 max-w-[560px] text-[clamp(18px,1.5vw,21px)] leading-[1.5]">
            {t("landing.hero.lead")}
          </p>
        </Reveal>
        <Reveal index={3} className="mt-1.5 flex flex-wrap items-center justify-center gap-x-[22px] gap-y-4">
          <Button asChild>
            <Link to="/routes">{t("landing.hero.ctaRoute")}</Link>
          </Button>
          <Button asChild variant="secondary">
            <a href="#how">{t("landing.hero.ctaHow")}</a>
          </Button>
        </Reveal>
      </div>

      <Reveal
        variant="drop"
        delay={700}
        className="absolute top-[470px] left-[max(24px,calc(50%-570px))] hidden min-[1100px]:block"
      >
        <Polaroid
          src="/brand/drawing-sevastyanov.png"
          alt={t("landing.hero.polaroidAlt")}
          caption={t("landing.hero.polaroidCaption")}
          tilt="lg"
          photoHeight={168}
          className="w-[220px]"
        />
      </Reveal>
      <Reveal asChild variant="stick" delay={1000}>
        <aside className="sk-note absolute top-[520px] right-[max(24px,calc(50%-560px))] hidden w-[190px] px-[18px] pt-4 pb-[18px] text-[28px] leading-[1.05] min-[1100px]:block">
          <Tape className="!top-[-13px] !right-14 !left-auto !h-6 !w-[70px] ![transform:rotate(-4deg)]" />
          {t("landing.hero.sticker")}
        </aside>
      </Reveal>
    </section>
  );
}
