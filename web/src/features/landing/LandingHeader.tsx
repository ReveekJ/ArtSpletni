import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { MenuSheet } from "@/components/MenuSheet";
import { Logo } from "@/components/sketch/Logo";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { useCurrentUser } from "@/features/auth/api";
import { type Language, LANGUAGES } from "@/i18n";
import { useLanguage } from "@/lib/useLanguage";
import { cn } from "@/lib/utils";

const LANGUAGE_LABELS: Record<Language, string> = { ru: "RU", en: "EN", zh: "中文" };

function LanguageLinks() {
  const { t, i18n } = useTranslation();
  const current = useLanguage();
  return (
    <div role="group" aria-label={t("landing.nav.language")} className="flex gap-1">
      {LANGUAGES.map((lang) => (
        <button
          key={lang}
          type="button"
          lang={lang}
          aria-pressed={lang === current}
          onClick={() => void i18n.changeLanguage(lang)}
          className={cn(
            "cursor-pointer rounded-wobble border-0 bg-transparent px-1.5 py-1 font-sans text-[14px] font-semibold",
            lang === current ? "text-ink" : "text-ink-muted hover:text-ink",
          )}
        >
          {LANGUAGE_LABELS[lang]}
        </button>
      ))}
    </div>
  );
}

export function LandingHeader() {
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);
  const user = useCurrentUser();
  const registered = user?.kind === "registered";
  const links = [
    { href: "#how", label: t("landing.nav.how") },
    { href: "#route", label: t("landing.nav.route") },
    { href: "#why", label: t("landing.nav.why") },
  ];

  return (
    <header className="relative z-10 mx-auto box-border flex max-w-[1312px] items-center justify-between gap-4 px-[clamp(20px,4.5vw,64px)] pt-7">
      <Link to="/" aria-label={t("landing.nav.home")} className="flex">
        <Logo height={38} />
      </Link>
      <nav
        aria-label={t("landing.nav.aria")}
        className="hidden gap-9 text-[15px] font-medium min-[721px]:flex"
      >
        {links.map((link) => (
          <a
            key={link.href}
            href={link.href}
            className="text-ink no-underline hover:underline hover:underline-offset-6"
          >
            {link.label}
          </a>
        ))}
      </nav>
      <div className="flex items-center gap-3.5">
        <div className="hidden min-[721px]:block">
          <LanguageLinks />
        </div>
        <Button asChild variant="outline" size="sm">
          {registered ? (
            <Link to="/me">{t("landing.nav.profile")}</Link>
          ) : (
            <Link to="/login">{t("landing.nav.login")}</Link>
          )}
        </Button>
        <Button
          variant="outline"
          size="icon"
          aria-label={t("landing.nav.menu")}
          className="min-[721px]:hidden"
          onClick={() => setMenuOpen(true)}
        >
          <Icon name="menu" />
        </Button>
      </div>
      <MenuSheet open={menuOpen} onOpenChange={setMenuOpen} />
    </header>
  );
}
