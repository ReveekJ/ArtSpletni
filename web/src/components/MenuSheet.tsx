import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Logo } from "@/components/sketch/Logo";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Drawer, DrawerClose, DrawerContent, DrawerTitle } from "@/components/ui/drawer";
import { Icon, type IconName } from "@/components/ui/icon";
import { useCurrentUser, useLogout } from "@/features/auth/api";

interface MenuSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface NavEntry {
  to: string;
  icon: IconName;
  label: string;
}

export function MenuSheet({ open, onOpenChange }: MenuSheetProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useCurrentUser();
  const logout = useLogout();
  const registered = user?.kind === "registered";
  const name = user?.displayName ?? user?.email ?? "";

  const entries: NavEntry[] = [
    { to: "/routes", icon: "route", label: t("app.nav.routes") },
    ...(user ? [{ to: "/me", icon: "user" as const, label: t("app.nav.profile") }] : []),
    { to: "/suggest", icon: "edit", label: t("app.nav.suggest") },
    ...(user?.role === "admin"
      ? [{ to: "/admin", icon: "settings" as const, label: t("app.nav.admin") }]
      : []),
  ];

  const close = () => onOpenChange(false);

  return (
    <Drawer open={open} onOpenChange={onOpenChange} direction="right">
      <DrawerContent className="bg-paper-texture px-5 pt-[18px] pb-6">
        <div className="flex h-full flex-col gap-[18px] overflow-y-auto">
          <header className="flex items-center justify-between">
            <Logo height={30} />
            <DrawerTitle className="sr-only">{t("app.nav.menu")}</DrawerTitle>
            <DrawerClose asChild>
              <Button variant="outline" size="icon" aria-label={t("app.common.close")}>
                <Icon name="x" />
              </Button>
            </DrawerClose>
          </header>

          {registered ? (
            <Card variant="pencil" className="mt-1 flex-row items-center gap-3.5 px-4 py-3.5">
              <span aria-hidden="true" className="sk-avatar size-12 text-xl">
                {name.slice(0, 1).toUpperCase()}
              </span>
              <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="truncate text-[17px] font-semibold">{user?.displayName ?? user?.email}</span>
                {user?.displayName && user.email ? (
                  <span className="truncate text-[14px] text-ink-muted">{user.email}</span>
                ) : null}
              </span>
            </Card>
          ) : (
            <Card variant="pencil" className="mt-1 gap-3 px-4 py-4">
              <p className="m-0 text-body-sm text-ink-muted">{t("app.auth.guestHint")}</p>
              <Button asChild size="sm" className="self-start">
                <Link to="/login" onClick={close}>
                  {t("app.nav.login")}
                </Link>
              </Button>
            </Card>
          )}

          <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
            <legend className="mb-2 p-0 text-label">{t("app.common.language")}</legend>
            <LanguageSwitcher className="grid w-full grid-cols-3" />
          </fieldset>

          <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
            <legend className="mb-2 p-0 text-label">{t("app.theme.title")}</legend>
            <ThemeSwitcher className="grid w-full grid-cols-3" />
          </fieldset>

          <Card asChild className="px-4 py-0.5">
            <nav aria-label={t("app.nav.menu")}>
              {entries.map((entry) => (
                <Link
                  key={entry.to}
                  to={entry.to}
                  onClick={close}
                  className="flex h-[54px] items-center gap-3 border-b border-solid border-rule text-[16px] font-semibold text-ink no-underline last:border-b-0"
                >
                  <Icon name={entry.icon} />
                  <span className="flex-1">{entry.label}</span>
                  <Icon name="chevron-right" size={18} className="text-ink-muted" />
                </Link>
              ))}
            </nav>
          </Card>

          {registered ? (
            <Button
              variant="outline"
              size="sm"
              className="self-start"
              onClick={() =>
                logout.mutate(undefined, {
                  onSuccess: () => {
                    close();
                    navigate("/");
                  },
                })
              }
            >
              <Icon name="logout" size={18} />
              {t("app.nav.logout")}
            </Button>
          ) : null}

          <p className="mt-auto mb-0 text-caption text-ink-muted">{t("app.footer.credits")}</p>
        </div>
      </DrawerContent>
    </Drawer>
  );
}
