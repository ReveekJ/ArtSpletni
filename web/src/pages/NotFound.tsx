import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Polaroid } from "@/components/sketch/Polaroid";
import { Sticker, Tape } from "@/components/sketch/Sticker";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";

export default function NotFound() {
  const { t } = useTranslation();
  return (
    <section className="flex flex-1 flex-col gap-[18px]">
      <div aria-hidden="true" className="relative mx-auto mt-5 h-[290px] w-full max-w-[350px]">
        <Polaroid
          tilt="lg"
          tape={false}
          photoHeight={220}
          className="absolute top-2.5 left-1/2 w-[240px] -translate-x-1/2 [clip-path:polygon(0_0,100%_0,100%_78%,88%_84%,74%_78%,60%_88%,44%_80%,30%_90%,14%_82%,0_88%)]"
        >
          <span className="text-[96px] leading-none font-semibold text-ink-muted">?</span>
        </Polaroid>
        <Tape className="top-0! left-[calc(50%-24px)]! rotate-[5deg]" />
        <Sticker className="absolute right-2.5 bottom-0">{t("app.common.notFoundSticker")}</Sticker>
      </div>

      <div className="flex flex-col gap-2.5 text-center">
        <p className="m-0 text-label text-ink-muted">{t("app.common.notFoundCode")}</p>
        <h1 className="m-0 text-h1">{t("app.common.notFoundTitle")}</h1>
        <p className="m-0 text-body text-ink-muted">{t("app.common.notFoundText")}</p>
      </div>

      <div className="mt-auto flex flex-col gap-3.5 pt-4">
        <Button asChild block>
          <Link to="/routes">
            <Icon name="route" />
            {t("app.common.openRoutes")}
          </Link>
        </Button>
        <Button asChild variant="secondary" block>
          <Link to="/">
            <Icon name="home" />
            {t("common.home")}
          </Link>
        </Button>
      </div>
    </section>
  );
}
