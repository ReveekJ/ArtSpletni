import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { DrawnSvg } from "@/components/motion/DrawnSvg";
import { Reveal } from "@/components/motion/Reveal";
import { Logo } from "@/components/sketch/Logo";
import { ThemeToggleButton } from "@/components/ThemeSwitcher";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";

const BURST =
  "M96.2 10.1 L115.1 55.6 L153.6 38.6 L140.5 72.2 L182.6 82.1 L144.3 111.5 L174.4 148.5 L126.8 133.4 L130.8 190.6 L99.8 148.2 L70.0 175.8 L68.4 134.6 L31.3 142.7 L54.6 105.3 L6.2 80.1 L57.7 73.6 L38.1 28.6 L82.5 53.2Z";

function CtaCard() {
  const { t } = useTranslation();
  return (
    <Reveal asChild variant="place">
      <Card
        variant="brand"
        className="flex-row flex-wrap items-center justify-between gap-7 overflow-hidden p-[clamp(32px,5vw,64px)]"
      >
        <DrawnSvg
          aria-hidden="true"
          viewBox="0 0 200 200"
          delay={300}
          className="absolute -top-[70px] -right-[60px] size-[300px] opacity-90 [--draw-duration:1.8s] [--pencil-duration:1.2s] [--pencil-solid:#231d1e80]"
        >
          <path d={BURST} fill="none" stroke="#231d1e" strokeWidth="1.2" strokeLinejoin="round" />
        </DrawnSvg>
        <div className="relative flex max-w-[620px] flex-col gap-2.5">
          <h2 className="m-0 text-[clamp(34px,4vw,54px)] leading-[1.02] font-semibold tracking-[-.035em]">
            {t("landing.cta.title")}
          </h2>
          <p className="m-0 text-body-lg">{t("landing.cta.text")}</p>
        </div>
        <Button
          asChild
          className="relative h-[58px] border-[#231d1e] bg-[#fffcf6] px-7 text-[18px] text-[#231d1e] shadow-[3px_4px_0_#231d1e] hover:shadow-[4px_5px_0_#231d1e]"
        >
          <Link to="/routes">
            <Icon name="route" />
            {t("landing.cta.button")}
          </Link>
        </Button>
      </Card>
    </Reveal>
  );
}

export function CtaFooter() {
  const { t } = useTranslation();
  return (
    <section aria-labelledby="footer-cta" className="pt-[clamp(64px,8vw,112px)] pb-10">
      <h2 id="footer-cta" className="sr-only">
        {t("landing.cta.title")}
      </h2>
      <div className="mx-auto box-border flex max-w-[1184px] flex-col gap-16 px-[clamp(20px,4.5vw,64px)]">
        <CtaCard />
        <footer className="flex flex-col gap-7">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <Logo height={44} />
            <div className="flex flex-wrap items-center gap-3">
              <LanguageSwitcher compact />
              <ThemeToggleButton />
            </div>
          </div>
          <div className="flex flex-wrap justify-between gap-3 border-t border-solid border-rule pt-5 text-[14px] text-ink-muted">
            <span>{t("landing.footer.credits")}</span>
            <span>{t("landing.footer.copyright")}</span>
          </div>
        </footer>
      </div>
    </section>
  );
}
