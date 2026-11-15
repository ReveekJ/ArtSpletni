import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, Outlet, useLocation } from "react-router-dom";

import { MenuSheet } from "@/components/MenuSheet";
import { Logo } from "@/components/sketch/Logo";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";

export function Layout() {
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);
  const { pathname } = useLocation();

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="mx-auto flex w-full max-w-[640px] items-center justify-between gap-3 px-5 pt-[18px] pb-2">
        <Link to="/" aria-label={t("app.nav.home")} className="inline-flex">
          <Logo height={30} />
        </Link>
        <Button
          variant="outline"
          size="icon"
          aria-label={t("app.nav.menu")}
          onClick={() => setMenuOpen(true)}
        >
          <Icon name="menu" />
        </Button>
      </header>
      <main className="mx-auto flex w-full max-w-[640px] flex-1 flex-col px-5 pt-3 pb-8">
        <div key={pathname} className="sk-page flex flex-1 flex-col">
          <Outlet />
        </div>
      </main>
      <MenuSheet open={menuOpen} onOpenChange={setMenuOpen} />
    </div>
  );
}
